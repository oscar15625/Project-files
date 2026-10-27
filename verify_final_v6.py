"""Final artifact/validation gate and portable SHA-256 evidence manifest."""
import run,json,hashlib
from pathlib import Path
import numpy as np
from campaign_v6 import cases
from src.model import Model

root=Path('results/v6'); manifest=json.loads((root/'manifest.json').read_text()); checks={}
assert set(manifest)=={c['tag'] for c in cases()}
for tag,entry in manifest.items():
    folder=root/tag; r=json.loads((folder/'metrics.json').read_text()); v=json.loads((folder/'validation.json').read_text()); y=np.load(folder/'state.npy'); m=Model(**r['config'])
    assert (folder/'COMPLETE').exists()
    # Preserve failures; never label a case successful just because it exists.
    assert entry['status']==('PASS' if v['pass'] else 'FAILED_VALIDATION')
    assert np.all(np.isfinite(y)) and np.max(y)<199.999,tag
    a=json.loads((root/'cost_audits'/tag/'summary.json').read_text())
    assert max(a['checks'].values())<1e-6 and abs(a['welfare_reconstruction_error'])<1e-6
    for k in ['profit_mod','profit_pt']: assert not v['retail_test'][k]['failed_price_evaluations']
    checks[tag]=dict(status=entry['status'],max_state=float(y.max()),cost_identity_error=max(a['checks'].values()))
hashes={}
for p in sorted(root.rglob('*')):
    if p.is_file() and p.name!='final_verification.json' and p.suffix in ['.json','.npy','.csv']:
        hashes[p.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in [Path('src/model.py'),Path('src/checkpoint.py'),Path('refine.py'),Path('audit.py'),Path('campaign_v6.py'),Path('polish_v6.py'),Path('analyze_v6.py'),Path('spec_audit_v5.py'),Path('data/SiouxFalls_net.tntp'),Path('data/SiouxFalls_trips.tntp')]: hashes[p.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in [Path('report_v6.py'),Path('REPRODUCTION_V6.md'),Path('notes/V6_METHOD_REVIEW.md'),Path('output/pdf/MaaS_reproduction_v6_final_ko.pdf')]:
    if p.exists(): hashes[p.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(cases=len(checks),passed=sum(v['status']=='PASS' for v in checks.values()),checks=checks,sha256=hashes)
(root/'final_verification.json').write_text(json.dumps(result,indent=2))
print('Artifact checks complete:',result['cases'],'cases;',result['passed'],'validated states;',len(hashes),'hashes')
