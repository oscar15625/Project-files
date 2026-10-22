# Project-files

## Revision 4 (2026-10-22)

Latest: [Korean precision-reproduction report](REPRODUCTION_V4.md), [PDF](output/pdf/MaaS_reproduction_v4_ko.pdf), [all run statuses](results/v4/manifest.json), [metric comparison with the paper](results/v4/paper_errors.csv).

Adds independent MoD/PT access scopes, total-capacity controls, root-mode versus route scales, stable Shannon Bellman solves, accounting and first-boarding exports, small-network figure variants, and recoverable iteration snapshots. The supplied 2026 PUME follow-up supports the mathematical specialization but does not identify the original MaaS experiment's parameters. Quantitative replication remains incomplete; `PASS` means the recorded numerical/deviation/accounting checks passed, not proof of a global equilibrium or agreement with the paper.

```text
python validate_v4.py
python batch_v4.py scope
python batch_v4.py common
python batch_v4.py mode
python repair_v4.py
python topology_v4.py
python global_response_v4.py
python report_v4.py
python verify_manifest_v4.py
```

Batch scripts skip completed runs and recover unfinished runs from immutable checkpoints. Preserve failed trials and use a new tag for a new start. Details and recovery state: [notes/RESUME.md](notes/RESUME.md). Sources and conditional analytical bounds: [notes/FOLLOWUP_LEDGER.md](notes/FOLLOWUP_LEDGER.md). The PDF generator uses Windows Malgun fonts; scientific calculations do not require those fonts.

## MaaS / PUMCM reconstruction (2026-10-21)

See [the Korean report](REPRODUCTION.md) and [the PDF report](output/MaaS_reproduction_report.pdf).

Status: an independently implemented, tested equilibrium simulator; **not a successful quantitative replication of the paper**. Missing behavioral and access-aggregation specifications materially affect results. Both the literal aggregate-access interpretation and an explicitly alternative node-access model are retained.

Install Python 3.12 dependencies with `python -m pip install -r requirements.txt`. Then:

```text
python validate.py
python experiments.py --network small --access node
python experiments.py --network sioux --access node
python sensitivity.py
python audit.py
python export_results.py
python make_report.py
```

Use `--access aggregate` for the literal network-wide access interpretation. `run.py` implements the paper's extragradient iteration; `refine.py` solves the constructed VI using a documented auxiliary method. Reported final comparisons use the latter, not the original convergence trajectory.

`results/final_manifest.json` identifies comparison runs. A `converged` flag certifies the numerical residual only; consult `audit.json` for strategic deviation checks. Earlier failed/degenerate experiments are deliberately preserved and must not be cited as final equilibria. In particular, `sioux_aggregate_theta1_with` failed its deviation check; use `sioux_aggregate_corrected` instead.

Inputs are attributed and hashed in `data/provenance.json`. Supplied PDF sources and local dependency bundles are excluded from Git. Full assumptions and outstanding replication work are in the report.
