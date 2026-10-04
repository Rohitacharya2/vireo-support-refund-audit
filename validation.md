# Validation and known limits

## Reconciliation checks

- Source file: `data/tickets.csv`, 12,238 rows and 11,600 unique `ticket_id` values.
- 638 IDs are present in both `helpdesk` and `legacy_fd`. The tool retains the helpdesk copy. After converting legacy currency, all 638 paired ticket groups agree on the business fields in this pack; there are no normalized duplicate conflicts.
- There are 2,465 refund-bearing export rows. The canonical set has 2,340 refund tickets because 125 duplicated IDs carried a refund on both copies.
- Summing raw refund fields without cleaning gives ₹23,01,24,081. The canonical, currency-normalized sum is ₹67,09,932. Of that, helpdesk rows contribute ₹48,17,881 and legacy-only tickets contribute ₹18,92,051 after dividing their exported amounts by 100.
- Independent totals from `monthly_totals.csv`, `monthly_by_reason.csv`, `monthly_by_agent.csv`, and `all_period_by_reason.csv` agree: ₹67,09,932 and 2,340 refund tickets.
- `monthly_by_team.csv` also ties to the same ₹67,09,932 and 2,340 refund tickets separately for both resolver-roster team and first-assigned team; no refund ticket is missing a roster match.
- Refund totals are raised-on-ticket values, not a payment settlement ledger.

## Spot checks

I checked a 25-ticket stratified sample against source rows and `canonical_refund_detail.csv`: five paired IDs, five legacy-only refunds, five helpdesk-only refunds, five blank refunds, and five refund-plus-replacement cases. The deterministic selection used Python's `random.Random(13)`; all 25 matched the normalization and inclusion rules (0 sample mismatches). Sample IDs are listed in the table; representative checks:

| Ticket | Source values | Expected treatment | Tool result |
|---|---|---|---|
| `TK-243834` | Helpdesk ₹1,299; legacy 129,900 | Keep one ticket; convert legacy to ₹1,299 | One ₹1,299 refund ticket |
| `TK-240759` | Legacy-only 110,400 | Divide by 100 | ₹1,104 refund |
| `TK-253136` | Helpdesk-only ₹2,974 | Keep rupee value | ₹2,974 refund |
| `TK-244027` | Blank refund on both copies | Exclude from refund totals | No refund counted |
| `TK-248252` | Helpdesk ₹2,499; replacement flag Y; order, customer and SKU match | Keep rupee amount and add to review queue | ₹2,499; exact reference match |

Other sampled IDs: paired `TK-243594`, `TK-242180`, `TK-244528`, `TK-240751`; legacy-only `TK-244000`, `TK-242639`, `TK-243913`, `TK-241934`; helpdesk-only `TK-250860`, `TK-247935`, `TK-251598`, `TK-245197`; blank `TK-247947`, `TK-241423`, `TK-252564`, `TK-253205`; dual-flag `TK-251537`, `TK-244392`, `TK-254172`, `TK-251319`.

The 25-row spot check supplements whole-file reconciliation; it is not an independent audit of settlement records.

## Policy review queue

There are 166 unique tickets with both a nonblank refund and `replacement_issued=Y`. The order join yields 100 matches on the supplied order ID, customer, and product; 58 more have a unique customer+product match when the ticket order ID is blank. Eight are ambiguous and left unresolved. For the 158 matched candidates, the replacement cost proxy is **₹2,84,170** (unit cost plus ₹340 logistics, per policy). Treat these as review candidates. A ticket flag does not prove cash settlement, delivery, or that both benefits applied to the same order in practice.

## Business interpretation

- Refund value rose from ₹6.10 lakh in Q1 2025 to ₹16.28 lakh in Q4 2025; refund rate moved only from 20.13% to 20.24%, while ticket volume rose 2.54 times.
- Q2 2026 refunds total ₹12.80 lakh; 209 `GW-OTHER` refunds total ₹5,84,774 (45.7% of the quarter's refund value).
- The email says `GW-OTHER` is first in the dropdown. Its 43.3% full-period share may reflect coding habits as well as true goodwill; validate the code before treating reductions as savings.
- Policy says Returns Desk handles the large majority, but the resolver roster attributes 612 of 2,340 refund tickets (26.2%) and ₹16,92,666 (25.2%) to that team. The first-routed-team view is similar. `agent_id` means the ticket resolver, not necessarily the person who raised or approved the refund. Reconcile the ownership mismatch before interpreting agent totals.
- The 15% goal scenario is ₹87,716 less per quarter, or ₹3,50,864 annualized. It assumes the lower amount is achieved without shifting cost to another refund code or lowering CSAT; the data does not establish a causal intervention.
- CSAT means use responded surveys only. Response rates are about 43-46% each quarter, so the averages may not represent all customers.
- The task email says the Q4 customer-experience instruction was accompanied by a 0.4-point CSAT lift. These data show a 0.03-point change in responding-customer mean from Q3 2025 (3.48) to Q4 (3.51), so the stated lift is not reproduced for those quarters.

## Deliberate limits

- Agent totals are descriptive. Policy expects Returns Desk to handle most refunds, but the export attributes only about one quarter to that resolver team; reconcile that mismatch and the meaning of the resolver field before comparing agents by role, shift, assignment period, volume, and case mix. Tier 2 is not comparable with Tier 1 on raw closures.
- No allegation of improper “giveaway” or agent intent is made from a selected dropdown code.
- No causal claim is made from quarter-on-quarter amounts or CSAT.
- No customer message text is used by the report generator or included in the AI-ready prompt.
- Validation does not reconcile refunds to bank, payment-gateway, or general-ledger settlement data because none was supplied.
