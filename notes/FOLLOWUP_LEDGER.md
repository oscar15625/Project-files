# Evidence added for revision 4

User supplied: Yao & Zhang, *Perturbed utility Markovian traffic equilibrium: theory and computation*, arXiv:2607.09568v1, 10 July 2026, 49 PDF pages. Public abstract: https://arxiv.org/abs/2607.09568 . The supplied PDF remains local, excluded from GitHub.

* Section 6.1, equations (37)-(40), PDF page 20: negative Shannon entropy with **state-specific** positive scale mu_s yields log-sum-exp surplus and softmax choice. This supports distinct root mode and downstream route scales as a legitimate sensitivity model. It does **not** identify the scales actually used in the TRC MaaS experiment.
* Section 6.1, PDF page 21: alpha>1 permits sparse choices. The original MaaS smoothness assumption and analytic sensitivity cannot simply be carried over to sparsemax. We retain the smooth Shannon specialization and disclose that choice.
* Appendix E.1, PDF page 47: the follow-up's logit example uses scale 1 and its nested recursive logit draws state scales in [0.5,2]. These are different experiments, not recovered MaaS settings.
* Absorbing-state and finite-value requirements motivate checking Bellman solvability and flow conservation. We use an exact potential transformation of the linearized Shannon Bellman equation: w_ij = exp((-c_ij - D_j + D_i)/theta), V_i=-D_i+theta log(z_i). D is a shortest-path potential, not a restriction to shortest routes. All graph edges remain in the Markov loading.

Verified numerical evidence in results/v4/validation.json: old/new Bellman and gradient outputs agree within 8.8e-11 on the two networks; selected price finite differences at scales down to .01 agree within 4.5e-9 relative/absolute normalized error; accounting and terminal balance pass. These initial-state derivatives include near-zero demand branches, so equilibrium deviation checks remain necessary.

Conditional accounting diagnostic from the critique: under the implemented root logit, an interior independent OD fare obeys margin=mode_theta/(1-share). Consequently platform profit >= mode_theta times platform demand. The paper's 5658 profit and 39.5% of 432720 trips imply mode_theta<=0.0331 under these assumptions. This is a necessary condition, not an estimate or proof that the paper uses logit or those units. Low scales are therefore tested as hypotheses, without changing the public target values.

Capacity interpretation is tested independently for MoD and PT. Node or line-node PT capacities are either per resource or divided to preserve total network capacity. Changes in resource count are reported with total capacity and boarding flows; they must not be described as innocuous graph refactoring.

Restart verification: a forced interruption after two accepted iterations, then reconstruction from a disk snapshot, agrees with uninterrupted optimization to 3.4e-12 in state. Snapshots are immutable generation files, atomically renamed from temporary files, avoiding Windows replacement/reader locking. Solver iteration state is restarted, not serialized; the test verifies equilibrium recovery, not identical optimizer trajectory.
