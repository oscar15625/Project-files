# MaaS Research v7.1 — run, verify and recover

Branch: `research-v7-1-critical-validation`. Source baseline: **November** `research-handoff-20261108`, not the October v6-final run. Output: `results/research_v7_1`. No remote push is authorized for this task.

## Read first

- `results/research_v7_1/Detailed_Review_KR.md`: detailed review in Korean.
- `results/research_v7_1/Technical_Report_EN.md`: technical report in English.
- `results/research_v7_1/claim_evidence_ledger.csv`: presentation-safe claims and limitations.
- `results/research_v7_1/validation.json`: artifact integrity status; **not** an assertion that all numerical attempts converged.
- `results/research_v7_1/manifest.json`: evidence SHA256 hashes.
- `results/research_v7_1/experiment_manifest.json`: registered settings, thresholds and original input hashes.

Run all commands from `MaaS_Codex_v6_All/research_run`. The Python used is `<LOCAL_USER>/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`. The bootstrap imports the existing local `.vendor` dependencies. No dependency installation is needed. Exact versions and thread variables are recorded in `environment.json`. A plain `python` below denotes that executable.

## Dependency order

```text
python research_v71.py
python research_v71_m01.py campaign
python research_v71_extra.py
python research_v71_micro.py
python research_v71_report.py
python verify_research_v71.py
```

The first script only reanalyzes saved source states and builds R00 / Milestone A. M01 is the actual projection benchmark: 27 isolated, sequential processes with 20,000 solver H calls per attempt. Each solver call, including rejected adaptive trials, is logged; final validation calls are counted separately. Run M01 alone, without other experimental workloads. Extra performs nine registered boundary solves, twelve strategic-timing probes and two same-VI prototypes. Reports are generated only after raw experiments exist. The verifier re-evaluates states and checks counts, identities and old-source hashes.

Never execute old `research_v6`/`research_v7` main runners to regenerate v7.1: they target protected output directories. Never delete a failure or replace the original 63/64 grid with a diagnostic retry. Never label PG/EG final iterates as equilibria merely because their profits look close to a root-solver reference.

## Safe interruption recovery

1. Inspect `results/research_v7_1/running.json`, `v71_m01.log`, per-attempt `execution.log`, and `notes/RESUME_RESEARCH_V7_1.md`. Check Windows processes and command lines before starting anything. A stale RUNNING file alone is not proof that a process is alive. Do not launch a second copy while the first remains active.
2. Verify the existing Git bundle and `protected_hashes.json`. Do not change source models, tags or old results. Completed M01 attempts have `metrics.json` and are skipped by the campaign runner.
3. For an interrupted M01 attempt without `metrics.json`, **archive the entire attempt directory** under `results/research_v7_1/interrupted_attempts/<timestamp>/` before restarting that attempt. Preserve its configuration, events, trace, checkpoint and logs. Record consumed H evaluations and interruption time in the resume note. This restarts only that incomplete timing replicate; it avoids mixing wall-time segments or counting replayed checkpoint events as uninterrupted work. Do not use the runner's low-level checkpoint continuation for a publishable fair-timing result. Interrupted work remains separately disclosed.
4. Restart the campaign only after no old process remains. Completed attempts are not rerun. If a `failed_process.json` is present without final metrics, preserve it with the interrupted attempt and investigate the execution log first.
5. Extra skips completed case metrics. Preserve incomplete raw solver files and logs before retrying an incomplete extra case. A final metrics file with a numerical FAIL is a completed failed attempt, not permission to silently overwrite it.
6. Regenerate reports and run the verifier. Final integrity must not be inferred from file existence. In particular, missing results must never be converted to NOT_RUN without explanation.

## Provenance and acceptance

`provenance/` preserves the source versions imported during the M01 campaign. The later R00 wording adds classification details without changing the benchmark operator or numerical protocol. `protected_hashes.json` seals old V4/V5/November v6/v7 results and relevant source files. Per-run configurations identify the source-state hashes and solver settings.

The inherited root-reference acceptance uses saved auxiliary flow coordinates and separately reports original-time natural residuals. The original-variable PG/EG benchmark uses its actual time vector; it is never root-polished. This qualification is visible in both reports. Additional local solutions and the nested prototype are diagnostics with their own complete final checks.

Cost scenarios are post-processing hypotheses, frozen product crosses are not equilibria, and OD-average utility is not individual welfare. M02 finite traffic-response probes change strategic timing. The nested prototype keeps the original fixed-time partial-price conditions; it does not turn operators into leaders optimizing a total derivative through traffic responses.

## Backups

Milestone A is committed and bundled as `backups/research-v7-1-A.bundle`. The final bundle and byte-preserving results ZIP are recorded in the resume note after verification. Bundles preserve Git history; the ZIP preserves exact CSV/JSON byte hashes independently of Git line-ending settings. Keep both. Restore to a separate directory and verify before replacing any working tree.

```text
git bundle verify backups/research-v7-1-A.bundle
git status --short
git log -3 --oneline
```

Remote push, author contact, empirical fare calibration and Phase C market extensions are not part of the completed numerical claims. New model variants require new registered configurations and separate output paths.
