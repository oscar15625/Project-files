# Inverse-BPR boundary micro-diagnostic

Evidence: DIAGNOSTIC_ONLY. The original network and all benchmark iterates are unmodified.

For a zero-flow scalar resource, H(t)=capacity*((t/t0-1)/0.15)^(1/4). With t0=5, capacity=300, t=5.001 and gamma=1e-4, the EG predictor projects to t0. H(t0)=0, so the corrector returns to t=5.001 unchanged. The iterate difference is exactly zero while the natural residual is 0.001. This persists for five explicit updates in the micro-test. Thus small iterate change is not sufficient evidence of VI accuracy for this boundary configuration.

The inverse BPR derivative is unbounded near free flow. This example is outside the usual globally Lipschitz fixed-step EG setting; it does not refute EG convergence theorems or establish an error in the paper. The reconstruction contains destination-pruned unused congestible resources, listed separately; their presence is verified from graph resource indices. Nonzero-flow cases and network price coupling need separate diagnosis. Adaptive EG can avoid this particular stall while still failing the total budget because its common step shrinks.

Possible next tests: mathematically eliminate identically unused resources at their exact lower bound, or introduce a justified scaling/coordinate reformulation. Any such variant must be separately labeled and satisfy the same physical and economic acceptance contract; it is not silently applied to the reported original-variable benchmark.
