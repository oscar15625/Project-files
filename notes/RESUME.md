# Resume checkpoint

Updated: 2026-10-21 evening, Asia/Seoul.
Status: **RUNNING_V4**. User changed the schedule on 2026-10-22: start immediately (about 02:40 KST), recovery at 07:40. Old start automation is PAUSED; maas-2 now runs once at 07:40. No author contact.

Current implementation: independent MoD/PT aggregate/node/line-node resources; stable shortest-distance potential transformation of the Shannon Bellman linear system; root mode scale separate from route scale, analytic fare formula uses mode scale and Wright omega; retail/wholesale accounting and first-boarding shares. Atomic NPZ checkpoint and JSONL lifecycle log added to refine.py, including least-squares callbacks and intentional restart test. Tests are running via validate_v4.py, log results/validation_v4.log. Verify that log and results/v4/validation.json before continuing. Next: mixed-scope no-MaaS experiments, then staged common/mode scale sweeps with paired cases and cross-network validation. Supplied follow-up copied to sources/pume_followup.pdf and text; 49 pages, arXiv2607.09568v1 July 10 2026. Read Sections 3,6.1 and Appendix E.1: state scales are allowed; follow-up logit uses 1 and NRL samples [.5,2], NOT evidence for earlier MaaS settings. Implementation uses exact potential transform instead of low-scale log iteration, to be regression-tested.

## Authorization and schedule
- User requests substantial precision improvement using public sources and experiments; author contact is unavailable.
- Immediate start replaces old 01:20 booking; `maas` paused.
- Recovery 2026-10-22 07:40 KST, existing-chat automation `maas-2`.
- Branch `maas-reproduction-2026-10-21`, remote `oscar15625/Project-files`, authorized for milestone backups.

## Completed preparation
- Read 14-page supplied critique text and inspected its key mathematical page.
- Preserved critique locally under ignored `sources/`.
- Created detailed `notes/OVERNIGHT_PLAN.md` including critique hypotheses, source verification, phase ordering, numerical tests, recovery protocol and reporting criteria.
- Created both one-shot automations and verified their saved prompts, schedules and target chat.
- Existing v3 reports/results remain unchanged. Baseline before this preparation: `d956bd9`.

## Exact next action
At or after scheduled start, read `notes/OVERNIGHT_PLAN.md`; inspect `git status --short`, current branch/log, processes and existing run state. Begin Phase 0: add and test periodic atomic checkpoints and restart support BEFORE expensive new research/experiment batches. Then verify the public 2026 PUME follow-up and implement independent MoD/PT access aggregation and accounting diagnostics.

No active simulation process was launched by this scheduling turn. No experimental result from this phase exists yet. Do not restart completed v3 experiments indiscriminately. This file must be updated after every meaningful stage so a fresh execution can resume without reconstructing chat history.

## Known baseline cautions
- Old results include rejected/degenerate equilibria; consult audit.json and final_manifest.json.
- Existing solver checkpoints are completion-only; interrupted runs are not yet resumable mid-iteration.
- Do not call a node-access variant the original experiment; behavior scale and units remain unverified.
- PDF feedback suggests contacting authors, but user's current instruction explicitly excludes that route.
- Usage reset may not occur exactly at 06:30; the scheduled attempt does not bypass limits or guarantee runtime availability.
