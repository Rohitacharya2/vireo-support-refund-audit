# Five-hour task plan

The assignment says five hours is the cap. This sequence prioritizes a clean, defensible answer over broad feature work.

| Time | Work | Done when |
|---|---|---|
| 0:00-0:30 | Read the brief, email thread, README, and support policy. List ambiguities and decide reconciliation rules. | Legacy units, duplicate IDs, business definitions, and client request are written down. |
| 0:30-1:15 | Profile all inputs: row counts, timestamps, IDs, blanks, refund values, reasons, and agent keys. | A short data-quality inventory explains the raw total mismatch. |
| 1:15-2:15 | Build the smallest reliable local report generator. | Clean-machine command creates month totals, reason totals, agent totals, and policy review queue. |
| 2:15-3:00 | Reconcile totals and inspect a stratified sample. | Reason, agent, and month totals tie; edge cases and limitations are documented. |
| 3:00-3:40 | Calculate one measurable goal and its money scenario with a customer-outcome guardrail. | Memo can state a baseline, target, arithmetic, and caveat. |
| 3:40-4:20 | Write the one-page memo and finish technical README/validation notes. | Another person can understand the conclusion and rerun the tool. |
| 4:20-4:45 | Prepare the submission-form answers and three-minute recording script. | Links/hours are the only items requiring the candidate's actual actions. |
| 4:45-5:00 | Run once from a fresh output folder, inspect reports, rehearse, and stop. | Final files agree and recording can stay under three minutes. |

## What to build first

1. Normalize the money and remove duplicate ticket IDs.
2. Tie out totals by month, reason, and resolving agent.
3. Add a narrow policy exception review for refund-plus-replacement flags.
4. Write validation before styling or adding a dashboard.

## What to omit under the cap

Skip a hosted app, automatic LLM calls, per-agent blame ranking, prediction, and settlement claims. They add cost or risk without improving the first finance answer. Keep the optional AI prompt aggregate-only. Do not spend time on charts until the reconciled CSVs and memo are correct.
