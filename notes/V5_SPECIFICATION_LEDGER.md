# V5 source-to-code specification ledger

Scope: audits the selected v4 specialization, not recovery of the authors' full settings.

| Specification | Source | Implementation / evidence | Conclusion |
|---|---|---|---|
| OD dummy root and service-mode gates | Main paper Section 2 | Model.evaluate, group graphs; 18 explicit flattened graph comparisons | Equivalent for tested common scale 1; not all possible scales |
| Exclusive service copies within trip | Section 2 | Separate non-MaaS/MaaS/driving graphs | Structurally represented |
| Destination terminal treatment | Section 3.1 | Graph destination absorption and pruning | Zero terminal cost specialization; complete original terminal specification not recovered |
| PT fare per traversed link | Eq. 27 | PT edge price attribute; link-volume revenue | Represented; do not replace with fare per first boarding |
| PT ride time in Sioux Falls | Appendix A | 1.2 times road free-flow time | Source consistent |
| Initial PT waiting time 2 | Appendix A and Section 5.1.1 | Initial gate uses 2 | Unresolved: Appendix explicitly describes PT transfers; separate initial boarding value not identified |
| Transfer access and penalty | Section 5.1.3, Appendix A | Access time plus non-MaaS penalty 8 / MaaS 0.5 | Explicitly decomposed; units remain part of specialization |
| PT capacity | Appendix A, Table A2 | Access resources and physical links | Sharing of access capacity remains uncertain; Sioux physical limit 1e6, small-network application is assumption |
| MoD access demand aggregation | Section 5.1.1 | node and aggregate variants retained | Literal source favors aggregate; proximity of node results is not validation |
| PT operator revenue | Eqs. 19-20 | Retail plus wholesale, gradient decomposition | Included; 12 finite-difference checks |
| MaaS operator revenue | Eqs. 17-18 | OD receipts minus wholesale payments | v4 accounting retained; no behavioral change |
| Perturbation function and scale | Section 3.1; supplied PUME follow-up | Shannon specialization with common scale 1 | Supported mathematical specialization; original experimental scale not recovered |
| Reported mode share and transfers | Tables 2-3 | First boarding and link counts exported separately | Paper reporting definitions not fully identified |
| Solution algorithm | Eqs. 24-25 | v4 auxiliary VI refinement retained | Not replication of original iteration trajectory or proof of global Nash equilibrium |

Sources: supplied MaaS TRC article and PUME follow-up; local extracted text in sources/. These PDFs are not redistributed. Feedback is advisory, not experimental evidence.
