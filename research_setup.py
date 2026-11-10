"""Seal V5 and run its legacy checks in a disposable copy, never in baseline."""
import os,sys,json,hashlib,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent; os.chdir(ROOT)
sys.path.insert(0,str(ROOT.parents[1]/'.vendor'))
import run
import numpy as np
from src.model import Model
OUT=ROOT/'results/research_v6/G00'; OUT.mkdir(parents=True,exist_ok=True)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[ROOT/'src/model.py']+[p for d in ['results/v4','results/v5'] for p in (ROOT/d).rglob('*') if p.is_file()]
before={str(p.relative_to(ROOT)):digest(p) for p in protected}
(OUT/'protected_hashes.json').write_text(json.dumps(before,indent=2))
registry=[]
for path in sorted((ROOT/'results/v5').glob('*/summary.json')):
    old=json.loads(path.read_text()); tag=path.parent.name; m=Model(**old['config']); y=np.load(ROOT/'results/v4'/tag/'state.npy')
    h,current=m.evaluate(y); err=max(abs(current[k]-old['baseline'][k]) for k in current)
    assert err<1e-6
    registry.append(dict(id=tag,config=old['config'],metrics=current,max_difference=err,state_hash=digest(ROOT/'results/v4'/tag/'state.npy')))
assert len(registry)==6
(OUT/'baseline_registry.json').write_text(json.dumps(registry,indent=2))
sandbox=ROOT/'tmp/research_g00_legacy'; sandbox.mkdir(parents=True,exist_ok=True)
for p in ROOT.glob('*.py'): shutil.copy2(p,sandbox/p.name)
for name in ['src','data']: shutil.copytree(ROOT/name,sandbox/name,dirs_exist_ok=True)
for name in ['v4','v5','small_node_theta1_without']: shutil.copytree(ROOT/'results'/name,sandbox/'results'/name,dirs_exist_ok=True)
env=os.environ.copy(); env['PYTHONPATH']=str(ROOT.parents[1]/'.vendor')
tests=[]
for name in ['validate_v4.py','verify_spec_v5.py','verify_manifest_v4.py']:
    tick=time.perf_counter()
    with (OUT/(name+'.log')).open('w',encoding='utf-8') as log:
        result=subprocess.run([sys.executable,name],cwd=sandbox,env=env,stdout=log,stderr=subprocess.STDOUT)
    tests.append(dict(script=name,exit_code=result.returncode,seconds=time.perf_counter()-tick))
    print(name,result.returncode,flush=True)
    (OUT/'legacy_checks.json').write_text(json.dumps(tests,indent=2))
unchanged=all(digest(ROOT/k)==v for k,v in before.items())
status=dict(status='PASS' if unchanged and all(t['exit_code']==0 for t in tests) else 'FAILED_BASELINE',baseline_count=len(registry),protected_files=len(before),unchanged=unchanged,checks=tests)
(OUT/'status.json').write_text(json.dumps(status,indent=2)); print(status)
