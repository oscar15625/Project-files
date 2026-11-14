"""Same-model VI root: flow coordinates + stable per-customer fare score.

Not an extragradient algorithm. All prices remain explicit. No reference warm start.
"""
from research_v71 import *
from scipy.optimize import least_squares,minimize_scalar
import argparse
P=ROOT/'results/vi_cloud_20261114'
sys.path.insert(0,str(P/'sources'))
from nested_extension import NestedModel

def solve(label,cfg,factor,score):
    tag=f'{label}_{score}_{factor:g}';dest=P/'runs'/tag;dest.mkdir(parents=True,exist_ok=True)
    if (dest/'COMPLETE.json').exists():return
    m=NestedModel(**cfg) if 'nest_lambda' in cfg else Model(**cfg)
    y0=m.project(m.initial()*factor);mask=m.congest;lo=np.r_[np.where(mask,0,m.t0),np.zeros(len(y0)-m.nt)]
    hi=np.full(len(y0),200.);hi[:m.nt][mask]=((200/m.t0[mask]-1)/.15)**.25
    used=set(int(i) for _,group in m.graphs for g in group.values() for i in g.res if i>=0)
    unused=np.array([i for i in range(m.nt) if i not in used],dtype=int)
    x0=y0.copy();x0[:m.nt][mask]=(np.maximum(y0[:m.nt][mask]/m.t0[mask]-1,0)/.15)**.25
    x0[unused]=lo[unused];active=np.array([i for i in range(len(x0)) if i not in unused])
    calls=0;phase='solver';budget=8000;tick=time.perf_counter();cpu=time.process_time();orig=m.evaluate
    trace=[];best=[float('inf'),x0.copy()]
    def evaluate(y,details=False):
        nonlocal calls
        if phase=='solver' and calls>=budget:raise RuntimeError('H_BUDGET')
        calls+=1;return orig(y,details)
    m.evaluate=evaluate
    def decode(x):
        y=x.copy();y[:m.nt][mask]=m.t0[mask]*(1+.15*np.maximum(x[:m.nt][mask],0)**4);return y
    def residual(x):
        y=decode(x);h,_=m.evaluate(y,True);flow=m.last_flows.copy();v=np.zeros_like(x)
        v[:m.nt][mask]=x[:m.nt][mask]-flow[mask]/m.cap[mask]
        v[:m.nt][~mask]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~mask]
        if m.maas:
            od=np.asarray(m.last_od);lam=getattr(m,'nest_lambda',1.);w=od[:,6]/np.maximum(od[:,4]+od[:,6],1e-300)
            kappa=(od[:,5]*w+(1-w)/lam)/m.mode_theta
            hf=(y[m.nt:-2]-od[:,8]-od[:,9])*kappa-1 if score=='SCORE' else h[m.nt:-2]/m.ods[:,2]
            v[m.nt:-2]=y[m.nt:-2]-np.clip(y[m.nt:-2]-hf,0,200)
        v[-2:]=y[-2:]-np.clip(y[-2:]-h[-2:]/np.maximum(m.retail_volume,1e-8),0,200)
        return v
    def fun(z):
        x=x0.copy();x[active]=z;v=residual(x);nr=float(np.linalg.norm(v))
        if nr<best[0]:best[:]=[nr,x.copy()]
        if not trace or calls-trace[-1]['h_calls']>=200:
            trace.append(dict(h_calls=calls,full_scaled=nr,seconds=time.perf_counter()-tick));write(dest/'trace.json',trace);np.save(dest/'checkpoint.npy',best[1])
        return v[active]
    write(dest/'config.json',dict(model=cfg,initial_factor=factor,fare_scaling=score,h_budget=budget,gtol=1e-14,xtol=1e-12,ftol=1e-12,max_nfev=200,x_scale='jac',unused_resources=unused.tolist(),start='cold Model.initial()*factor; no equilibrium state loaded'))
    try:
        opt=least_squares(fun,np.maximum(x0[active],lo[active]+1e-8),bounds=(lo[active],hi[active]),xtol=1e-12,ftol=1e-12,gtol=1e-14,x_scale='jac',max_nfev=200)
        x=x0.copy();x[active]=opt.x;stop=str(opt.message)
    except RuntimeError as e:
        if str(e)!='H_BUDGET':raise
        x=best[1];stop='H_BUDGET_EXHAUSTED'
    solver_calls=calls;solver_seconds=time.perf_counter()-tick;phase='validation'
    y=decode(x);np.save(dest/'raw_state.npy',y);np.save(dest/'raw_coordinates.npy',x)
    m.evaluate(y);flow=m.last_flows.copy();snap=(~mask)&(y[:m.nt]-m.t0<1e-6)&(m.cap-flow>1e-3)
    cleanup=float(np.max(y[:m.nt][snap]-m.t0[snap])) if snap.any() else 0.;x[:m.nt][snap]=m.t0[snap];y=decode(x)
    full=float(np.linalg.norm(residual(x)));h,r=m.evaluate(y,True);flow=m.last_flows.copy();od=np.asarray(m.last_od).copy()
    # Independently evaluate the same model's original H, not the solver's score.
    ha=h.copy();ha[:m.nt][mask]=m.cap[mask]*x[:m.nt][mask]-flow[mask]
    aux=float(np.linalg.norm(y-m.project(y-1e-4*ha)));direct=float(np.linalg.norm(y-m.project(y-1e-4*h)))
    cap=float(np.maximum(flow[~mask]-m.cap[~mask],0).max());comp=float(np.max(abs((y[:m.nt]-m.t0)[~mask]*(m.cap-flow)[~mask])))
    forward=float(np.max(abs(y[:m.nt][mask]-m.t0[mask]*(1+.15*(flow[mask]/m.cap[mask])**4))))
    deviations=[];fd=[]
    variables=[(-2,'profit_mod'),(-1,'profit_pt')]+([(m.nt+j,'profit_maas') for j in range(m.nod)] if m.maas else [])
    for i,key in variables:
        def value(price):
            z=y.copy();z[i]=price;return m.evaluate(z)[1][key]
        grid=np.unique(np.r_[np.linspace(0,max(5,min(200,y[i]*2)),31),[10,25,50,100,200]])
        vals=np.array([value(p) for p in grid]);j=int(vals.argmax());lower=grid[max(j-1,0)];upper=grid[min(j+1,len(grid)-1)]
        opt=minimize_scalar(lambda p:-value(p),bounds=(lower,upper),method='bounded',options={'xatol':1e-9})
        deviations.append(dict(index=i,gain=float(max(0,vals.max()-r[key],-opt.fun-r[key]))))
        eps=1e-5;fd.append(float(abs((value(y[i]+eps)-value(y[i]-eps))/(2*eps)+h[i])))
    exactgain=None
    if m.maas and not isinstance(m,NestedModel):
        m.optimize_fares=True;z=y.copy();exactgain=max(0,m.evaluate(z)[1]['profit_maas']-r['profit_maas']);m.optimize_fares=False
    pricegain=max([a['gain'] for a in deviations]+[exactgain or 0]);fderror=max(fd)
    basepass=full<1e-6 and aux<1e-6 and cap<1e-4 and comp<1e-3 and abs(r['accounting_error'])<1e-6 and r['flow_conservation_error']<1e-6 and pricegain<1e-4 and fderror<1e-5 and np.max(y)<199.999
    status='PASS' if basepass else 'FAILED_VALIDATION'
    result=dict(**r,status=status,strict_original_time_pass=bool(basepass and direct<1e-6),full_scaled=full,natural_aux=aux,natural_direct=direct,capacity_violation=cap,complementarity=comp,forward_bpr_error=forward,price_audit_gain=pricegain,finite_difference_error=fderror,deviations=deviations,exact_mnl_fare_gain=exactgain,solver_h_calls=solver_calls,validation_h_calls=calls-solver_calls,total_h_calls=calls,pumcm_calls=calls*sum(len(g) for _,g in m.graphs),solver_seconds=solver_seconds,total_seconds=time.perf_counter()-tick,cpu_seconds=time.process_time()-cpu,stop_reason=stop,cleanup_max_time=cleanup,model_config=cfg,case=label,factor=factor,score=score)
    np.save(dest/'state.npy',y);np.save(dest/'coordinates.npy',x);np.savetxt(dest/'od_results.csv',od,delimiter=',',header='origin,destination,demand,fare,share_non,share_drive,share_maas,value,wholesale_mod,wholesale_pt',comments='')
    write(dest/'metrics.json',result);write(dest/'COMPLETE.json',dict(status=status));write(dest/'trace.json',trace)
    print(tag,status,'strict',result['strict_original_time_pass'],'H',solver_calls,'res',full,'gain',pricegain,flush=True)

def campaign():
    assert read(P/'audit_status.json')['status']=='PASS_MODEL_AND_SAVED_STATES'
    jobs=[]
    for c in ['A_no_maas','B_maas_no_transfer_advantage','C_maas_paper_advantage']:
        cfg=read(folder('E01',c)/'metrics.json')['config']
        for f in [.95,1.,1.05]:jobs.append((c,cfg,f,'SCORE'))
        jobs.append((c,cfg,1.,'DEMAND'))
    for c in sorted((P/'cloud_reference').iterdir()):jobs.append((c.name,read(c/'config.json'),1.,'SCORE'))
    write(P/'solver_protocol.json',dict(date='2026-11-14',jobs=jobs,solver='FLOW_SCORE_TRF',note='Trust-region root, not EG; score identity H_f=q*P_maas*score. Same thresholds and initial traffic/retail/fare values; all prices explicit. No MNL closed-form fare inserted into nested model. DEMAND is matched gtol ablation to isolate score normalization.',budget_h=8000,validation_extra=True,scope='Small only; no E03/M03 rerun'))
    for c,cfg,f,s in jobs:
        p=P/'runs'/f'{c}_{s}_{f:g}';p.mkdir(parents=True,exist_ok=True);write(p/'job.json',dict(label=c,cfg=cfg,factor=f,score=s))
        if (p/'COMPLETE.json').exists():continue
        with (p/'execution.log').open('a',encoding='utf-8') as log:rc=subprocess.run([sys.executable,__file__,'worker',str(p/'job.json')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        if rc.returncode:raise RuntimeError(f'Worker crashed {p}')
        r=read(p/'metrics.json');print(c,s,f,r['status'],r['strict_original_time_pass'],r['solver_h_calls'],flush=True)
    write(P/'campaign_status.json',dict(status='FINISHED',runs=len(jobs)))
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':solve(**read(Path(sys.argv[2])))
    else:campaign()
