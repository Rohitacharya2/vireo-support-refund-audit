# Vireo Audio refund audit

## Reconciled result

- 12,238 export rows collapse to 11,600 unique ticket IDs; 638 IDs appeared in both systems.
- 2,465 raw refund rows become 2,340 unique refund tickets after deduplication.
- Reconciled refund value: **₹6,709,932** across the Jan 2025-Jun 2026 pack.
- The unreconciled raw sum is ₹230,124,081; it overstates the reconciled result because legacy amounts are in hundredths of a rupee and repeated IDs are present.
- 0 duplicate ID groups differ after currency normalization; zero means paired copies agreed on business fields in this pack.
- The policy says Returns Desk processes the large majority of refunds. The resolver roster attributes 612 of 2,340 refund tickets (26.2%) and ₹1,692,666 (25.2%) to Returns Desk. `agent_id` is the resolving agent, not a refund-approval or payment-settlement field; verify the ownership mismatch before interpreting names.

## Quarterly trend

| Quarter | Tickets | Refund tickets | Refund rate | Refund amount | Mean refund | CSAT mean (responses only) |
|---|---:|---:|---:|---:|---:|---:|
| 2025Q1 | 1,053 | 212 | 20.13% | ₹609,583 | ₹2,875.39 | 3.54 (n=476) |
| 2025Q2 | 1,388 | 253 | 18.23% | ₹727,422 | ₹2,875.19 | 3.52 (n=603) |
| 2025Q3 | 1,843 | 405 | 21.98% | ₹1,207,091 | ₹2,980.47 | 3.48 (n=826) |
| 2025Q4 | 2,678 | 542 | 20.24% | ₹1,627,575 | ₹3,002.91 | 3.51 (n=1,242) |
| 2026Q1 | 2,361 | 455 | 19.27% | ₹1,258,438 | ₹2,765.80 | 3.49 (n=1,051) |
| 2026Q2 | 2,277 | 473 | 20.77% | ₹1,279,823 | ₹2,705.76 | 3.46 (n=1,039) |

## Suggested measurable goal

The email says `GW-OTHER` is first in the reason dropdown, so validate its coding before using it as a savings target. Q2 2026 is a provisional baseline: 209 refunds totaling ₹584,774. A 15% reduction would mean no more than ₹497,057.90 in a comparable quarter, a potential ₹87,716.10 quarterly reduction (₹350,864.40 annualized), provided the change does not reduce customer outcomes. Keep responding-customer CSAT at or above 3.4/5; Q2 2026 observed 3596 points across 1,039 responses (3.46/5). This is a target scenario, not proven savings or a causal forecast.

## Policy review queue

166 unique tickets have both a refund and `replacement_issued=Y`. Reference joins identify 158 with an order ID plus customer/SKU match, or a unique customer+SKU fallback where the ticket order ID is blank. Their policy planning replacement cost is ₹284,170; this is a review estimate, not confirmed avoidable spend. The remaining 8 are unresolved (for example, ambiguous or missing reference matches). See `refund_replacement_review.csv`; escalate confirmed same-order cases per policy before treating them as errors.

## Agent report interpretation

`monthly_by_agent.csv` and `monthly_by_agent_reason.csv` attribute refunds to the ticket resolver, not necessarily the person who approved, issued, or settled the refund. This resolver view differs from the policy expectation that Returns Desk processes most refunds. `monthly_by_team.csv` shows both resolver-roster team and first-routed team; reconcile ownership before using agent totals as a behavior measure. These are descriptive totals, not a misconduct ranking. Tier 2 cases are not comparable to Tier 1 volume metrics.

## Definitions and limits

- Month is ticket creation month in the ticket export's displayed IST timestamp.
- Refund blank means no recorded refund; CSAT blanks are excluded from the mean.
- Each `ticket_id` is counted once. If a paired ID exists in both sources, the `helpdesk` row is retained; legacy-only amounts are divided by 100 based on the email and policy notes about legacy-native units.
- Amounts are refunds raised on tickets, not independently reconciled cash settlements or net revenue impact.
- Refund-rate changes and CSAT are observational. Do not infer the effect of the Q4 service instruction from this dataset alone.
- The migration date (14 Sep 2025) and growing ticket volume complicate before/after comparisons.

## Validation

Rows are checked in `validation.md`. Aggregate cross-checks: monthly refund totals sum to ₹6,709,932; reason totals sum to the same; agent totals sum to the same; unique refund-ticket count is 2,340.
