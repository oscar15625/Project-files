# M03 comparability contract

Evidence class: DIAGNOSTIC_ONLY. Two prototypes solve the same original fixed-time partial-derivative price residual. JOINT_AUX solves the full traffic-ratio/fare/retail system; NESTED_SAME_VI solves physical traffic inside each outer residual evaluation. Both start from contract (1.5,1.5) reference times with all prices increased 3%. Neither is the original EG algorithm.

The outer numerical Jacobian may differentiate a composed residual to find its zero. This does not turn the leader objective into profit(t*(p),p). A leader optimizing that composed profit would use total strategic derivatives and can define a different game: NOT_COMPARABLE with the original VI without further argument. This is why M02 gains are not automatic Nash violations.

Acceptance requires full VI/physical residuals and inherited finite price-deviation audits, not least_squares.success alone. The complete prototype records inner failures, every H call (including numerical Jacobian and validation) and graph solves. Timings include instrumentation and validation. One warm-start small case cannot establish universal VTO superiority or large-network speedup. PG/EG comparisons remain M01 and are not substituted for this comparison.
