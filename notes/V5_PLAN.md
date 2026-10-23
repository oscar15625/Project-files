# V5: structural specification audit

User resumed 2026-10-23, Asia/Seoul. No author contact. No automatic recovery booking: if disconnected, preserve files and wait for the user's renewed instruction. Work branch: codex/maas-v5-spec-audit, derived from v4 commit 71176e5. The v4 tag remains unchanged.

Scope from supplied V4_Feedback.pdf: independently verify feedback claims; map source equations to implementation and unresolved assumptions; trace representative OD costs; inspect PT price incentives before considering calibration. Source PDF stays ignored/local.

1. Add read-only graph edge labels. Verify unchanged benchmark evaluations against stored v4 metrics.
2. Export conditional unit-flow cost decomposition for every OD: road/PT ride, initial access, transfer access, capacity shadow delay, penalties, fare and driving charges. Reconstruct value with expected entropy and check identity.
3. Export explicit minimum-cost pure-PT path edge ledgers for direct, transfer and unavailable OD classes. These are diagnostic paths, not a replacement for stochastic assignment.
4. At fixed other-leader decisions, profile PT retail revenue and derivatives, including the paper's price 3.65. Distinguish link usage from first-boarder count; report capacity utilization and shadow waiting.
5. Only change behavior/constraints if a concrete source discrepancy is identified. Otherwise report unresolved specification faithfully rather than tune toward a target.
6. Produce Korean PDF/Markdown, CSV/JSON evidence, versioned GitHub and local bundle backups. Record exact next action in notes/RESUME.md after milestones.
