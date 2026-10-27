# EPFL group meeting: methodological review notes

Meeting: 2026-12-03. Prepared as a reproduction-based review, not a claim to have recovered the authors' code or to have developed a new solution theorem.

## 1. Explain the problem before the algorithm

Travelers choose both a service regime (non-MaaS, driving, MaaS) and a route. The MaaS platform chooses an OD fare and pays operators for utilized capacity. Operators choose retail prices while receiving wholesale payments from MaaS. A wholesale price is an exogenous negotiated parameter here, not an endogenous bargaining solution. The economically relevant response is substitution between retail and MaaS use, alongside congestion and transfer costs.

The main paper uses a virtual traffic operator to express traffic supply consistency jointly with price optimality. This avoids solving a complete congested traffic equilibrium inside every operator objective evaluation. It does not eliminate the traveler loading and sensitivity calculations.

## 2. Traveler problem: the specialization actually implemented

For the implemented Shannon specialization, transient-state values obey

`V_i = theta * log(sum_(i,j) exp((-C_ij + V_j)/theta))`, with destination value zero.

The transition probability is `P_ij = exp((-C_ij + V_j - V_i)/theta)`. Expected visits and link flows follow from an absorbing Markov system. The implementation uses sparse linear solves and an exact shortest-distance potential transformation to improve numerical conditioning. It does not truncate routes to shortest paths. Proper absorption is essential; sparse factorization alone does not make an improper recursive choice model valid.

At the root, the three service regimes use a logsum with a separately configurable mode scale. This campaign fixes both scales at 1. That is a selected behavioral specification, not an estimate or a recovered author setting. Default V5 outputs are regression-tested unchanged.

The demand derivative includes route reallocation and service-regime substitution. For example, the derivative of a non-MaaS value with respect to the PT per-link fare equals minus the expected number of paid PT links. A reduction in first-boarding PT share is not interchangeable with a reduction in paid link volume.

## 3. What the VI means

Let `y=(t,p,r)` collect resource times, MaaS OD fares and operator retail prices. The map is

`H(y) = (supply(t)-flow(y), -gradient_p profit_MaaS(y), -gradient_r profit_operators(y))`.

The VI seeks `H(y*) dot (y-y*) >= 0` for all feasible y. For a lower-bounded scalar, interior optimality means the corresponding H component is zero; at its lower bound it may be positive. For a PT resource, capacity slack is paired with zero excess delay, while a binding resource may have positive shadow delay. For BPR roads, time and flow must satisfy the supply relation.

The paper's existence argument uses continuity on a compact convex set. Existence does not imply uniqueness or convergence from every start. The paper explicitly notes general nonmonotonicity. Numerical residuals and a tested price-deviation search support a candidate; they do not certify a global Nash equilibrium over every possible strategy.

## 4. Partial versus total derivatives is a key review point

The implemented PT first-order condition is evaluated at fixed virtual-operator time decisions, other operators' prices and MaaS fares:

`d Profit_PT / d r_PT = B + r_PT * dB/dr_PT + c_PT * dW/dr_PT`,

where B is retail paid-PT-link flow and W is MaaS PT-link flow. The final term can be positive because a retail price increase shifts demand to MaaS. Omitting it changes the game.

This is the partial derivative of the single-level game. A counterfactual retail price change followed by a full congestion re-equilibrium computes a different response and is not the same deviation test. Report this distinction explicitly when discussing the auxiliary numerical validation.

Similarly, the entry comparison is

`Delta Profit_PT = (Retail_after - Retail_before) + Wholesale_after`.

That is an accounting identity across two solved states, not a claim that wholesale revenue causally changes while everything else remains fixed. Raising the wholesale price requires re-solving all interacting decisions.

## 5. Solver and validation: claim only what was tested

The paper's extragradient algorithm uses a projected prediction and correction, requiring two H evaluations per iteration. Its convergence guarantee under monotonicity assumptions does not automatically extend to this nonmonotone game. The reproduction retains that implementation but uses auxiliary flow-coordinate root/least-squares refinement for the reported final states; it does not reproduce Algorithm 1's trajectory or iteration counts.

The current specialization allows exact conditional optimization of separable MaaS OD fares using the Wright omega function. This reduces the root dimension. It relies on the selected root logit form, fixed OD demand and the absence of additional coupling constraints; it need not survive latent classes, budget constraints or a different perturbation.

V6 checks: default regression; distinct initial and transfer waiting costs; conservation; resource complementarity; scaled and natural VI residuals; operator price grid plus local refinement; MaaS exact conditional fare response and sampled finite-difference gradients; all-OD cost/entropy reconstruction. Grid-based deviations and a single perturbed warm start do not prove global uniqueness. Preserve failures and configurations.

## 6. Demand expert's contribution and limitations

Fixed OD trip totals imply that additional PT use is a reallocation of existing demand, not induced total travel. First boarding, any PT use, paid PT links and transfers measure different things. Network segmentation affects a per-link fare and must be preserved or normalized carefully in large-network applications.

Aggregate expected utility is not an observed welfare measure or proof that every traveler benefits. Compare OD-specific expected utility and demand exposed to losses, in addition to the sum. Within-OD heterogeneity remains unmodeled even if all OD averages improve. Percentage changes in negative welfare levels require an explicit denominator; the report uses absolute gains or the magnitude of baseline welfare.

A natural next research design is to hold network, supply and total OD demand fixed, introduce transfer-aversion classes with a controlled mean, and examine whether the operator-and-traveler improvement conditions shift across wholesale prices. This is proposed future work, not a V6 result. The original paper already studies OD-specific VOT; merely adding heterogeneity is not automatically novel. Distributional benefit, thresholds and equilibrium robustness would be the questions.

## 7. Large-network implications that can be defended

Destination grouping shares a sparse factorization across origins when downstream costs and preferences are identical. More OD pairs then add loading/aggregation work without necessarily multiplying factorizations. New preference classes can require additional value systems. Destination-specific networks, transit line states and transfer edges can expand memory substantially; sparse LU fill-in must be measured rather than inferred from road-link count.

Analytical sparse solves for sensitivity avoid one full finite difference per fare. Do not form a dense link-by-link Jacobian if only directional products are required. BPR flow coordinates avoid cancellation near free-flow time. Reuse graph structure, monitor conditioning, separate lower-level accuracy from VI accuracy, and checkpoint each accepted solver step.

V6 reports local H-evaluation and solver timings on two networks, with warm starts and one requested BLAS thread. These observations identify workload and implementation choices; they do not establish asymptotic complexity, parallel speedup or performance on a metropolitan network. The fixed price/time upper box of 200 is an implementation assumption and should be checked for active bounds.

## 8. Suggested review narrative and honest conclusion

1. Economic question and strategic actors.
2. PUMCM choice/loading and why its sensitivities matter.
3. Virtual operator and VI: existence versus algorithmic convergence.
4. Independent implementation, checks, and the exact reproduction boundary.
5. Retail cannibalization versus wholesale compensation; conditional benefit results.
6. Demand heterogeneity and computational scaling as next research questions.

Useful English formulation: "The independent implementation reproduces a conditional mechanism, rather than the published numerical equilibrium. I distinguish fixed-time VI optimality from re-equilibrated price responses, and operator gains from aggregate and distributional traveler benefits."

## Sources

Main article supplied by the user: Yao, Ma and Zhang, Transportation Research Part C 188 (2026), 105703, https://doi.org/10.1016/j.trc.2026.105703. In particular Sections 3-4, Table 2, Table 3 and Section 5.1.4. The user's supplied PUMCM abstract and PUME follow-up support the choice-model investigation but do not recover the MaaS experiment's unreported settings. Local source-to-code limitations remain in notes/V5_SPECIFICATION_LEDGER.md. The meeting motivation is user context and is not included in scientific claims.
