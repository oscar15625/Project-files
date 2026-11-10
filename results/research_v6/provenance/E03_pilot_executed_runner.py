"""Gated E01/E03 counterfactual campaign on an unchanged V5 model."""
import os,sys,time,json,hashlib,subprocess,traceback,threading,csv,shutil,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent; os.chdir(ROOT)
sys.path.insert(0,str(ROOT.parents[1]/'.vendor'))
import run
import numpy as np
import ctypes
from ctypes import wintypes
from scipy.special import logsumexp
from src.model import Model
from refine import refine
from audit import audit
from spec_audit_v5 import components,FIELDS,writecsv
OUT=ROOT/'results/research_v6'
def memory_rss():
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
    c=Counters(); c.cb=ctypes.sizeof(c)
    kernel=ctypes.windll.kernel32; kernel.GetCurrentProcess.restype=wintypes.HANDLE
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    if not ctypes.windll.psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(c),c.cb): raise OSError('Memory measurement failed')
    return c.WorkingSetSize
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj,indent=2,default=lambda x:x.item()),encoding='utf-8'); tmp.replace(path)
def sha(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()
def gitsha(): return subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
class CountModel(Model):
    def __init__(self,**cfg): super().__init__(**cfg); self.calls=0; self.pumcm_calls=0; self.evaluation_seconds=0.
    def evaluate(self,y,details=False):
        tick=time.perf_counter(); self.calls+=1; self.pumcm_calls+=sum(len(g) for _,g in self.graphs)
        try: return super().evaluate(y,details)
        finally: self.evaluation_seconds+=time.perf_counter()-tick
def config(maas=True,penalty=1,wholesale=(1.3,1.3)):
    return dict(name='small',maas=maas,theta=1,mode_theta=1,penalty=penalty,wholesale=list(wholesale),mod_access_scope='node',pt_access_scope='node',pt_capacity_total=False)
def cases(phase):
    if phase=='E01':
        return [('A_no_maas',config(False,10)),('B_maas_no_transfer_advantage',config(True,10)),('C_maas_paper_advantage',config())]
    values=[0.,1.5,3.] if phase=='E03_pilot' else np.arange(0,3.51,.5)
    return [(f'mod_{a:g}_pt_{b:g}',config(wholesale=(float(a),float(b)))) for a in values for b in values]
def folder(phase,tag): return OUT/phase/tag/'ROOT_AUX'/'0'
def polish(m,y,x):
    # Same numerical active-set rule for every case, predeclared in protocol.
    m.optimize_fares=False; m.evaluate(y); flows=m.last_flows.copy()
    selected=(~m.congest)&(y[:m.nt]-m.t0<1e-6)&(m.cap-flows>1e-3)
    delta=float(np.max(y[:m.nt][selected]-m.t0[selected])) if selected.any() else 0.
    y[:m.nt][selected]=m.t0[selected]; x[:m.nt][selected]=m.t0[selected]
    m.optimize_fares=m.maas; h,r=m.evaluate(y); flows=m.last_flows.copy()
    h[:m.nt][m.congest]=m.cap[m.congest]*np.maximum(x[:m.nt][m.congest],0)-flows[m.congest]
    v=np.r_[h[:m.nt],h[-2:]]
    v[:m.nt][m.congest]=x[:m.nt][m.congest]-flows[m.congest]/m.cap[m.congest]
    v[:m.nt][~m.congest]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~m.congest]
    v[-2:]/=np.maximum(m.retail_volume,1e-8); v[-2:]=y[-2:]-np.maximum(0,y[-2:]-v[-2:])
    r.update(natural_residual=float(np.linalg.norm(y-m.project(y-1e-4*h))),scaled_residual=float(np.linalg.norm(v)),polish_max_time_change=delta)
    m.optimize_fares=False
    return y,x,r
def cost_check(m,y):
    records=[]; maxerr=0.; reconstructed=0.
    for ids,group in m.graphs:
        kinds=list(group); sols=[g.solve(y[:m.nt],y[-2:],m.wholesale,k) for k,g in group.items()]
        entries=np.array([np.full(len(ids),m.fixed) if k=='drive' else y[m.nt+ids] if k=='maas' else np.zeros(len(ids)) for k in kinds]).T
        vals=np.array([s[0] for s in sols]).T-entries; lv=logsumexp(vals/m.mode_theta,axis=1); shares=np.exp(vals/m.mode_theta-lv[:,None])
        for local,idx in enumerate(ids):
            root_entropy=-m.mode_theta*np.sum(shares[local]*np.log(np.maximum(shares[local],1e-300)))
            value=root_entropy
            for j,(kind,g) in enumerate(group.items()):
                inject=np.zeros(len(ids)); inject[local]=1; flow=sols[j][4](inject); parts=flow@components(m,g,y,kind)
                visits=np.bincount(g.i,weights=flow,minlength=g.n); mask=(flow>1e-200)&(visits[g.i]>0)
                entropy=-m.theta*np.sum(flow[mask]*np.log(flow[mask]/visits[g.i[mask]]))
                maxerr=max(maxerr,abs(sols[j][0][local]+parts.sum()-entropy))
                value+=shares[local,j]*(-parts.sum()-entries[local,j]+entropy)
                records.append(dict(origin=int(m.ods[idx,0]),destination=int(m.ods[idx,1]),kind=kind,mode_share=shares[local,j],**dict(zip(FIELDS,parts)),entry_charge=entries[local,j],route_entropy=entropy,paid_pt_links=flow@g.attr[:,3]))
            maxerr=max(maxerr,abs(value-m.mode_theta*lv[local])); reconstructed+=m.ods[idx,2]*value
    return maxerr,reconstructed,records
def validate(path,r,y,x):
    m=CountModel(**r['config']); h,b=m.evaluate(y,True); flow=m.last_flows.copy(); od=np.array(m.last_od)
    np.savetxt(path/'od_results.csv',od,delimiter=',',header='origin,destination,demand,maas_fare,share_non,share_drive,share_maas,value,conditional_wholesale_mod,conditional_wholesale_pt',comments='')
    np.savetxt(path/'resource_results.csv',np.c_[np.arange(m.nt),m.t0,m.cap,m.congest,y[:m.nt],flow],delimiter=',',header='resource,t0,capacity,congestible,time,flow',comments='')
    # Existing fixed-t audit reconstructs Model from config and writes only new path.
    a=audit(str(path.relative_to(ROOT/'results')))
    errors=[]
    for idx,key in [(-2,'profit_mod'),(-1,'profit_pt')]+([(m.nt,'profit_maas'),(m.nt+1,'profit_maas')] if m.maas else []):
        eps=1e-5; yp=y.copy(); ym=y.copy(); yp[idx]+=eps; ym[idx]-=eps
        fd=(m.evaluate(yp)[1][key]-m.evaluate(ym)[1][key])/(2*eps)
        errors.append(dict(index=idx,analytic=float(-h[idx]),finite_difference=float(fd),relative_error=float(abs(fd+h[idx])/max(1,abs(fd)))))
    probe=y.copy(); m.optimize_fares=m.maas; exact=m.evaluate(probe)[1]; m.optimize_fares=False
    faregain=max(0,exact['profit_maas']-b['profit_maas'])
    fixed=~m.congest; caperr=float(np.maximum(flow[fixed]-m.cap[fixed],0).max()); comp=float(np.max(abs((y[:m.nt][fixed]-m.t0[fixed])*(m.cap[fixed]-flow[fixed]))))
    err,welfare,rows=cost_check(m,y); writecsv(path/'od_costs.csv',rows)
    metrics=dict(vi_residual=r['natural_residual'],scaled_residual=r['scaled_residual'],capacity_violation=caperr,capacity_complementarity=comp,conservation_error=b['flow_conservation_error'],accounting_error=abs(b['accounting_error']),cost_identity_error=err,welfare_identity_error=abs(welfare-b['traveler_welfare']),deviation_gain_fixed_t=max(a[k]['unilateral_gain'] for k in ['profit_mod','profit_pt']),maas_exact_fare_gain=faregain,finite_differences=errors,deviation_gain_reequilibrated=None)
    status='PASS'
    if not np.all(np.isfinite(y)) or np.max(y)>=199.999 or min(y[-2:])<0: status='FAILED_SOLVER'
    elif max(r['natural_residual'],r['scaled_residual'])>=1e-6 or caperr>=1e-4 or comp>=1e-3: status='FAILED_VI'
    elif abs(b['accounting_error'])>=1e-6 or b['flow_conservation_error']>=1e-6: status='FAILED_ACCOUNTING'
    elif metrics['deviation_gain_fixed_t']>=1e-4 or faregain>=1e-4: status='FAILED_DEVIATION'
    elif err>=1e-6 or metrics['welfare_identity_error']>=1e-6 or max(e['relative_error'] for e in errors)>=1e-4: status='FAILED_BEHAVIORAL_CHECK'
    metrics['status']=status; write(path/'validation.json',metrics)
    return metrics
def execute(phase,tag,cfg):
    path=folder(phase,tag); path.mkdir(parents=True,exist_ok=True)
    if (path/'COMPLETE').exists(): return json.loads((path/'metrics.json').read_text())
    m=CountModel(**cfg); source='small_node_node_total0_'+('with' if m.maas else 'without')
    meta=dict(experiment_id=phase,scenario_id=tag,experiment_class='S',paper_source='Sections 3-5; Table 2; section 5.1.4',assumption_status='reconstruction counterfactual; illustrative, not empirically calibrated',baseline_id='E01/A_no_maas',model_config=m.config(),git_sha=gitsha(),config_hash=sha(m.config()),seed=0,solver='ROOT_AUX',source_start='results/v4/'+source+'/state.npy',derivative_scope='fixed time and other prices',reequilibrated_deviation_status='NOT_PERFORMED')
    write(path/'configuration.json',meta)
    stop=threading.Event(); peak=[memory_rss()]
    def sample():
        while not stop.wait(.05): peak[0]=max(peak[0],memory_rss())
    monitor=threading.Thread(target=sample,daemon=True); monitor.start(); tick=time.perf_counter(); cpu=time.process_time()
    try:
        if not (path/'metrics.json').exists():
            start=np.load(ROOT/'results/v4'/source/'state.npy'); start[-2:]*=[1.03,.97]
            resume=any((path/'checkpoints').glob('*.npz'))
            y,r=refine(m,str(path.relative_to(ROOT/'results')),start,maxiter=100,resume=resume)
            # Preserve raw solver outputs before applying the common cleanup rule.
            raw=path/'raw_solver'; raw.mkdir(exist_ok=True)
            for name in ['metrics.json','state.npy','coordinates.npy']: shutil.copy2(path/name,raw/name)
            x=np.load(path/'coordinates.npy'); y,x,changes=polish(m,y,x); r.update(changes)
            np.save(path/'state.npy',y); np.save(path/'coordinates.npy',x); write(path/'metrics.json',r)
        else:
            r=json.loads((path/'metrics.json').read_text()); y=np.load(path/'state.npy'); x=np.load(path/'coordinates.npy')
        solver_seconds=time.perf_counter()-tick; solver_calls=m.calls; pumcm=m.pumcm_calls; eval_seconds=m.evaluation_seconds
        v=validate(path,r,y,x)
        r.update(meta); r.update(v); r.update(time_seconds=time.perf_counter()-tick,solver_seconds=solver_seconds,cpu_seconds=time.process_time()-cpu,h_evaluations=solver_calls,pumcm_evaluations=pumcm,h_seconds=eval_seconds,peak_memory_mb=peak[0]/1024**2,memory_method='process RSS sampled every 50 ms; includes interpreter and imported libraries',government_net=None)
        write(path/'metrics.json',r); (path/'COMPLETE').write_text(v['status'])
        return r
    finally: stop.set(); monitor.join(timeout=1)
def main():
    p=argparse.ArgumentParser(); p.add_argument('phase',choices=['E01','E03_pilot','E03_coarse']); args=p.parse_args()
    assert json.loads((OUT/'G00/status.json').read_text())['status']=='PASS'
    if args.phase!='E01':
        assert all(json.loads((folder('E01',t)/'metrics.json').read_text())['status']=='PASS' for t,_ in cases('E01'))
    if args.phase=='E03_coarse':
        assert all(json.loads((folder('E03_pilot',t)/'metrics.json').read_text())['status']=='PASS' for t,_ in cases('E03_pilot')), 'Pilot failed: no grid expansion permitted'
    manifest=json.loads((OUT/'manifest.json').read_text()) if (OUT/'manifest.json').exists() else {}
    for tag,cfg in cases(args.phase):
        key=args.phase+'/'+tag; write(OUT/'running.json',dict(pid=os.getpid(),case=key,status='RUNNING')); print('START',key,flush=True)
        try:
            r=execute(args.phase,tag,cfg); manifest[key]=dict(status=r['status'],path=str(folder(args.phase,tag).relative_to(ROOT)),config=cfg)
        except Exception:
            error=traceback.format_exc(); print(error,flush=True); write(folder(args.phase,tag)/'failure.json',dict(status='FAILED_SOLVER',error=error))
            manifest[key]=dict(status='FAILED_SOLVER',path=str(folder(args.phase,tag).relative_to(ROOT)),config=cfg,error=error)
        write(OUT/'manifest.json',manifest); print('FINISHED',key,manifest[key]['status'],flush=True)
    write(OUT/'running.json',dict(pid=os.getpid(),phase=args.phase,status='FINISHED'))
if __name__=='__main__': main()
