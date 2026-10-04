# Vireo Audio support refund audit

A small, local report generator for the Vireo Audio support-ticket take-home. It reconciles duplicated ticket IDs and legacy refund units, then writes monthly refund summaries by reason code and resolving agent, plus an order-linked refund/replacement review queue.

## Run it

Requirements: Python 3.10 or later. The tool uses only the Python standard library; no package install, API key, internet connection, or paid call is needed.

From this folder:

```text
python refund_audit.py
```

To choose other folders:

```text
python refund_audit.py --data data --out reports
```

On Windows, use `py refund_audit.py` if `python` is not on PATH. The included `data/` folder contains the five CSV inputs and Vireo's support policy. The tool writes these files under `reports/`:

- `audit_summary.md` - reconciled total, quarterly trend, business target, and cautions
- `monthly_totals.csv` - ticket volume, refund count, refund value, and response-only CSAT by month
- `monthly_by_reason.csv` - monthly refund count and amount by dropdown reason code
- `monthly_by_agent.csv` - monthly refund count and amount attributed to the resolving agent
- `monthly_by_agent_reason.csv` - the combined monthly, agent, and reason view
- `monthly_by_team.csv` - monthly totals by resolver roster team and first assigned team
- `all_period_by_reason.csv` - full-period reason totals
- `canonical_refund_detail.csv` - one row per reconciled refund ticket, without customer message text
- `refund_replacement_review.csv` - refund-plus-replacement flags with order-match confidence and planning cost
- `ai_review_prompt.txt` - a privacy-minimized prompt built from aggregates only; optionally paste it into an AI assistant to draft a second-reader summary

## Reconciliation choices

- Count each `ticket_id` once. If both `helpdesk` and `legacy_fd` copies exist, retain the helpdesk copy.
- Divide `legacy_fd` refund amounts by 100. The email thread says Freshdesk stored money in its native unit; the paired rows confirm that the legacy value is 100 times the helpdesk value after normalization.
- Attribute the refund to `agent_id`, the resolver, and use the roster row in effect on the resolution date where available. This does not identify who approved, issued, or settled the refund.
- Treat a blank refund amount as no recorded refund. Exclude blank CSAT values from averages.
- Use ticket creation month as the reporting month. The timestamps are the helpdesk's displayed IST values.
- For refund-plus-replacement flags, match a supplied order ID only when customer and product also agree. Use customer plus product as the fallback only when order ID is blank and the match is unique.

These are reporting rules, not proof that a refund settled or a replacement was delivered. The flags are a review queue, not confirmed policy violations.

## AI and cost

The calculations are deterministic and run locally. The tool does not make model or API calls. It creates an aggregate-only prompt for an optional human-led AI review; it excludes customer messages, names, and order-level rows. Cost for a local run is ₹0. AI-assisted development and review are disclosed in `submission-form-answers.md`.

## Read before interpreting agent totals

The policy says Returns Desk handles the large majority of refunds, but the resolver roster attributes only about a quarter of refund tickets to that team in this export. Reconcile the ownership mismatch before interpreting agent totals. The email also says `GW-OTHER` is first in the reason dropdown, so validate its coding before treating the value as goodwill spend. Tier 2 cases are multi-touch and should not be compared with Tier 1 on volume. Use agent files for traceability and same-role review, not as an unadjusted misconduct ranking.
