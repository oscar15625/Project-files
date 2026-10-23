# V5 resume checkpoint

Status: COMPLETE_V5_AUDIT_QUANTITATIVE_REPLICATION_INCOMPLETE. Date: 2026-10-23 (Asia/Seoul).

All six audit cases and independent verification are complete. All audit/check processes finished. No automatic reconnect is scheduled; wait for the user's instruction following connection recovery.

Branch: codex/maas-v5-spec-audit. Final tag: maas-reproduction-v5. Previous v4 tag remains unchanged. Final local backup: backups/maas-reproduction-v5.bundle.

Read REPRODUCTION_V5.md, notes/V5_SPECIFICATION_LEDGER.md and results/v5/independent_checks.json. PDF: output/pdf/MaaS_reproduction_v5_ko.pdf. Results include 5,295 OD-mode rows, six resource/path/price ledgers, 18 explicit graph checks and 12 gradient decompositions. All source PDFs remain local and ignored.

No behavioral settings changed. Read-only edge labels added to src/model.py. spec_audit_v5.py skips completed cases via COMPLETE markers; verify_spec_v5.py repeats independent checks; report_v5.py creates the report without running experiments.

Next research: identify source-backed initial PT access waiting and shared-capacity definitions, perturbation settings and reporting definitions. Test only explicit, documented candidate settings before rerunning leader optimization. Do not call closer individual metrics a recovered original specification. Do not contact authors. Preserve previous failed trials and baseline v4 results.
