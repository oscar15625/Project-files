# V6 recovery checkpoint (2026-10-27)

Status: COMPLETE_FINAL_REPRODUCTION_BASELINE. Conditional mechanisms reproduced; original numerical equilibrium remains unrecovered. All 16 planned cases finished and passed final recorded validation. No experiments are running. No automatic reconnect/resume is scheduled. User will give a new instruction if needed.

Branch codex/maas-v6-final-mechanisms. Final tag maas-reproduction-v6-final. Local bundle backups/maas-reproduction-v6-final.bundle; intermediate bundles maas-v6-core.bundle and maas-v6-experiments.bundle. V5 and older tags remain unchanged.

Deliverables: REPRODUCTION_V6.md; output/pdf/MaaS_reproduction_v6_final_ko.pdf (7 pages, visually inspected); notes/V6_METHOD_REVIEW.md; results/v6/entry_comparison.csv; od_benefits.csv; representative_price_response.csv; local_scaling.csv; manifest.json; final_verification.json with hashes.

Results: small paper wholesale and PT=2 improve operator profits and aggregate welfare. Sioux PT=1 reduces PT profit; PT=2 produces joint operator and aggregate traveler benefit under both node and aggregate MoD specifications. Initial PT wait=1 and transfer PT wait=1 do not remove the PT loss at wholesale=1. Lower transfer penalty increases transfers on both networks. Sioux node PT=2 harms expected utility in 14 ODs (1.72 percent of demand); do not call this every-traveler Pareto improvement.

Three small core cases initially failed the raw capacity-complementarity product tolerance due to tiny positive delays on slack resources. polish_v6.py sets those near-boundary delays to the exact lower bound, reoptimizes conditional fares, recalculates residuals and reruns checks. Original files remain under before_active_set_polish. Maximum time correction 2.82e-8. No economic parameter changed. Do not delete original failure evidence.

Reproduction commands: validate_v6.py; campaign_v6.py core; polish_v6.py; campaign_v6.py diagnostic; analyze_v6.py; verify_final_v6.py; report_v6.py. Use bundled Python or install requirements. Core/diagnostic scripts skip COMPLETE cases; read validation.json/manifest status rather than assuming a COMPLETE marker means a pass. Interrupted root solves resume atomic checkpoints; finalized states are state.npy and metrics.json (these are authoritative after polishing).

Current final scope is closed. Further work, if requested, should be a separate branch for controlled demand heterogeneity and wholesale-benefit conditions, with large-network workload measurements. Do not launch more fitting or contact authors. User's goal is a methodological review at the 2026-12-03 EPFL group meeting. Supplied PDFs/feedback remain local and ignored.
