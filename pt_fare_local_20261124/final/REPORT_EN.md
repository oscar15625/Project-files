# Full-demand Sioux Falls PT tariff counterfactual

Four primary equilibria and eight perturbed-start solves passed strict validation. This is an independent Shannon/MNL VI counterfactual, not a numerical replication of the paper's Table 3.

| 운임/조건 | MaaS % | PT 단가 | PT 이익 | MoD 이익 | MaaS 이익 | 이용자 기대효용 |
|---|---:|---:|---:|---:|---:|---:|
| LINK A | 0.0000 | 2.84682 | 308,438.84 | 101,042.70 | 0.00 | -9,600,955.38 |
| LINK C | 14.2734 | 1.82046 | 222,150.81 | 125,859.01 | 115,967.56 | -8,318,515.42 |
| FLAT A | 0.0000 | 5.43090 | 314,620.45 | 99,588.84 | 0.00 | -9,374,540.87 |
| FLAT C | 14.7477 | 3.26642 | 220,281.85 | 125,326.76 | 119,703.29 | -8,320,069.71 |


The pinned source is b682637921d843bc2edac8f154b5d03f21fa257a. All528 OD and432,720 trips are retained. MoD access is aggregate; PT access capacity is node-specific. Only non-MaaS PT retail charging changes between link-based and first-PT-entry-per-journey charging. Wholesale, demand, supply and all other choice assumptions remain fixed between tariffs. No Sioux zone map was supplied; no zonal full-network experiment was invented.

MaaS share rises from 14.2734% to 14.7477%. The matched PT profit changes are -86288.02 and -94338.60, respectively. Both are losses in this full-network configuration, unlike the positive LINK effect in the supplied Small study. Lost retail receipts exceed incremental wholesale receipts. See paired_comparison.csv, physical_service.csv and od_welfare.csv.

The solver uses flow coordinates and exact conditional MNL fare elimination, retaining the original fixed-traffic retail-price VI conditions. HYBR with bounded TRF fallback is a root method, not an extragradient improvement. All OD fares, traffic times and retail prices are jointly consistent at the final state. Two retail-price factors(.8/1.2) plus small traffic perturbations per condition are sensitivity checks, not global uniqueness proofs. See VALIDATION_SUMMARY.json for residual, Markov balance, accounting, deviation and finite-difference checks. Solver H counts include numerical Jacobian calls but exclude post-solve validation calls.

Windows Python 3.12.14, NumPy 2.5.4, SciPy 1.18.1. Linux execution has not been performed locally. python verify.py replays archived states without optimization. Original source PDF and private paths are not distributed. The frozen20261115 release is untouched.
