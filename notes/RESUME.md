# Resume checkpoint

Updated: 2026-10-22 12:15 Asia/Seoul (verified system clock).
Status: **V4_CAMPAIGN_COMPLETE; QUANTITATIVE_REPLICATION_INCOMPLETE**.

All 82 planned primary trials and 7 additional deviation-informed starts completed. No experiment remains running or partially executed. 89 records: 55 PASS, 18 rejected by unilateral-price deviation checks, 16 not converged, zero execution errors/incomplete. PASS means numerical/deviation/accounting validation, not proof of global Nash equilibrium or agreement with the paper. All 55 accepted OD exports independently reproduce aggregate results within 5.6e-9. Forced-interruption restart agreed within 3.4e-12.

## Deliverables
- REPRODUCTION_V4.md and output/pdf/MaaS_reproduction_v4_ko.pdf (Korean, five pages).
- results/v4/manifest.json, summary.csv, paper_errors.csv, campaign_completion.json, export_verification.json.
- Per-run configurations, metrics, state, OD/resource CSV, audit, iteration histories and immutable checkpoints.
- notes/FOLLOWUP_LEDGER.md records source evidence and conditional Jensen bound mu_mode <= 0.02003 for the paper's reported MaaS share/profit under interior Shannon OD pricing.

## Authorization and scheduling
- User authorized immediate start, no author contact, public sources/experiments, and backups to oscar15625/Project-files branch maas-reproduction-2026-10-21.
- Original 01:20 automation maas paused; maas-2 was moved from 06:30 to 07:40.
- Since this campaign is complete, maas-2 is now PAUSED. Do not restart the finished campaign automatically or imply successful quantitative replication.

## Reproduction and recovery
Use bundled Python or install requirements.txt. README lists commands. batch_v4.py scope/common/mode skip completed runs and recover interrupted states; repair_v4.py and topology_v4.py preserve alternate starts/structures. global_response_v4.py tries up to three price-deviation starts. report_v4.py regenerates summaries/PDF; verify_manifest_v4.py checks OD-derived results; verify_campaign_v4.py verifies all 82 planned trials have termination records. Failed trials should be retained, with any new attempt using a new tag. Source PDFs remain ignored/local.

## Findings and next direction
Independent MoD/PT access scopes, total-capacity controls, separate mode/route scales, and small-network figure variants did not jointly reproduce the paper's shares/prices/profits. Figure-versus-appendix small-network differences have negligible influence in the tested settings. Low scales produce multiple stationary points and profitable deviations; root convergence alone is insufficient. Do not claim a failed solver proves a behavioral model impossible. The direct-reading aggregate-MoD/node-PT case has Sioux driving 62.17% to 59.50%, MaaS 14.27%; the paper has 48.5% to 40.3%, MaaS 39.5%.

Further scientific work, if continued, should focus on identifying the smooth surplus/perturbation function, service-access units and normalizations, and mode/transfer accounting from public sources. No author contact. Avoid arbitrary rescaling or fitting one target. Validate no-MaaS settings first, then hold them fixed for MaaS and cross-network comparisons. Any new generalized perturbation model must be an explicit hypothesis with analytic/finite-difference verification and deviation tests.

## Backups
Methods 5927bae; intermediate experiments 254943d; topology/report code 29740be. Final revision is tagged maas-reproduction-v4. Local final bundle: backups/maas-reproduction-v4.bundle. Verify git log/tag and remote branch for the exact final SHA.
