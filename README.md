# Project-files

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
