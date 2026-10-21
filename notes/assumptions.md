# Reconstruction ledger

Primary source: Yao, Ma, Zhang (2026), TRC 188, 105703, supplied published PDF.
Reference: supplied four-page PUMCM TRISTAN XII extended abstract (2025).

Confirmed: equations 4-11 (choice/loading/sensitivity), 13-21 (VI), 24-25 (extragradient), 26 (BPR), 27 (service pricing); Tables 1, A1, A2; Appendix A parameters.

Unspecified: experimental perturbation function/scale, numerical upper bounds, initialization, exact dummy-link construction, and precise mode-share aggregation. We use Shannon negative entropy, scale 1, discount 1, as in the reference abstract's simulation. This is a PUMCM specialization, not an assertion about the authors' code. Linear solves of the exponentiated Bellman equation are equivalent to converged value iteration for this specialization.

Small roads are directed as Fig. 3; PT lines are bidirectional [1,2,3,5,6] and [3,4,7]. Sioux PT lines are [1,3,12,13], [2,6,8,16,17,19,20], [12,11,10,16,18] (Fig.12). Transfers connect line-specific states at the same node, with receiving-service access time plus transfer penalty. Initial boarding has access time but no transfer penalty. PT access is capacitated; MoD access uses aggregate boarding demand in BPR. All road modes share congestion. Wholesale payments are per traversed physical service link (Eq.17); MoD retail fares are distance-based. Distances follow Appendix A, not the TNTP Length column; (14,15) explicitly uses 0.8 despite its time of 5.

Report both natural projected residual (Appendix A) and step difference (Section 5.1.2): the paper describes both. Nonmonotone VI convergence is empirical; a stationary solution is not a global best-response certificate.

The node-access variant is an explicitly different aggregation rule, not the literal Section 5.1.1 statement. Small-network PT physical capacity 1,000,000 is assumed. Appendix A.1 includes PT (5,6), while the prose says PT lines span three and four nodes; this reconstruction prioritizes the table. Root refinement uses an analytic OD-fare best response only for the chosen Shannon specialization. The final report lists failed/degenerate runs and missing experiments.
