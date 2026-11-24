# PT tariff full-network local extension — 2026-11-24

Read REPORT_KR.md, REPORT_EN.md, summary.csv, paired_comparison.csv and VALIDATION_SUMMARY.json. Four primary cases + eight multistarts are complete. The original Small package is a separate input; six saved Small states were replayed.

Extract the ZIP to a short path, e.g. C:/maas/pt24 or ~/pt24. Use Python3.12 and requirements.txt. Run `python verify.py` for read-only saved-state/manifest verification. Redirect output outside the release folder. Linux-compatible code is supplied; this run was tested on Windows only.

`python campaign.py` is the bounded resume entry point, skips COMPLETE cases, and does no new solve when all12 are complete. Do not remove COMPLETE to force a restart. Use a fresh output branch/directory for new research. `python extension.py` and `python structure_audit.py` are audit builders; they write audit outputs, unlike verify.py.

src/model.py and data files are pinned to Git commit b682637921d843bc2edac8f154b5d03f21fa257a. Protocol: aggregate MoD access, node-specific PT access, full528OD, no demand scaling. Small's node/node settings are distinct. No full-network zones are simulated without an explicit zone map. All amounts are model units. The original paper's Table3 is not numerically reproduced here.

results/*/ contains state.npy, coordinates.npy, metrics.json, trace.json, protocol.json, COMPLETE.json and best checkpoints. COMPLETE means the attempt ended; consult its status rather than assuming PASS. The supplied Small logs are retained separately under input/. requirements.txt describes the tested environment, not empirical calibration.
