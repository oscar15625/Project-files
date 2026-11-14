# Improved VI solver / cloud nested-choice handoff — 2026-11-14

Results: original Small MNL SCORE solver 9/9 strict PASS, nested choice default starts 9/10 strict PASS, B lambda=.65 additional starts .95 and 1.05 both PASS. All 10 nested model configurations therefore have accepted solutions, but the default-start failure is preserved. Matched DEMAND normalization control passed 1/3. Original 27 PG/EG failures and first 12 root trials (2 accepted) are not overwritten.

Read `results/vi_cloud_20261114/REPORT_KR.md`, `REPORT_EN.md`, `all_results.csv`, `cloud_comparison.csv`, and `summary.json`. New solver: `vi_robust_20261114.py`. It solves equivalent complementarity residuals with flow coordinates and a stable per-customer platform-fare condition. It is a trust-region root method, **not** an improved implementation of the original paper's EG iteration. No equilibrium warm starts were used. The same nested-choice VI was preserved, including fixed-time partial price derivatives. No MNL-only closed-form fares were used in the nested model.

## Portable verification first

```bash
python -m pip install -r requirements-cloud.txt
python replay_vi_results_20261114.py
```

The portable script evaluates 24 saved states and preserves their PASS/FAIL labels. It does not optimize, require original cloud folders, or call Windows memory APIs. The default dataset includes 9 MNL cases, 3 controls, 10 nested default cases, and 2 explicitly labeled retries. All cases have configuration, raw/final state arrays, trace/checkpoint, H counts, price audits and original-time/auxiliary residuals.

This extracted ZIP is tested on Windows using the recorded numerical libraries. Linux replay is designed to be portable but is not claimed tested locally. The exact prior numerical versions were NumPy 2.5.4, SciPy 1.18.1; compatible ranges are in requirements-cloud.txt. Validate before changing libraries or claiming numerical equivalence.

`python vi_robust_20261114.py` is the **optimizer campaign** (not the safe default). It skips cases with COMPLETE.json. To develop new experiments, register a separate output path and settings; do not remove COMPLETE or overwrite failed cases. `vi_retry_20261114.py` records the two already completed sensitivity runs. Audit/report scripts additionally reference the original user-provided archive locations and are local provenance tools, not the portable replay entry point.

## Interpretation

The inherited cloud archive passed 18 kernel/regression/gradient tests and 10 saved-state audits. Its manifest contained 118 entries; all 123 inspected input files were unchanged. One wording correction: the M03 retail-price difference is 2.66e-9, while all prices including MaaS fares differ by 4.01e-8. No cloud model defect was found in these tests. Broad finite price grids/refinement supplement the archived local deviation probes, but neither is a global Nash proof.

The reduced inverse-BPR singularity and demand-normalized fare residual help this Small problem. Step shrinkage, inactive resources, and flat near-zero-demand price gradients are distinct numerical issues. A root solver can stop at nonzero residual or economically invalid stationary candidates; those failures remain visible. The new method has no global convergence or large-network performance guarantee. Whole-network vs node-based MoD access remains an original-paper reconstruction difference.

Runtime figures from different sessions are descriptive. Solver H counts include numerical Jacobian calls; final validation calls are separate. The inherited PG/EG trials had a 20,000-H budget, the new methods 8,000; do not describe that as a matched timing benchmark.

## Files and recovery

The ZIP is a portable **verification** bundle with code, Small inputs/reference configs, new states and logs, plus the preserved first-improvement failures. It is not a replacement for the earlier full recovery archive. PACKAGE_MANIFEST.json verifies exported bytes. Text metadata has local personal paths normalized; original local hashes remain provenance, not an assertion that redacted exports have identical text bytes. Binary .npy states are byte-preserved.

Local raw outputs and the unredacted source-input hash record remain in the canonical research_run directory. GitHub sharing occurs on the new branch `codex/vi-solver-cloud-validation-20261114`; the prior published v7.1/M03 branch remains intact. If interrupted, inspect actual processes before resuming. checkpoint.npy is a candidate coordinate vector, not a serialized SciPy trust-region optimizer. Start a separately recorded attempt if necessary and preserve failed results.
