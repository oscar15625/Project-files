"""Atomic state snapshots plus append-only lifecycle events."""
import json,os,time,subprocess
from pathlib import Path
import numpy as np

def save(folder,x,config,iteration,residual,status='running'):
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    payload=dict(config=config,iteration=iteration,residual=float(residual),status=status,pid=os.getpid(),timestamp=time.time())
    try: payload['commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    except Exception: payload['commit']='unknown'
    snapshots=folder/'checkpoints'; snapshots.mkdir(exist_ok=True)
    generation=f'{time.time_ns()}-{os.getpid()}'
    temp=snapshots/(generation+'.tmp.npz'); target=snapshots/(generation+'.npz')
    np.savez(temp,x=x,metadata=json.dumps(payload)); os.replace(temp,target)
    with (folder/'events.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(payload)+'\n'); f.flush()

def load(folder,config):
    paths=sorted((Path(folder)/'checkpoints').glob('*.npz'))
    paths=[p for p in paths if not p.name.endswith('.tmp.npz')]
    target=paths[-1] if paths else Path(folder)/'checkpoint.npz'
    with np.load(target) as snap:
        meta=json.loads(str(snap['metadata']))
        if meta['config']!=config: raise ValueError('Checkpoint model configuration differs')
        return snap['x'].copy(),meta
