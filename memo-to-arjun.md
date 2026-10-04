# Monthly refund reconciliation

**To:** Arjun Mehta, Finance Controller  
**From:** Candidate  
**Date:** 4 October 2026  
**Subject:** Refund totals by reason and resolving agent

I rebuilt the refund summary from the 18-month support export. The raw total is not comparable to rupees as exported: 3,874 legacy rows use Freshdesk's native money unit, and 638 ticket IDs appear in both source systems. After converting legacy amounts to rupees and counting each ticket ID once, the pack contains **₹67.10 lakh across six quarters**, or **₹11.18 lakh per quarter on average**. That is close to the helpdesk administrator's rough estimate of ₹11 lakh per quarter, rather than more than ₹1 crore per quarter.

The corrected quarterly total rose from **₹6.10 lakh in Q1 2025 to ₹16.28 lakh in Q4 2025**. Refunds per ticket were nearly flat over those endpoints: **20.13% and 20.24%**. Ticket volume rose from 1,053 to 2,678 over the same comparison, so the higher refund total is consistent with handling many more tickets; this is an observation, not a causal explanation. The helpdesk migration on 14 September 2025 also makes simple before-and-after claims risky.

`GW-OTHER` is the largest refund reason over the full period at **₹29.07 lakh**. In Q2 2026 it was **₹5.85 lakh**, about 46% of that quarter's refunds. Because `GW-OTHER` is first in the reason dropdown, validate reason-code use before setting a savings target. Provisionally, a 15% reduction from that baseline would mean **₹4.97 lakh or less** in a comparable quarter, or a potential **₹87,716 quarterly reduction** (about ₹3.51 lakh annualized). This is a target scenario, not confirmed savings. Keep responding-customer CSAT at or above 3.4/5; Q2 2026 averaged 3.46 from 1,039 responses. The dataset does not reproduce a 0.4-point Q4 CSAT increase versus Q3; the observed quarter means differ by about 0.03 points.

The attached monthly tables attribute refunds to the ticket resolver, not necessarily the person who approved, issued, or settled the refund. Policy says Returns Desk processes the large majority, yet the roster attributes only 612 of 2,340 refund tickets (26.2%) and ₹16.93 lakh (25.2%) to that team. Please reconcile this ownership mismatch before using individual totals; Tier 2 work is not comparable to Tier 1 by volume. I also found 166 tickets carrying both a refund and replacement flag. Order references match 158 to a customer and product, and these should be checked against fulfillment and settlement records. Their policy planning cost is ₹2.84 lakh, an exposure estimate rather than confirmed avoidable spend. Escalate confirmed same-order cases to the Team Lead and Finance.

The report is reproducible from the included README and runs locally without paid calls. It reports refunds raised in tickets, not bank settlement or net financial impact. The monthly summary, agent breakdown, validation notes, and review queue are included with the tool.
