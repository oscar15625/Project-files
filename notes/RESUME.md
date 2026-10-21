# Resume checkpoint

Updated: 2026-10-22 about 02:53 Asia/Seoul.
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
Check processes before launching duplicates. Active batch scripts: `batch_v4.py scope`, `batch_v4.py common`, `batch_v4.py mode`, and `repair_v4.py`. Logs: results/v4_scope.log, v4_common.log, v4_mode.log, v4_repair.log. Each accepted optimizer step has an immutable snapshot in each result's checkpoints/ directory. Rerun the same script to skip completed metrics and resume unfinished runs. Failed metrics are preserved and skipped, not silently retried; additional starts use a distinct tag. On completion, aggregate all v4 metrics/audits into an honest comparison report; do not treat residual-only stationary points as equilibria. In particular sioux_common_0.2_without passed residual but FAILED the deviation check (PT gain ~20,738). Some small aggregate starts fail; repair_v4.py adds warm starts from the prior validated aggregate case.

Methods checkpoint 5927bae pushed to authorized GitHub branch; local backups/v4-methods.bundle. Validation passed, including forced restart. Many v4 simulations are now running/completed. Update this file after the next milestone.

## Known baseline cautions
- Old results include rejected/degenerate equilibria; consult audit.json and final_manifest.json.
- V4 checkpoints support restart after each accepted iteration; the earlier v3 files were completion-only.
- Do not call a node-access variant the original experiment; behavior scale and units remain unverified.
- PDF feedback suggests contacting authors, but user's current instruction explicitly excludes that route.
- Usage reset may not occur exactly at 06:30; the scheduled attempt does not bypass limits or guarantee runtime availability.
