#!/usr/bin/env python3
"""Reconcile Vireo support refund exports and write reviewable CSV summaries.

Uses only Python's standard library. It never reads customer message text into
the AI-ready prompt; all currency calculations remain deterministic locally.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


REASONS = (
    "CANCEL", "DOA-REPL", "DUP-PAYMENT", "GW-OTHER", "LOST-TRANSIT",
    "PRICE-ADJ", "RETURN-QC-OK", "WTY-BUYBACK",
)
EXPECTED_FILES = ("tickets.csv", "agents.csv", "customers.csv", "orders.csv", "products.csv")
MONEY_FIELDS = ("refund_inr", "replacement_cost_inr")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_money(value: str | None) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        return Decimal(value.strip())
    except InvalidOperation:
        return None


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:19], fmt).date()
        except ValueError:
            continue
    return None


def canonical_refund(row: dict[str, str]) -> Decimal | None:
    amount = parse_money(row.get("refund_amount_inr"))
    if amount is not None and row.get("source_system") == "legacy_fd":
        amount /= Decimal(100)
    return amount


def amount_text(value: Decimal | None) -> str:
    return "" if value is None else f"{value.quantize(Decimal('0.01'))}"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt(value: Decimal | int | float) -> str:
    if isinstance(value, Decimal):
        value = value.quantize(Decimal("0.01"))
        return f"₹{value:,.2f}".replace(".00", "")
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def get_agent(roster: dict[str, list[dict[str, str]]], agent_id: str, when: date | None) -> tuple[str, str]:
    assignments = roster.get(agent_id, [])
    if not assignments:
        return "Unknown", "Unknown"
    if when:
        for item in assignments:
            start = parse_date(item.get("from_date"))
            end = parse_date(item.get("to_date"))
            if (start is None or start <= when) and (end is None or when <= end):
                return item.get("name", "Unknown"), item.get("team", "Unknown")
    item = assignments[-1]
    return item.get("name", "Unknown"), item.get("team", "Unknown")


def make_prompt(summary: dict[str, object], monthly: list[dict[str, object]], reason_rows: list[dict[str, object]]) -> str:
    safe_months = "\n".join(
        f"{r['month']}: tickets={r['ticket_count']}; refunds={r['refund_ticket_count']}; "
        f"amount_inr={r['refund_total_inr']}"
        for r in monthly
    )
    safe_reasons = "\n".join(
        f"{r['reason_code']}: count={r['refund_ticket_count']}; amount_inr={r['refund_total_inr']}"
        for r in reason_rows
    )
    return f"""You are reviewing a finance support report. Use only the aggregate facts below.
Do not infer individual agent misconduct or claim causation. Separate observed facts,
hypotheses, and recommended checks. The email says GW-OTHER is first in the dropdown;
the policy says Returns Desk handles most refunds, but agent_id identifies the resolver.
Mention both as interpretation limits, along with the system migration on 14 Sep 2025,
the paise-to-rupee correction for legacy_fd rows, and the deduplication rule.
Do not invent facts. Keep the response to five short bullets and identify any
question that requires source-system verification. No customer message text or names
are included in this prompt.

Reconciled report:
- Unique tickets: {summary['unique_ticket_count']}
- Refund tickets: {summary['refund_ticket_count']}
- Refund value INR: {summary['refund_total_inr']}
- Paired ticket IDs removed as migration duplicates: {summary['duplicate_id_count']}
- Paired IDs with a currency-normalized amount mismatch: {summary['duplicate_conflict_count']}

Monthly totals:
{safe_months}

Refund reasons (all months):
{safe_reasons}
"""


def run(data_dir: Path, out_dir: Path) -> dict[str, object]:
    missing = [name for name in EXPECTED_FILES if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required data files in {data_dir}: {', '.join(missing)}")

    raw = read_csv(data_dir / "tickets.csv")
    roster_rows = read_csv(data_dir / "agents.csv")
    orders = read_csv(data_dir / "orders.csv")
    products = read_csv(data_dir / "products.csv")
    roster: dict[str, list[dict[str, str]]] = defaultdict(list)
    for person in roster_rows:
        roster[person.get("agent_id", "")].append(person)

    order_by_id = {o.get("order_id", ""): o for o in orders if o.get("order_id")}
    order_by_customer_sku: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for order in orders:
        order_by_customer_sku[(order.get("customer_id", ""), order.get("sku", ""))].append(order)
    product_cost = {p.get("sku", ""): parse_money(p.get("unit_cost_inr")) for p in products}

    by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in raw:
        by_id[row.get("ticket_id", "")].append(row)

    duplicate_conflicts: list[str] = []
    normalized_raw_refund_rows = 0
    raw_refund_sum = Decimal(0)
    for row in raw:
        original = parse_money(row.get("refund_amount_inr"))
        if original is not None:
            normalized_raw_refund_rows += 1
            raw_refund_sum += original
    canonical: list[dict[str, object]] = []
    for ticket_id, group in by_id.items():
        chosen = next((r for r in group if r.get("source_system") == "helpdesk"), group[0])
        # Compare paired rows on all shared business fields after unit normalization.
        if len(group) > 1:
            signatures = set()
            for item in group:
                values: list[str] = []
                for key, value in item.items():
                    if key == "source_system":
                        continue
                    if key == "refund_amount_inr":
                        money = canonical_refund(item)
                        values.append("" if money is None else amount_text(money))
                    else:
                        values.append(value or "")
                signatures.add(tuple(values))
            if len(signatures) > 1:
                duplicate_conflicts.append(ticket_id)
        row = dict(chosen)
        row["_refund"] = canonical_refund(chosen)
        row["_date"] = parse_date(chosen.get("created_at"))
        row["_resolved_date"] = parse_date(chosen.get("resolved_at"))
        row["_month"] = (chosen.get("created_at", "")[:7])
        canonical.append(row)

    canonical.sort(key=lambda r: (str(r["_month"]), str(r.get("ticket_id", ""))))
    monthly_total: dict[str, dict[str, object]] = {}
    reason_agg: dict[tuple[str, str], dict[str, object]] = {}
    agent_agg: dict[tuple[str, str, str, str], dict[str, object]] = {}
    agent_reason_agg: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    team_agg: dict[tuple[str, str, str], dict[str, object]] = {}
    all_reason: dict[str, dict[str, object]] = {}
    unknown_reason: Counter[str] = Counter()
    missing_agents: Counter[str] = Counter()
    detail_rows: list[dict[str, object]] = []

    for row in canonical:
        month = str(row["_month"])
        overall = monthly_total.setdefault(month, {
            "month": month, "ticket_count": 0, "refund_ticket_count": 0, "refund_total": Decimal(0),
            "csat_total": Decimal(0), "csat_count": 0,
        })
        overall["ticket_count"] += 1
        score = parse_money(str(row.get("csat_score", "")))
        if score is not None:
            overall["csat_total"] += score
            overall["csat_count"] += 1
        amount = row["_refund"]
        if amount is None:
            continue
        reason = str(row.get("refund_reason_code") or "MISSING")
        agent_id = str(row.get("agent_id") or "Unknown")
        agent_name, team = get_agent(roster, agent_id, row["_resolved_date"] or row["_date"])
        first_team = str(row.get("assigned_team") or "Unknown")
        if agent_name == "Unknown":
            missing_agents[agent_id] += 1
        if reason not in REASONS:
            unknown_reason[reason] += 1
        detail_rows.append({
            "ticket_id": row.get("ticket_id", ""), "month": month, "source_system": row.get("source_system", ""),
            "agent_id": agent_id, "agent_name": agent_name, "resolver_team": team, "reason_code": reason,
            "refund_total_inr": amount_text(amount), "replacement_issued": row.get("replacement_issued", ""),
        })
        overall["refund_ticket_count"] += 1
        overall["refund_total"] += amount
        rk = (month, reason)
        ra = reason_agg.setdefault(rk, {"month": month, "reason_code": reason, "refund_ticket_count": 0, "refund_total": Decimal(0)})
        ra["refund_ticket_count"] += 1
        ra["refund_total"] += amount
        total_reason = all_reason.setdefault(reason, {"reason_code": reason, "refund_ticket_count": 0, "refund_total": Decimal(0)})
        total_reason["refund_ticket_count"] += 1
        total_reason["refund_total"] += amount
        ak = (month, agent_id, agent_name, team)
        aa = agent_agg.setdefault(ak, {"month": month, "agent_id": agent_id, "agent_name": agent_name, "team": team, "refund_ticket_count": 0, "refund_total": Decimal(0)})
        aa["refund_ticket_count"] += 1
        aa["refund_total"] += amount
        ark = (month, agent_id, agent_name, team, reason)
        ara = agent_reason_agg.setdefault(ark, {"month": month, "agent_id": agent_id, "agent_name": agent_name, "team": team, "reason_code": reason, "refund_ticket_count": 0, "refund_total": Decimal(0)})
        ara["refund_ticket_count"] += 1
        ara["refund_total"] += amount
        for basis, basis_team in (("resolver_roster", team), ("first_assigned_team", first_team)):
            tk = (month, basis, basis_team)
            ta = team_agg.setdefault(tk, {"month": month, "team_basis": basis, "team": basis_team, "refund_ticket_count": 0, "refund_total": Decimal(0)})
            ta["refund_ticket_count"] += 1
            ta["refund_total"] += amount

    def money_rows(items: list[dict[str, object]]) -> list[dict[str, object]]:
        for item in items:
            for key in list(item):
                if key == "refund_total":
                    item["refund_total_inr"] = amount_text(item.pop(key))
        return items

    totals = money_rows(sorted(monthly_total.values(), key=lambda r: str(r["month"])))
    for row in totals:
        count = int(row["csat_count"])
        row["csat_mean"] = f"{(row['csat_total'] / count):.3f}" if count else ""
        row["csat_response_rate"] = f"{100 * count / int(row['ticket_count']):.1f}" if row["ticket_count"] else ""
        row.pop("csat_total", None)
        row.pop("csat_count", None)
    by_reason = money_rows(sorted(reason_agg.values(), key=lambda r: (str(r["month"]), str(r["reason_code"]))))
    by_agent = money_rows(sorted(agent_agg.values(), key=lambda r: (str(r["month"]), str(r["agent_id"]))))
    by_agent_reason = money_rows(sorted(agent_reason_agg.values(), key=lambda r: (str(r["month"]), str(r["agent_id"]), str(r["reason_code"]))))
    by_team = money_rows(sorted(team_agg.values(), key=lambda r: (str(r["month"]), str(r["team_basis"]), str(r["team"]))))
    reason_totals = money_rows(sorted(all_reason.values(), key=lambda r: str(r["reason_code"])))

    # Flag co-occurring refund + replacement fields, then match the purchase.
    # A blank order_id may use the README's customer_id + product_sku fallback.
    flags: list[dict[str, object]] = []
    for row in canonical:
        refund = row["_refund"]
        if refund is None or str(row.get("replacement_issued", "")).upper() != "Y":
            continue
        oid = str(row.get("order_id") or "")
        customer = str(row.get("customer_id") or "")
        sku = str(row.get("product_sku") or "")
        match = None
        confidence = "unmatched"
        if oid:
            candidate = order_by_id.get(oid)
            if candidate and candidate.get("customer_id") == customer and candidate.get("sku") == sku:
                match, confidence = candidate, "order_id_customer_sku_match"
            else:
                confidence = "order_id_did_not_match_reference"
        else:
            candidates = order_by_customer_sku.get((customer, sku), [])
            if len(candidates) == 1:
                match, confidence = candidates[0], "unique_customer_sku_fallback"
            elif len(candidates) > 1:
                confidence = "ambiguous_customer_sku_fallback"
        cost = product_cost.get(sku)
        replacement_cost = (cost + Decimal(340)) if cost is not None else None
        flags.append({
            "ticket_id": row.get("ticket_id", ""), "month": row["_month"], "agent_id": row.get("agent_id", ""),
            "refund_reason_code": row.get("refund_reason_code", ""), "refund_inr": amount_text(refund),
            "replacement_issued": "Y", "order_match": confidence,
            "matched_order_id": (match or {}).get("order_id", ""), "product_sku": sku,
            "planning_replacement_cost_inr": amount_text(replacement_cost),
            "combined_planning_exposure_inr": amount_text(refund + replacement_cost) if replacement_cost is not None else "",
        })

    fields = ["month", "ticket_count", "refund_ticket_count", "refund_total_inr", "csat_mean", "csat_response_rate"]
    write_csv(out_dir / "monthly_totals.csv", fields, totals)
    write_csv(out_dir / "monthly_by_reason.csv", ["month", "reason_code", "refund_ticket_count", "refund_total_inr"], by_reason)
    write_csv(out_dir / "monthly_by_agent.csv", ["month", "agent_id", "agent_name", "resolver_team", "refund_ticket_count", "refund_total_inr"], [{**r, "resolver_team": r.pop("team")} for r in by_agent])
    write_csv(out_dir / "monthly_by_agent_reason.csv", ["month", "agent_id", "agent_name", "resolver_team", "reason_code", "refund_ticket_count", "refund_total_inr"], [{**r, "resolver_team": r.pop("team")} for r in by_agent_reason])
    write_csv(out_dir / "monthly_by_team.csv", ["month", "team_basis", "team", "refund_ticket_count", "refund_total_inr"], by_team)
    write_csv(out_dir / "all_period_by_reason.csv", ["reason_code", "refund_ticket_count", "refund_total_inr"], reason_totals)
    write_csv(out_dir / "canonical_refund_detail.csv", ["ticket_id", "month", "source_system", "agent_id", "agent_name", "resolver_team", "reason_code", "refund_total_inr", "replacement_issued"], detail_rows)
    write_csv(out_dir / "refund_replacement_review.csv", ["ticket_id", "month", "agent_id", "refund_reason_code", "refund_inr", "replacement_issued", "order_match", "matched_order_id", "product_sku", "planning_replacement_cost_inr", "combined_planning_exposure_inr"], flags)

    refund_total = sum((r["_refund"] for r in canonical if r["_refund"] is not None), Decimal(0))
    refund_count = sum(1 for r in canonical if r["_refund"] is not None)
    duplicate_count = len(raw) - len(canonical)
    conflict_count = len(duplicate_conflicts)
    q2_rows = [r for r in canonical if r["_month"] in ("2026-04", "2026-05", "2026-06")]
    q2_gw = [r for r in q2_rows if r["_refund"] is not None and r.get("refund_reason_code") == "GW-OTHER"]
    q2_gw_total = sum((r["_refund"] for r in q2_gw), Decimal(0))
    goal_delta = q2_gw_total * Decimal("0.15")
    goal_cap = q2_gw_total - goal_delta
    q2_csat = [parse_money(str(r.get("csat_score", ""))) for r in q2_rows]
    q2_csat = [v for v in q2_csat if v is not None]
    matched_flags = [r for r in flags if r["order_match"] in ("order_id_customer_sku_match", "unique_customer_sku_fallback")]
    matched_replacement_cost = sum((parse_money(str(r["planning_replacement_cost_inr"])) or Decimal(0) for r in matched_flags), Decimal(0))
    matched_refunds = sum((parse_money(str(r["refund_inr"])) or Decimal(0) for r in matched_flags), Decimal(0))
    returns_team = sum((v["refund_ticket_count"] for k, v in team_agg.items() if k[1] == "resolver_roster" and k[2] == "Returns Desk"), 0)
    returns_amount = sum((parse_money(str(v.get("refund_total_inr", "0"))) or Decimal(0) for k, v in team_agg.items() if k[1] == "resolver_roster" and k[2] == "Returns Desk"), Decimal(0))

    summary: dict[str, object] = {
        "raw_ticket_rows": len(raw), "unique_ticket_count": len(canonical), "duplicate_id_count": duplicate_count,
        "duplicate_conflict_count": conflict_count, "raw_refund_rows": normalized_raw_refund_rows,
        "raw_unadjusted_refund_sum": amount_text(raw_refund_sum), "refund_ticket_count": refund_count,
        "refund_total_inr": amount_text(refund_total), "refund_replacement_flag_count": len(flags),
        "refund_replacement_matched_count": len(matched_flags), "replacement_planning_cost_inr": amount_text(matched_replacement_cost),
        "matched_refund_amount_inr": amount_text(matched_refunds), "unknown_reason_count": sum(unknown_reason.values()),
        "unknown_agent_refund_ticket_count": sum(missing_agents.values()),
        "returns_desk_resolver_refund_count": returns_team, "returns_desk_resolver_refund_amount_inr": amount_text(returns_amount),
    }

    qtr: dict[str, dict[str, object]] = {}
    for row in canonical:
        d = row["_date"]
        if not d:
            continue
        q = f"{d.year}Q{(d.month - 1) // 3 + 1}"
        agg = qtr.setdefault(q, {"tickets": 0, "refunds": 0, "amount": Decimal(0), "csat_total": Decimal(0), "csat_n": 0})
        agg["tickets"] += 1
        if row["_refund"] is not None:
            agg["refunds"] += 1
            agg["amount"] += row["_refund"]
        score = parse_money(str(row.get("csat_score", "")))
        if score is not None:
            agg["csat_total"] += score
            agg["csat_n"] += 1

    summary_lines = [
        "# Vireo Audio refund audit",
        "",
        "## Reconciled result",
        "",
        f"- {len(raw):,} export rows collapse to {len(canonical):,} unique ticket IDs; {duplicate_count:,} IDs appeared in both systems.",
        f"- {normalized_raw_refund_rows:,} raw refund rows become {refund_count:,} unique refund tickets after deduplication.",
        f"- Reconciled refund value: **{fmt(refund_total)}** across the Jan 2025-Jun 2026 pack.",
        f"- The unreconciled raw sum is {fmt(raw_refund_sum)}; it overstates the reconciled result because legacy amounts are in hundredths of a rupee and repeated IDs are present.",
        f"- {conflict_count} duplicate ID groups differ after currency normalization; zero means paired copies agreed on business fields in this pack.",
        f"- The policy says Returns Desk processes the large majority of refunds. The resolver roster attributes {returns_team:,} of {refund_count:,} refund tickets ({(100 * returns_team / refund_count):.1f}%) and {fmt(returns_amount)} ({(100 * returns_amount / refund_total):.1f}%) to Returns Desk. `agent_id` is the resolving agent, not a refund-approval or payment-settlement field; verify the ownership mismatch before interpreting names.",
        "",
        "## Quarterly trend",
        "",
        "| Quarter | Tickets | Refund tickets | Refund rate | Refund amount | Mean refund | CSAT mean (responses only) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for q, a in sorted(qtr.items()):
        mean = a["amount"] / a["refunds"] if a["refunds"] else Decimal(0)
        csat = a["csat_total"] / a["csat_n"] if a["csat_n"] else Decimal(0)
        rate = Decimal(100) * a["refunds"] / a["tickets"] if a["tickets"] else Decimal(0)
        summary_lines.append(f"| {q} | {a['tickets']:,} | {a['refunds']:,} | {rate:.2f}% | {fmt(a['amount'])} | {fmt(mean)} | {csat:.2f} (n={a['csat_n']:,}) |")

    summary_lines += [
        "",
        "## Suggested measurable goal",
        "",
        f"The email says `GW-OTHER` is first in the reason dropdown, so validate its coding before using it as a savings target. Q2 2026 is a provisional baseline: {len(q2_gw):,} refunds totaling {fmt(q2_gw_total)}. A 15% reduction would mean no more than {fmt(goal_cap)} in a comparable quarter, a potential {fmt(goal_delta)} quarterly reduction ({fmt(goal_delta * 4)} annualized), provided the change does not reduce customer outcomes. Keep responding-customer CSAT at or above 3.4/5; Q2 2026 observed {sum(q2_csat)} points across {len(q2_csat):,} responses ({(sum(q2_csat) / len(q2_csat)):.2f}/5). This is a target scenario, not proven savings or a causal forecast.",
        "",
        "## Policy review queue",
        "",
        f"{len(flags)} unique tickets have both a refund and `replacement_issued=Y`. Reference joins identify {len(matched_flags)} with an order ID plus customer/SKU match, or a unique customer+SKU fallback where the ticket order ID is blank. Their policy planning replacement cost is {fmt(matched_replacement_cost)}; this is a review estimate, not confirmed avoidable spend. The remaining {len(flags)-len(matched_flags)} are unresolved (for example, ambiguous or missing reference matches). See `refund_replacement_review.csv`; escalate confirmed same-order cases per policy before treating them as errors.",
        "",
        "## Agent report interpretation",
        "",
        "`monthly_by_agent.csv` and `monthly_by_agent_reason.csv` attribute refunds to the ticket resolver, not necessarily the person who approved, issued, or settled the refund. This resolver view differs from the policy expectation that Returns Desk processes most refunds. `monthly_by_team.csv` shows both resolver-roster team and first-routed team; reconcile ownership before using agent totals as a behavior measure. These are descriptive totals, not a misconduct ranking. Tier 2 cases are not comparable to Tier 1 volume metrics.",
        "",
        "## Definitions and limits",
        "",
        "- Month is ticket creation month in the ticket export's displayed IST timestamp.",
        "- Refund blank means no recorded refund; CSAT blanks are excluded from the mean.",
        "- Each `ticket_id` is counted once. If a paired ID exists in both sources, the `helpdesk` row is retained; legacy-only amounts are divided by 100 based on the email and policy notes about legacy-native units.",
        "- Amounts are refunds raised on tickets, not independently reconciled cash settlements or net revenue impact.",
        "- Refund-rate changes and CSAT are observational. Do not infer the effect of the Q4 service instruction from this dataset alone.",
        "- The migration date (14 Sep 2025) and growing ticket volume complicate before/after comparisons.",
        "",
        "## Validation",
        "",
        f"Rows are checked in `validation.md`. Aggregate cross-checks: monthly refund totals sum to {fmt(refund_total)}; reason totals sum to the same; agent totals sum to the same; unique refund-ticket count is {refund_count:,}.",
    ]
    (out_dir / "audit_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    (out_dir / "ai_review_prompt.txt").write_text(make_prompt(summary, totals, reason_totals), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile Vireo support refund records and write CSV summaries.")
    parser.add_argument("--data", type=Path, default=Path("data"), help="Folder containing the five CSV inputs (default: ./data)")
    parser.add_argument("--out", type=Path, default=Path("reports"), help="Output folder (default: ./reports)")
    args = parser.parse_args()
    result = run(args.data, args.out)
    print(f"Wrote reconciled reports to {args.out.resolve()}")
    print(f"Unique tickets: {result['unique_ticket_count']:,}; refund tickets: {result['refund_ticket_count']:,}; total: ₹{Decimal(str(result['refund_total_inr'])):,.2f}")


if __name__ == "__main__":
    main()
