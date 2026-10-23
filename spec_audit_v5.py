"""Read-only cost/state/price audit of validated v4 equilibria."""
import run
import csv,json,heapq,time
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
from src.model import Model

OUT=Path('results/v5'); OUT.mkdir(parents=True,exist_ok=True)
FIELDS=['road_time','pt_ride_base','pt_ride_shadow','initial_access_base','initial_mod_delay','initial_pt_shadow','transfer_access_base','transfer_mod_delay','transfer_pt_shadow','transfer_penalty','retail_mod','retail_pt','driving_variable']
def writecsv(path,rows):
    if not rows: return
    temp=path.with_suffix('.tmp');
    with temp.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,list(rows[0])); w.writeheader(); w.writerows(rows)
    temp.replace(path)

def components(m,g,y,kind):
    a=g.attr; c=np.zeros((len(a),len(FIELDS))); t=y[:m.nt]
    for e,((s,d),r) in enumerate(zip(g.edge_labels,g.res)):
        if r>=0:
            if s[0]=='M' and d[0]=='M': c[e,0]=t[r]
            elif isinstance(s[0],int) and s[0]==d[0]: c[e,1:3]=[m.t0[r],t[r]-m.t0[r]]
            else:
                initial=s[0]=='gate'; c[e,3 if initial else 6]=m.t0[r]
                c[e,(4 if d[0]=='M' else 5) if initial else (7 if d[0]=='M' else 8)]=t[r]-m.t0[r]
        c[e,9 if a[e,6] else 12]=a[e,1]
    if kind=='non': c[:,10:12]=a[:,2:4]*y[-2:]
    return c

def pure_path(g,c,local):
    start=int(g.gates[local]); queue=[(0.,start,())]; best={start:0.}
    edges={}
    for e,(s,d) in enumerate(g.edge_labels):
        if s[0]!='M' and d[0]!='M': edges.setdefault(int(g.i[e]),[]).append(e)
    while queue:
        cost,n,path=heapq.heappop(queue)
        if n==g.n: return path
        if cost>best[n]+1e-12: continue
        for e in edges.get(n,[]):
            j=int(g.j[e]); cand=cost+c[e].sum()
            if cand<best.get(j,float('inf')):
                best[j]=cand; heapq.heappush(queue,(cand,j,path+(e,)))
    return None

def audit(tag):
    out=OUT/tag; out.mkdir(exist_ok=True)
    src=Path('results/v4')/tag; original=json.loads((src/'metrics.json').read_text()); y=np.load(src/'state.npy'); m=Model(**original['config'])
    H,current=m.evaluate(y); err=max(abs(current[k]-original[k]) for k in current)
    assert err<1e-6,(tag,err)
    resource_flow=m.last_flows.copy(); records=[]; paths=[]; edges=[]; maxima={'regression':err,'value_identity':0.,'root_identity':0.,'load_balance':0.}
    aggregate=np.zeros(len(FIELDS)); entry_total=0.; entropy_total=0.
    selected={(1,13),(1,18),(4,5),(1,3)} if m.name=='sioux' else {(1,5),(1,7),(3,5)}
    for ids,group in m.graphs:
        kinds=list(group); solved=[g.solve(y[:m.nt],y[-2:],m.wholesale,k) for k,g in group.items()]
        entries=np.array([np.full(len(ids),m.fixed) if k=='drive' else y[m.nt+ids] if k=='maas' else np.zeros(len(ids)) for k in kinds]).T
        values=np.array([s[0] for s in solved]).T-entries; lv=logsumexp(values/m.mode_theta,axis=1); shares=np.exp(values/m.mode_theta-lv[:,None])
        for local,idx in enumerate(ids):
            o,d,q=m.ods[idx]; root_entropy=-m.mode_theta*np.sum(shares[local]*np.log(np.maximum(shares[local],1e-300)))
            reconstructed=0.
            for b,(kind,g) in enumerate(group.items()):
                V,R,dV,dR,load=solved[b]; inject=np.zeros(len(ids)); inject[local]=1; flow=load(inject); c=components(m,g,y,kind); parts=flow@c
                visits=np.bincount(g.i,weights=flow,minlength=g.n); valid=(flow>1e-200)&(visits[g.i]>0)
                entropy=-m.theta*np.sum(flow[valid]*np.log(flow[valid]/visits[g.i[valid]]))
                cost=float(parts.sum()+entries[local,b]); reconstructed+=shares[local,b]*(-cost+entropy)
                identity=abs(V[local]+parts.sum()-entropy); maxima['value_identity']=max(maxima['value_identity'],float(identity))
                maxima['load_balance']=max(maxima['load_balance'],abs(float(flow[~g.internal].sum()-1)))
                row=dict(origin=int(o),destination=int(d),demand=q,kind=kind,mode_share=shares[local,b],**dict(zip(FIELDS,parts)),entry_charge=entries[local,b],expected_cost=cost,route_entropy=entropy,value=V[local]-entries[local,b],pt_link_count=float(flow@g.attr[:,3]),first_pt_probability=float(flow[g.board_pt].sum()),transfer_count=float(flow@g.attr[:,6]),wholesale_mod=float(R[local,0]) if kind=='maas' else 0.,wholesale_pt=float(R[local,1]) if kind=='maas' else 0.)
                records.append(row); weight=q*shares[local,b]; aggregate+=weight*parts; entry_total+=weight*entries[local,b]; entropy_total+=weight*entropy
                if (int(o),int(d)) in selected and kind!='drive':
                    path=pure_path(g,c,local)
                    paths.append(dict(origin=int(o),destination=int(d),kind=kind,available=path is not None,path=' -> '.join(str(g.edge_labels[e][0]) for e in path)+f' -> end({int(d)})' if path is not None else '',cost=float(c[list(path)].sum()+entries[local,b]) if path is not None else None,entry_charge=float(entries[local,b]),**dict(zip(FIELDS,c[list(path)].sum(axis=0) if path is not None else np.zeros(len(FIELDS))))))
                    if path is not None:
                        for step,e in enumerate(path): edges.append(dict(origin=int(o),destination=int(d),kind=kind,step=step,source=str(g.edge_labels[e][0]),target=str(g.edge_labels[e][1]),resource=int(g.res[e]),**dict(zip(FIELDS,c[e])),edge_cost=float(c[e].sum())))
            maxima['root_identity']=max(maxima['root_identity'],abs(reconstructed+root_entropy-m.mode_theta*lv[local]))
            entropy_total+=q*root_entropy
    assert max(maxima.values())<1e-6,maxima
    welfare_reconstructed=-aggregate.sum()-entry_total+entropy_total
    assert abs(welfare_reconstructed-current['traveler_welfare'])<1e-6
    resource=[]
    for i in range(m.nt):
        label='road' if i<len(m.rows) else 'pt_ride' if i<m.accessM else 'mod_access' if i in m.mod_resources else 'pt_access' if i in m.pt_resources else 'unused_access'
        resource.append(dict(resource=i,type=label,capacity=m.cap[i],flow=resource_flow[i],utilization=resource_flow[i]/m.cap[i],base_time=m.t0[i],time=y[i],delay=y[i]-m.t0[i],congestible=bool(m.congest[i])))
    writecsv(out/'od_costs.csv',records); writecsv(out/'pure_pt_paths.csv',paths); writecsv(out/'path_edges.csv',edges); writecsv(out/'resources.csv',resource)
    summary=dict(source_run=tag,config=m.config(),checks=maxima,welfare_reconstruction_error=float(welfare_reconstructed-current['traveler_welfare']),total_components=dict(zip(FIELDS,aggregate)),entry_total=entry_total,entropy_total=entropy_total,baseline=current)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)); print(tag,maxima,flush=True)
    profile=[]
    for price in np.unique(np.r_[np.linspace(0,6,61),y[-1],3.65 if m.name=='sioux' else 1.38]):
        z=y.copy(); z[-1]=price; h,r=m.evaluate(z); volume=m.retail_volume[1]
        eps=1e-5; zp=z.copy(); zm=z.copy(); zp[-1]+=eps; zm[-1]-=eps
        # No clipping here: tiny negative diagnostic perturbation is avoided at zero.
        if price>eps:
            fd=(m.evaluate(zp)[1]['profit_pt']-m.evaluate(zm)[1]['profit_pt'])/(2*eps)
        else: fd=(m.evaluate(zp)[1]['profit_pt']-r['profit_pt'])/eps
        profile.append(dict(price=price,revenue=r['profit_pt'],retail_revenue=r['retail_pt'],wholesale_revenue=r['wholesale_pt'],pt_link_volume=volume,first_pt_trips=r['share_non_pt']*m.total/100,gradient=-h[-1],finite_difference=fd,gradient_error=abs(fd+h[-1]),driving_share=r['share_drive'],maas_share=r['share_maas']))
        writecsv(out/'price_profile.csv',profile)
    (out/'COMPLETE').write_text('cost/state/price audit completed\n')

if __name__=='__main__':
    for tag in ['sioux_node_node_total0_without','sioux_node_node_total0_with','sioux_aggregate_node_total0_without','sioux_aggregate_node_total0_with','small_node_node_total0_without','small_node_node_total0_with']:
        if (OUT/tag/'COMPLETE').exists(): continue
        audit(tag)
