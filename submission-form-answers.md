# Submission-form answers (draft)

Drafted from the form prompts visible in the task screenshots. The actual `submission-form.md` was not among the uploaded files, so copy these into its matching fields if its wording differs.

## What did you build, and what business outcome does it move? State the number and the money.

I built a local Python refund-audit tool that deduplicates tickets, converts legacy amounts, and produces monthly refunds by reason and resolving agent. Q2 2026 `GW-OTHER` is ₹5,84,774 across 209 refunds. Because it is first in the dropdown, validate coding first; provisionally, a 15% reduction would be ₹87,716 per quarter (about ₹3,50,864 annualized), with responding-customer CSAT at or above 3.4/5. This is a monitored scenario, not proven savings.

## What does one run cost, and what would a month cost at Vireo's volume (roughly 650 tickets a week)? Show the arithmetic. If you used no paid calls, say so.

₹0 per local run; 650 tickets/week × 52 weeks ÷ 12 ≈ 2,817 tickets/month; 2,817 × ₹0 = ₹0/month. The tool uses Python's standard library and makes no paid model/API calls. This excludes existing hardware and human review time.

## How do you know it works? Sample size, how you checked, error rate, and the kind of case it gets wrong.

I checked all 12,238 rows for IDs, source overlap, units, and tie-outs, then checked a 25-ticket stratified sample across duplicated IDs, legacy-only refunds, helpdesk-only refunds, blanks, and refund-plus-replacement flags. The 638 paired IDs agree after normalizing legacy amounts; monthly, reason, and agent reports independently sum to ₹67,09,932 across 2,340 unique refund tickets. The 8 ambiguous refund-plus-replacement order matches stay unresolved. The output is a ticket-level refund report, not a settlement reconciliation.

## Did you change, narrow, or push back on the client's ask? What, when, and why?

I kept the requested monthly reason and agent summaries, but narrowed “who is giving away money” to descriptive attribution: `agent_id` identifies the ticket resolver, not necessarily who approved or issued the refund. Policy says Returns Desk handles most refunds, while only about a quarter are attributed to its resolvers here; that ownership mismatch needs investigation. Tier 2 cases are not comparable with Tier 1 by raw volume. I added a separate refund-plus-replacement review queue and avoided labeling agents as improper without case-mix and settlement evidence.

## What is wrong with what you are handing us? Be specific: bugs, shortcuts, things you know are off.

The tool depends on the stated legacy ÷100 rule and helpdesk-preferred dedupe rule. It does not validate cash settlement, replacement delivery, or GL posting. The 166 dual-flag cases include 8 ambiguous reference matches; the 158 matched cases still need fulfillment/settlement confirmation. The agent report is descriptive and should not be used as an unadjusted performance ranking. Monthly trend comparisons cross the 14 Sep 2025 helpdesk migration.

## What did you deliberately leave out, and why that rather than something else?

I left out automatic LLM calls, hosted deployment, prediction, settlement matching, a highest-refund-agent ranking, and causal claims about the Q4 service instruction. A local deterministic calculation is cheaper and reproducible for finance; the supplied pack has no payment ledger or control group. The optional AI-ready prompt contains aggregates only.

## Anything you built or found that nobody asked for?

The order-linked exception queue finds 166 tickets with both a refund and replacement flag. It matches 158 to a customer/product order (including unique fallbacks); their policy planning replacement cost is ₹2,84,170. This is a review estimate, not confirmed avoidable spend. I also found a mismatch between the policy's expected Returns Desk ownership and resolver-team attribution, and that `GW-OTHER` is the dropdown's first option.

## What did you use AI for? Tools/models, where they helped, where they wasted time, what you threw away. Link your three-minute screen recording here.

I used OpenAI Codex (GPT-6) as a coding and analysis assistant to structure the reconciliation, draft and refine the report generator, inspect data excerpts and aggregate results, and draft the memo and validation notes. I corrected an initial timestamp parsing issue during iteration. I discarded the unadjusted raw refund sum and an unadjusted agent ranking because they were misleading. The tool makes no paid API/model calls; the optional prompt it writes contains aggregates only. Recording: **[paste the reviewed public Google Drive link]**.

## Someone picks this up on Monday and you are unreachable. The three things they need to know.

1. Run `python refund_audit.py` from this folder; reports are written under `reports/`.
2. The reconciled total is ₹67.10 lakh for Jan 2025-Jun 2026: each ticket ID once, legacy-only refunds divided by 100.
3. Review the 158 matched refund-plus-replacement candidates against settlement and fulfillment before treating the ₹2.84 lakh planning-cost proxy as savings or a policy breach.

## Honest hours spent. One number.

**[Enter your actual personal hours spent on the assignment as one number; do not use the assistant's elapsed time.]**

## GitHub Repo Link

**[Paste the public repository URL after you create and review it. This local folder is ready to upload; no public repository has been created.]**
