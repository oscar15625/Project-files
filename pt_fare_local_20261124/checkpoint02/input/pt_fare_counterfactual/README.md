# MaaS PT fare counterfactual (2026-11-24)

**Scope**: Sioux Falls structure audit (original source PT lines + positive-demand OD pair shortest PT link counts) **AND** independently executed **small network** PUMCM-VI tariff experiments. **Not** a full Sioux Falls fare re-equilibration or an empirical fare validation.

Main Korean report: `PT_TARIFF_COUNTERFACTUAL_REPORT_KR.md`

Core results: `results/summary.csv`, `results/paired_comparison.csv`, `results/od_shares.csv`, `results/sioux_station_od_hops.csv`.

Code: `fare_models.py` (fare-tracking state in NON-MaaS only), `run.py` (A/C solves), `audit.py` (PT-price-zero regression, revenue accounting and multi-start), `od_analysis.py` (OD choices), `create_report.py` (plots/report). Existing 2026-11-20 cloud extract is nested under `maas_cloud_study/` to supply the original small network and stored baseline vectors.

Run from the unpacked `pt_fare_counterfactual/` directory:

```
python -m pip install numpy scipy matplotlib
OPENBLAS_NUM_THREADS=1 python run.py
OPENBLAS_NUM_THREADS=1 python audit.py
OPENBLAS_NUM_THREADS=1 python od_analysis.py
OPENBLAS_NUM_THREADS=1 python create_report.py
```

The four-zone assignment is an **illustrative topology scenario** `{1,2}, {3,4}, {5,6}, {7,8}`, not Lausanne Mobilis's actual zones.
