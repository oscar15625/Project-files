# MaaS Research v7.1 shared evidence

Start with [recovery status](RECOVERY_STATUS_V7_1.md), [Korean report](results/research_v7_1/Detailed_Review_KR.md), [English report](results/research_v7_1/Technical_Report_EN.md), and [cloud execution guide](CLOUD_README.md).

Download [Small execution ZIP](distribution/MaaS_v7_1_Small_Cloud.zip), or run `python cloud_replay.py` after installing `requirements-cloud.txt`. Default replay performs no optimization. The branch is a sanitized snapshot with independent Git ancestry: historical local commits, original PDFs, private requests, full operator event streams and large checkpoint histories are not published. Original local history remains backed up. Representative states are byte-preserved; text metadata has local-user paths/BOMs normalized. EXPORT_FILE_INVENTORY.csv gives original and shared hashes; SHARED_MANIFEST.json is authoritative for the shared bytes. Original protected hashes describe the full local archive, not completeness of this subset.

Raw per-H events and complete checkpoints are retained in the local recovery ZIP. The portable replay has its own manifest and does not require the author's PDF, original Windows directories, or historical Git tags. The independent reconstruction is not the authors' implementation. The nested experiment remains interrupted and no failed run is relabeled PASS.
