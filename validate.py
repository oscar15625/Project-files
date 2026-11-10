import run
import numpy as np
import json
from pathlib import Path
from src.model import Model, Graph

def validate():
    report={}
    edges=[(('gate',1),('end',2),-1,1.,0,0,0,0,0),(('gate',1),('end',2),-1,2.,0,0,0,0,0)]
    graph=Graph(edges,[('gate',1)],2,1.)
    value,_,_,_,load=graph.solve(np.array([]),np.array([0.,0.]),np.array([0.,0.]),'drive')
    exact=np.exp(-np.array([1.,2.])); exact/=exact.sum()
    assert np.max(np.abs(load(np.array([100.]))-100*exact))<1e-12
    assert abs(value[0]-np.log(np.exp(-1)+np.exp(-2)))<1e-12
    report['independent_two_route_check']='passed'
    for name in ['small','sioux']:
        m=Model(name,True); y=m.initial(); h,metrics=m.evaluate(y)
        errs=[]
        for idx,key in [(-2,'profit_mod'),(-1,'profit_pt'),(m.nt,'profit_maas')]:
            eps=1e-5; a=y.copy(); b=y.copy(); a[idx]+=eps; b[idx]-=eps
            fd=(m.evaluate(a)[1][key]-m.evaluate(b)[1][key])/(2*eps)
            errs.append(abs(fd+h[idx])/max(1,abs(fd)))
        assert max(errs)<1e-6,(name,errs)
        assert metrics['flow_conservation_error']<1e-7,metrics
        assert abs(sum(metrics[k] for k in ['share_non','share_drive','share_maas'])-100)<1e-10
        report[name]={'gradient_relative_errors':errs,'flow_conservation_error':metrics['flow_conservation_error'],'demand':m.total,'road_links':len(m.rows),'od_pairs':m.nod}
    Path('results/validation.json').write_text(json.dumps(report,indent=2,default=float)); print(report)
if __name__=='__main__': validate()
