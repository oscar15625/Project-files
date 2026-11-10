# MaaS v7.1 Small Network — independent replay

This package is an independent Shannon-specialization reconstruction, not the authors' source code or an empirical market model. It includes the Small network as JSON/CSV and Python, exact saved representative states, failure examples, reports and dependency versions. No original PDFs, user prompts or credentials are included.

## Safe default (no optimization)

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-cloud.txt
python cloud_replay.py
```

Use a Python version compatible with NumPy/SciPy; the recorded original environment is in the evidence archive. The locked scientific versions are numpy 2.5.4, scipy 1.18.1 and matplotlib 3.11.2. `requirements-cloud.txt` gives compatible major-version ranges for cloud environments where the exact locked wheels are unavailable; numerical replay must pass before accepting a different environment. No environment-independent timing equivalence is claimed. Local extracted-package replay is tested on Windows. Linux is designed for portability but is not claimed tested here.

The default evaluates saved Small states once each. It checks input identity, selected economic metrics, original-time natural residuals, retained-coordinate residuals and preservation of numerical failures. It writes only a new timestamped `cloud_runs/` directory. `PASS_SAVED_STATE_REPLAY` means values were reproduced, not that failed EG states became equilibria. For source integrity, verify `PACKAGE_MANIFEST.json` hashes before editing. New results should have new paths and their own manifests.

## Explicit, bounded simulation

```bash
python cloud_replay.py --simulate-steps 20
```

This is a new short diagnostic, never a substitute for the registered 20,000-H benchmark or a certified equilibrium. The option is capped at 200 steps. The current recovery task did not run it. Existing states are never modified. Full Windows campaign scripts in the shared repository are archival reproducibility tools; they have platform-specific memory measurement and dependencies on full local baselines. Do not run their main routines in an unreviewed cloud checkout. Use this portable entry point first.

## Interpretation and scope

- Original M01: 27 attempts complete, 0 accepted under the registered original-variable criteria; failures are retained.
- Nine local contract-boundary cases and twelve M02 traffic probes were saved before interruption.
- M03 JOINT_AUX passed. NESTED_SAME_VI was interrupted without a final state or numerical checkpoint; its cost is unknown and speed comparison is NOT_COMPARABLE.
- The preserved November reconstruction uses node-level MoD access aggregation, unlike the original paper's stated total aggregation. Small-network calibration and exact paper-level quantitative agreement remain unresolved.
- Frozen duplication tests are not equilibrium or causal decompositions. Aggregate improving contracts do not prove individual Pareto improvement.

Keep the original acceptance thresholds. Do not interpolate an equilibrium, erase a failure, modify a saved baseline, or infer convergence from small consecutive-iterate differences alone. Review `Detailed_Review_KR.md` and `Technical_Report_EN.md` for evidence and limitations.
