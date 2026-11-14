# VI solver and cloud nested-choice audit

{
  "date": "2026-11-14",
  "original_m01": "27 completed, 0 accepted; preserved",
  "initial_flow_time_attempts": 12,
  "initial_attempts_pass": 2,
  "score_original_strict_pass": 9,
  "score_original_runs": 9,
  "score_cloud_strict_pass": 9,
  "score_cloud_runs": 10,
  "demand_ablation_strict_pass": 1,
  "demand_ablation_runs": 3,
  "model_source_sha256": "e138fd4f803a2ab5952c7e4d14b47a353bfc1f409c2634a71bb861b1d9338769",
  "cloud_source_sha256": "0d60c74b28ac443143aeb9cc41e1f7da72d9451a95293831348dc6f9982d66b6",
  "cloud_input_files_unchanged": 123,
  "score_identity_checks": 12,
  "scope": "Small network cold starts; no original PG/EG or M03 rerun; not original paper EG reproduction or global Nash proof",
  "fallback_strict_pass": 2,
  "fallback_runs": 2,
  "cloud_cases_with_at_least_one_strict_pass": 10
}

| Case | Start | Fare scaling | Status | Strict time PASS | Solver H | Full scaled |
|---|---:|---|---|---|---:|---:|
| A_no_maas | 1.0 | DEMAND | PASS | True | 2425 | 1.25e-11 |
| A_no_maas | 0.95 | SCORE | PASS | True | 858 | 3.22e-14 |
| A_no_maas | 1.0 | SCORE | PASS | True | 2425 | 1.25e-11 |
| A_no_maas | 1.05 | SCORE | PASS | True | 2071 | 8.18e-12 |
| B_lambda0.55 | 1.0 | SCORE | PASS | True | 1976 | 1.50e-11 |
| B_lambda0.65 | 0.95 | SCORE | PASS | True | 1347 | 6.36e-14 |
| B_lambda0.65 | 1.0 | SCORE | FAILED_VALIDATION | False | 8000 | 2.34e-03 |
| B_lambda0.65 | 1.05 | SCORE | PASS | True | 1977 | 1.24e-11 |
| B_lambda0.75 | 1.0 | SCORE | PASS | True | 1934 | 1.82e-11 |
| B_lambda0.85 | 1.0 | SCORE | PASS | True | 1765 | 1.44e-11 |
| B_lambda1.00 | 1.0 | SCORE | PASS | True | 1765 | 1.41e-11 |
| B_maas_no_transfer_advantage | 1.0 | DEMAND | FAILED_VALIDATION | False | 1697 | 7.96e-10 |
| B_maas_no_transfer_advantage | 0.95 | SCORE | PASS | True | 840 | 6.52e-14 |
| B_maas_no_transfer_advantage | 1.0 | SCORE | PASS | True | 1765 | 1.41e-11 |
| B_maas_no_transfer_advantage | 1.05 | SCORE | PASS | True | 1808 | 1.55e-11 |
| C_lambda0.55 | 1.0 | SCORE | PASS | True | 3447 | 7.42e-12 |
| C_lambda0.65 | 1.0 | SCORE | PASS | True | 3363 | 3.04e-12 |
| C_lambda0.75 | 1.0 | SCORE | PASS | True | 2731 | 9.49e-12 |
| C_lambda0.85 | 1.0 | SCORE | PASS | True | 2398 | 2.44e-12 |
| C_lambda1.00 | 1.0 | SCORE | PASS | True | 2437 | 7.37e-12 |
| C_maas_paper_advantage | 1.0 | DEMAND | FAILED_VALIDATION | False | 6555 | 3.05e-01 |
| C_maas_paper_advantage | 0.95 | SCORE | PASS | True | 1640 | 6.87e-14 |
| C_maas_paper_advantage | 1.0 | SCORE | PASS | True | 2437 | 7.38e-12 |
| C_maas_paper_advantage | 1.05 | SCORE | PASS | True | 2395 | 1.94e-13 |

| Accepted case/start | Platform profit | Welfare gain vs A | Harmed ODs | Max price diff vs cloud |
|---|---:|---:|---:|---:|
| B_lambda0.55 / 1.0 | 44.4024 | 26.9381 | 1 | 1.64e-11 |
| B_lambda0.65 / 0.95 | 60.3635 | 41.7660 | 1 | 1.91e-11 |
| B_lambda0.65 / 1.05 | 60.3635 | 41.7660 | 1 | 1.91e-11 |
| B_lambda0.75 / 1.0 | 77.4160 | 57.9264 | 0 | 5.49e-10 |
| B_lambda0.85 / 1.0 | 95.3187 | 75.3207 | 0 | 2.24e-11 |
| B_lambda1.00 / 1.0 | 123.3973 | 103.2870 | 0 | 2.82e-11 |
| C_lambda0.55 / 1.0 | 64.2866 | 83.9473 | 0 | 3.78e-09 |
| C_lambda0.65 / 1.0 | 82.6079 | 101.5011 | 0 | 5.55e-10 |
| C_lambda0.75 / 1.0 | 101.7745 | 120.6276 | 0 | 1.15e-09 |
| C_lambda0.85 / 1.0 | 121.5836 | 140.9217 | 0 | 1.43e-11 |
| C_lambda1.00 / 1.0 | 152.2156 | 172.8628 | 0 | 1.50e-11 |

Same VI complementarity conditions, cold starts, flow coordinates, stable per-customer fare score. This is a trust-region residual root solver, not the paper EG algorithm. All original failures are preserved. Cloud model tests and archived states were independently replayed. Finite price audits are not a global Nash certificate. Timing across sessions is descriptive only. The 8000 solver-H cap counts numerical Jacobian evaluations; validation is reported separately.
