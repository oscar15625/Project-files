# Replay and handoff

Extract the ZIP into a short folder. Use Python 3.12 (tested 3.12.14) and install requirements.txt into an isolated environment. Run `python verify_presentation_release.py > replay_output.json` with the output redirected OUTSIDE the extracted release (the manifest disallows unexpected files). The command runs saved-state evaluations and kernel/derivative checks, never an equilibrium optimizer. Bytecode caches are excluded from inventory checks.

Read baseline_audit/replay.json for the original build audit. verify_presentation_release.py checks whole-release hashes, schemas, source-derived figures' numbers, status preservation, economics and natural residuals, and 18 nested checks. Archived price-deviation optimizer searches are not rerun. The source-derived facts must match the frozen facts exactly on the source read; floating-point replays allow documented tolerances.

baseline/replay_vi_results_20261114.py can independently replay just the original24. Old source runners are historical evidence, not the default entry point. Never rerun them into protected results directories. To extend after the freeze, create a new branch/output directory and record input hashes first. No pending solver or scheduled continuation remains in this release. E05 is design-only and requires fresh implementation/gates, not continuation from a hidden checkpoint.

SHA256SUMS covers all payloads plus RELEASE_MANIFEST; the manifest hashes all payloads excluding itself and SHA256SUMS to avoid circular hashes. DELIVERY.json lives beside the ZIP and identifies the public commit and ZIP hash. Windows replay is verified; cloud Linux execution remains a user-side portability test.
