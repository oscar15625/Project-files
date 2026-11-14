"""Cold-start scaled VI residual solver; isolated v7.1 follow-up, no baseline edits."""
from research_v71 import *
from scipy.optimize import least_squares
import argparse
Q=O/'m01_improved_20261110'
CASES=['A_no_maas','B_maas_no_transfer_advantage','C_maas_paper_advantage']

def diagnostic():
    Q.mkdir(parents=True,exist_ok=True);rows=[];components=[]
    for p in sorted((O/'m01_runs').glob('*/metrics.json')):
        old=read(p);m=Model(**old['config']);y=np.load(p.parent/'state.npy');h,_=m.evaluate(y);f=m.last_flows.copy();r=y-m.project(y-1e-4*h)
        used=set(int(i) for _,group in m.graphs for g in group.values() for i in g.res if i>=0)
        un=np.array([i not in used for i in range(m.nt)])
        near=(y[:m.nt]-m.t0)<1e-9
        a=dict(run=p.parent.name,method=old['method'],natural=float(np.linalg.norm(r)),traffic_norm=float(np.linalg.norm(r[:m.nt])),price_norm=float(np.linalg.norm(r[m.nt:])),unused_norm=float(np.linalg.norm(r[:m.nt][un])),congested_boundary_norm=float(np.linalg.norm(r[:m.nt][near&m.congest])),step=old['final_step'],iterate_change=old['last_iterate_change'],original_status=old['status'])
        rows.append(a)
        for i in np.argsort(abs(r))[-5:][::-1]:
            d=dict(run=p.parent.name,index=int(i),residual=float(r[i]),kind='traffic' if i<m.nt else 'price')
            if i<m.nt:d.update(unused=bool(un[i]),congestible=bool(m.congest[i]),time=float(y[i]),t0=float(m.t0[i]),flow=float(f[i]),forward_time_error=float(y[i]-m.t0[i]*(1+.15*(f[i]/m.cap[i])**4)) if m.congest[i] else None)
            components.append(d)
    outcsv('m01_improved_20261110/original_failure_blocks.csv',rows);outcsv('m01_improved_20261110/original_top_components.csv',components)
    write(Q/'protocol.json',dict(cases=CASES,flow_initial_factors=[.95,1,1.05],time_ablation_initial_factors=[1],solver_h_budget=8000,solver='bounded trust-region reflective least squares on equivalent projected VI residual',tolerances=dict(xtol=1e-12,ftol=1e-12,gtol=1e-12,natural=1e-6,full_scaled=1e-6),max_nfev=200,x_scale='jac',prices='all explicit; no analytic MaaS fare elimination',initial='same projected Model.initial()*factor as M01; no equilibrium warm start',unused='Only graph-absent traffic resources are fixed exactly to free time; both ablations use same elimination',bounds='Original t<=200 guard expressed consistently in flow coordinates; reject artificial-bound hits',acceptance='inherited auxiliary residual and full scaled including MaaS fares, physical/economic checks; separately require direct-time criterion for strict M01 comparison',notes='Not an EG trajectory or a global convergence proof. Numerical Jacobian H calls included in budget; validation extra and reported.'))
    print('Original failure diagnosis saved',flush=True)

def worker(label,factor,kind):
    dest=Q/f'{label}_{kind}_{factor:g}';dest.mkdir(parents=True,exist_ok=True)
    if (dest/'metrics.json').exists():return
    cfg=read(folder('E01',label)/'metrics.json')['config'];m=Model(**cfg);m.optimize_fares=False
    y0=m.project(m.initial()*factor);mask=m.congest
    used=set(int(i) for _,group in m.graphs for g in group.values() for i in g.res if i>=0)
    unused=np.array([i for i in range(m.nt) if i not in used],dtype=int)
    active=np.array([i for i in range(len(y0)) if i not in unused])
    y0[unused]=m.t0[unused];x0=y0.copy()
    if kind=='FLOW_TRF':x0[:m.nt][mask]=(np.maximum(y0[:m.nt][mask]/m.t0[mask]-1,0)/.15)**.25
    lower=np.r_[np.where(mask,0,m.t0) if kind=='FLOW_TRF' else m.t0,np.zeros(len(y0)-m.nt)]
    upper=np.full(len(y0),200.)
    if kind=='FLOW_TRF':upper[:m.nt][mask]=((200/m.t0[mask]-1)/.15)**.25
    calls=0;graphs=0;phase='solver';budget=8000;trace=[];best=[float('inf'),x0.copy()];tick=time.perf_counter();cpu=time.process_time()
    from src.model import Graph
    oldeval=Model.evaluate;oldgraph=Graph.solve
    def counted(self,y,details=False):
        nonlocal calls
        if phase=='solver' and calls>=budget:raise RuntimeError('H_BUDGET')
        calls+=1;return oldeval(self,y,details)
    def countgraph(self,*a,**k):
        nonlocal graphs
        graphs+=1;return oldgraph(self,*a,**k)
    Model.evaluate=counted;Graph.solve=countgraph
    def decode(x):
        y=x.copy()
        if kind=='FLOW_TRF':y[:m.nt][mask]=m.t0[mask]*(1+.15*np.maximum(x[:m.nt][mask],0)**4)
        return y
    def fullres(x):
        y=decode(x);h,_=m.evaluate(y);f=m.last_flows.copy();v=y.copy()
        if kind=='FLOW_TRF':v[:m.nt][mask]=x[:m.nt][mask]-f[mask]/m.cap[mask]
        else:v[:m.nt][mask]=((np.maximum(y[:m.nt][mask]/m.t0[mask]-1,0)/.15)**.25-f[mask]/m.cap[mask])
        v[:m.nt][~mask]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~mask]
        if m.maas:v[m.nt:-2]=y[m.nt:-2]-np.maximum(0,y[m.nt:-2]-h[m.nt:-2]/m.ods[:,2])
        v[-2:]=y[-2:]-np.maximum(0,y[-2:]-h[-2:]/np.maximum(m.retail_volume,1e-8))
        return v
    def fun(z):
        x=x0.copy();x[active]=z;v=fullres(x);norm=float(np.linalg.norm(v))
        if norm<best[0]:best[:]=[norm,x.copy()]
        if not trace or calls-trace[-1]['h_calls']>=200:
            trace.append(dict(h_calls=calls,scaled=norm,seconds=time.perf_counter()-tick));write(dest/'trace.json',trace);np.save(dest/'checkpoint_coordinates.npy',best[1]);print(label,kind,factor,calls,norm,flush=True)
        return v[active]
    write(dest/'configuration.json',dict(config=cfg,kind=kind,factor=factor,h_budget=budget,unused_resources=unused.tolist(),original_projected_initial=m.project(m.initial()*factor).tolist(),no_equilibrium_warm_start=True))
    message=''
    try:
        opt=least_squares(fun,np.maximum(x0[active],lower[active]+1e-8),bounds=(lower[active],upper[active]),method='trf',x_scale='jac',xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=200)
        x=x0.copy();x[active]=opt.x;message=str(opt.message)
    except RuntimeError as e:
        if str(e)!='H_BUDGET':raise
        x=best[1];message='H_BUDGET_EXHAUSTED'
    solver_calls=calls;solver_graphs=graphs;solver_seconds=time.perf_counter()-tick;phase='validation'
    y=decode(x);np.save(dest/'raw_state.npy',y);np.save(dest/'raw_coordinates.npy',x)
    m.evaluate(y);f=m.last_flows.copy()
    selected=(~mask)&(y[:m.nt]-m.t0<1e-6)&(m.cap-f>1e-3)
    cleanup=float(np.max(y[:m.nt][selected]-m.t0[selected])) if selected.any() else 0
    x[:m.nt][selected]=m.t0[selected];y=decode(x)
    coord=x.copy()
    if kind!='FLOW_TRF':coord[:m.nt][mask]=(np.maximum(y[:m.nt][mask]/m.t0[mask]-1,0)/.15)**.25
    r,d=metrics(m,y,coord);fs=float(np.linalg.norm(fullres(x)))
    np.save(dest/'state.npy',y);np.save(dest/'coordinates.npy',coord)
    r.update(config=cfg,natural_residual=d['natural_aux'],scaled_residual=fs);write(dest/'metrics.json',r)
    v=validate(dest,r,y,coord)
    r.update(v,**d,method=kind,initial_factor=factor,full_scaled=fs,solver_h_calls=solver_calls,solver_pumcm_calls=solver_graphs,solver_seconds=solver_seconds,cleanup_max_time=cleanup,stop_reason=message)
    r['status']=v['status'] if fs<1e-6 else 'FAILED_NUMERICAL_CHECK'
    r['strict_original_time_pass']=r['status']=='PASS' and d['natural_direct']<1e-6
    r.update(total_h_calls=calls,validation_h_calls=calls-solver_calls,total_pumcm_calls=graphs,seconds=time.perf_counter()-tick,cpu_seconds=time.process_time()-cpu)
    write(dest/'metrics.json',r);write(dest/'trace.json',trace);print('FINAL',label,kind,factor,r['status'],r['strict_original_time_pass'],solver_calls,fs,flush=True)

def campaign():
    diagnostic()
    jobs=[(c,f,'FLOW_TRF') for c in CASES for f in [.95,1.,1.05]]+[(c,1.,'TIME_TRF') for c in CASES]
    for c,f,k in jobs:
        p=Q/f'{c}_{k}_{f:g}';p.mkdir(parents=True,exist_ok=True)
        if (p/'metrics.json').exists() and 'strict_original_time_pass' in read(p/'metrics.json'):continue
        with (p/'execution.log').open('a',encoding='utf-8') as log:
            z=subprocess.run([sys.executable,__file__,'worker','--case',c,'--factor',str(f),'--kind',k],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        if z.returncode:raise RuntimeError(f'Worker failed {p}; inspect preserved log')
        print('FINISHED',c,f,k,flush=True)
    write(Q/'campaign_status.json',dict(status='FINISHED',runs=12))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['campaign','worker']);p.add_argument('--case');p.add_argument('--factor',type=float,default=1);p.add_argument('--kind',default='FLOW_TRF');a=p.parse_args()
    if a.mode=='campaign':campaign()
    else:worker(a.case,a.factor,a.kind)
