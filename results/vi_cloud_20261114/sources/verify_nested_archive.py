"""READ-ONLY archive integrity and saved-state replay (no new optimization)."""
import os
for var in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[var]='1'
import json, pathlib,hashlib,numpy as np
from nested_extension import NestedModel
from nested_solver import residual
ROOT=pathlib.Path(__file__).resolve().parent
BASE=ROOT.parent/'base'
MAN=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text())
errors=[]
for item in MAN['files']:
 path=ROOT/item['path'];h=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
 if h!=item['sha256']:errors.append(item['path'])
assert not errors,'Archive file hashes differ: '+repr(errors)
checks=[]
for folder in sorted((ROOT/'audited').glob('*_lambda*')):
 if not (folder/'audit.json').exists():continue
 r=json.loads((folder/'audit.json').read_text())
 c=json.loads((ROOT/'experiments'/r['case']/'config.json').read_text());c.pop('source_reference')
 m=NestedModel(**c);y=np.load(folder/'state.npy',allow_pickle=False);x=np.load(folder/'coordinates.npy',allow_pickle=False)
 h,v=m.evaluate(y,details=True)
 r_scaled=float(np.linalg.norm(residual(m,x)))
 h[:m.nt][m.congest]=m.cap[m.congest]*np.maximum(x[:m.nt][m.congest],0)-m.last_flows[m.congest]
 nr=float(np.linalg.norm(y-m.project(y-1e-4*h)))
 met_error=max(abs(v[k]-r[k]) for k in v if k in r and isinstance(r[k],(int,float)))
 ok=r['valid_pass'] and r_scaled<1e-6 and nr<1e-6 and met_error<1e-5
 checks.append((r['case'],ok,r_scaled,nr,met_error))
assert len(checks)==10 and all(x[1] for x in checks),checks
print(json.dumps({'status':'PASS_SAVED_STATES','verified_files':len(MAN['files']),'cases':len(checks),'max_scaled_residual':max(x[2] for x in checks),'max_aux_natural_residual':max(x[3] for x in checks),'max_economic_replay_error':max(x[4] for x in checks)},indent=2))
