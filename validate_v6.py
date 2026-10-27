"""Check default regression and distinct initial/transfer PT cost semantics."""
import run, json
from pathlib import Path
import numpy as np
from src.model import Model
from spec_audit_v5 import components

out={}
for name in ['sioux','small']:
    for maas in [False,True]:
        tag=f'{name}_node_node_total0_'+('with' if maas else 'without')
        folder=Path('results/v4')/tag; r=json.loads((folder/'metrics.json').read_text()); y=np.load(folder/'state.npy'); base=Model(**r['config'])
        _,now=base.evaluate(y); err=max(abs(now[k]-r[k]) for k in now); assert err<1e-6
        out[tag]=err
        for field in ['initial_pt_wait','transfer_pt_wait']:
            altered=Model(**dict(r['config'],**{field:1}))
            for (_,bg),(_,ag) in zip(base.graphs,altered.graphs):
                for kind in bg:
                    b,a=bg[kind],ag[kind]
                    for idx,(s,d) in enumerate(a.edge_labels):
                        expected=-1 if isinstance(d[0],int) and ((s[0]=='gate') if field=='initial_pt_wait' else bool(a.attr[idx,6])) else 0
                        assert abs(a.attr[idx,1]-b.attr[idx,1]-expected)<1e-12
                    cost=components(altered,a,y,kind).sum(axis=1)
                    manual=a.attr[:,1].copy(); mask=a.res>=0; manual[mask]+=y[a.res[mask]]
                    if kind=='non': manual+=a.attr[:,2:4]@y[-2:]
                    assert np.max(abs(cost-manual))<1e-12
Path('results/v6').mkdir(exist_ok=True)
Path('results/v6/default_regression.json').write_text(json.dumps(out,indent=2))
print('PASS: default outputs unchanged and PT initial/transfer offsets isolated')
