import run,json,csv
from pathlib import Path
import numpy as np
from scipy.special import softmax,logsumexp
from src.model import Model,Graph
from spec_audit_v5 import components,writecsv

out=Path('results/v5'); checks=[]; price_checks=[]
for folder in sorted(out.iterdir()):
    if not folder.is_dir() or not (folder/'COMPLETE').exists(): continue
    cfg=json.loads((folder/'summary.json').read_text())['config']; m=Model(**cfg); y=np.load(Path('results/v4')/folder.name/'state.npy')
    # Explicit OD-root plus three subgraphs: check the compressed implementation.
    targets={(1,13),(1,18),(4,5)} if m.name=='sioux' else {(1,5),(1,7),(3,5)}
    for ids,group in m.graphs:
        for local,idx in enumerate(ids):
            o,d,q=m.ods[idx]; o,d=int(o),int(d)
            if (o,d) not in targets: continue
            root=('root',o); terminal=('end',d); edge=[]; values=[]; flows=[]; lengths=[]
            for kind,g in group.items():
                sol=g.solve(y[:m.nt],y[-2:],m.wholesale,kind); inj=np.zeros(len(ids)); inj[local]=1
                entry=m.fixed if kind=='drive' else y[m.nt+idx] if kind=='maas' else 0
                values.append(sol[0][local]-entry); flows.append(sol[-1](inj)); lengths.append(len(g.i))
                rename=lambda s: terminal if s[0]=='end' else ((kind,s[0]),int(s[1]))
                edge.append((root,rename(('gate',o)),-1,entry,0,0,0,0,0))
                c=components(m,g,y,kind).sum(axis=1)
                edge.extend((rename(s),rename(t),-1,c[e],0,0,0,0,0) for e,(s,t) in enumerate(g.edge_labels))
            full=Graph(edge,[root],d,m.theta); sol=full.solve(np.array([]),np.zeros(2),np.zeros(2),'drive'); f=sol[-1](np.array([1.]))
            probabilities=softmax(np.array(values)/m.theta); expected=[]
            for prob,flow in zip(probabilities,flows): expected.extend([prob,*list(prob*flow)])
            verr=abs(sol[0][0]-m.theta*logsumexp(np.array(values)/m.theta)); ferr=float(np.max(abs(f-np.array(expected))))
            assert max(verr,ferr)<1e-9
            checks.append(dict(run=folder.name,origin=o,destination=d,value_error=verr,edge_flow_error=ferr))
    paper_price=(2.42 if m.maas else 3.65) if m.name=='sioux' else (1.44 if m.maas else 1.38)
    for p in [float(y[-1]),paper_price]:
        z=y.copy(); z[-1]=p; h,r=m.evaluate(z); B=m.retail_volume[1]; eps=1e-5
        zp=z.copy(); zm=z.copy(); zp[-1]+=eps; zm[-1]-=eps
        rp=m.evaluate(zp)[1]; Bp=m.retail_volume[1]; rm=m.evaluate(zm)[1]; Bm=m.retail_volume[1]
        dB=(Bp-Bm)/(2*eps); dW=(rp['wholesale_pt']-rm['wholesale_pt'])/(2*eps); decomp=B+p*dB+dW
        assert abs(decomp+h[-1])<1e-3
        price_checks.append(dict(run=folder.name,price=p,pt_links=B,first_pt=r['share_non_pt']*m.total/100,direct_price_effect=B,retail_demand_effect=p*dB,wholesale_effect=dW,gradient=-h[-1],reconstructed_gradient=decomp,elasticity=p*dB/B,profit=r['profit_pt']))
writecsv(out/'explicit_root_checks.csv',checks); writecsv(out/'pt_gradient_decomposition.csv',price_checks)
# Independently hand-specified free-flow pure-PT witness, without model edge traversal.
folder=out/'sioux_node_node_total0_without'; s=json.loads((folder/'summary.json').read_text()); p=s['baseline']['price_pt']
paths=list(csv.DictReader((folder/'pure_pt_paths.csv').open(encoding='utf-8-sig')))
manual={(1,3):2+4*1.2+p,(1,13):2+(4+4+3)*1.2+3*p,(1,18):2+(4+4+6+5+4+3)*1.2+2+8+6*p}
for row in paths:
    key=int(row['origin']),int(row['destination'])
    if key in manual: assert abs(float(row['cost'])-manual[key])<1e-9
    else: assert row['available']=='False'
result=dict(explicit_root_cases=len(checks),max_root_value_error=max(r['value_error'] for r in checks),max_root_flow_error=max(r['edge_flow_error'] for r in checks),price_gradient_cases=len(price_checks),max_price_gradient_error=max(abs(r['gradient']-r['reconstructed_gradient']) for r in price_checks),manual_path_costs={str(k):v for k,v in manual.items()})
(out/'independent_checks.json').write_text(json.dumps(result,indent=2)); print(result)
