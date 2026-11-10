"""Separate fixed-time and traffic-re-equilibrated finite-price counterfactuals."""
from research_v7 import *
from scipy.optimize import least_squares
def traffic(m,start,xstart):
    mask=m.congest;m.optimize_fares=False;calls=0;tick=time.perf_counter()
    def decode(x):
        z=start.copy();z[:m.nt]=x;z[:m.nt][mask]=m.t0[mask]*(1+.15*np.maximum(x[mask],0)**4);return z
    def fun(x):
        nonlocal calls
        calls+=1;z=decode(x);h,r=m.evaluate(z);f=m.last_flows;res=x.copy()
        res[mask]=x[mask]-f[mask]/m.cap[mask]
        res[~mask]=(z[:m.nt]-np.maximum(m.t0,z[:m.nt]-h[:m.nt]/m.cap))[~mask]
        return res
    lo=np.where(mask,0,m.t0);opt=least_squares(fun,np.maximum(xstart,lo+1e-9),bounds=(lo,np.full(m.nt,200.)),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=100)
    y=decode(opt.x);h,r=m.evaluate(y);f=m.last_flows.copy();selected=(~mask)&(y[:m.nt]-m.t0<1e-6)&(m.cap-f>1e-3)
    y[:m.nt][selected]=m.t0[selected];opt.x[selected]=m.t0[selected];h,r=m.evaluate(y);f=m.last_flows.copy()
    h[:m.nt][mask]=m.cap[mask]*opt.x[mask]-f[mask]
    nr=float(np.linalg.norm(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-1e-4*h[:m.nt])))
    comp=float(np.max(abs((y[:m.nt][~mask]-m.t0[~mask])*(m.cap[~mask]-f[~mask]))))
    scaled=float(np.linalg.norm(fun(opt.x)))
    r.update(traffic_natural_aux=nr,traffic_scaled=scaled,capacity_complementarity=comp,traffic_pass=nr<1e-6 and scaled<1e-6 and comp<1e-3,calls=calls,seconds=time.perf_counter()-tick,solver_message=opt.message)
    return y,r
def main():
    rows=[]
    for tag in ['mod_1.5_pt_1.5','mod_0_pt_1.5','mod_3_pt_3']:
        p=folder('E03_coarse',tag);old=read(p/'metrics.json');m=Model(**old['config']);base=np.load(p/'state.npy');x=np.load(p/'coordinates.npy')[:m.nt]
        for op,idx in [('mod',-2),('pt',-1)]:
            for factor in [.95,1.,1.05]:
                z=base.copy();z[idx]*=factor;_,fixed=m.evaluate(z)
                path=V7/'M02'/f'{tag}_{op}_{factor:g}';path.mkdir(parents=True,exist_ok=True)
                if (path/'metrics.json').exists():r=read(path/'metrics.json')
                else:
                    y,r=traffic(m,z,x);np.save(path/'state.npy',y);write(path/'metrics.json',r)
                rows.append(dict(scenario=tag,operator=op,price_factor=factor,original_profit=old['profit_'+op],fixed_time_gain=fixed['profit_'+op]-old['profit_'+op],reequilibrated_gain=r['profit_'+op]-old['profit_'+op],traffic_pass=r['traffic_pass'],natural_aux=r['traffic_natural_aux'],scaled=r['traffic_scaled'],complementarity=r['capacity_complementarity'],calls=r['calls'],seconds=r['seconds'],classification='NEW_COUNTERFACTUAL',interpretation='Fixed rival prices and MaaS fares; different timing assumption, not original VI Nash violation'))
                print('M02',tag,op,factor,rows[-1]['reequilibrated_gain'],r['traffic_pass'],flush=True)
    csvout('strategic_counterfactual.csv',rows)
    attempts=[]
    for tag,factor,source in [('mod_1.5_pt_1.5',.95,'mod_1.5_pt_1.5'),('mod_1.5_pt_1.5',1.05,'mod_1.5_pt_1.5'),('mod_3.5_pt_1.5',1.,'mod_3_pt_1.5')]:
        p=folder('E03_coarse',tag);original=read(p/'metrics.json');dest=V7/'multistart'/f'{tag}_{factor:g}';dest.mkdir(parents=True,exist_ok=True)
        if (dest/'validation.json').exists():r=read(dest/'metrics.json');v=read(dest/'validation.json')
        else:
            m=Model(**original['config']);start=np.load(folder('E03_coarse',source)/'state.npy');start=m.project(start*factor)
            y,r=refine(m,str(dest.relative_to(ROOT/'results')),start,maxiter=100)
            raw=dest/'raw_solver';raw.mkdir(exist_ok=True)
            for n in ['metrics.json','state.npy','coordinates.npy']:shutil.copy2(dest/n,raw/n)
            x=np.load(dest/'coordinates.npy');y,x,changes=polish(m,y,x);r.update(changes);write(dest/'metrics.json',r);np.save(dest/'state.npy',y);np.save(dest/'coordinates.npy',x)
            v=validate(dest,r,y,x);r.update(v);write(dest/'metrics.json',r)
        attempts.append(dict(scenario=tag,start_factor=factor,start_source=source,status=v['status'],profit_mod=r['profit_mod'],profit_pt=r['profit_pt'],profit_maas=r['profit_maas'],residual=r['natural_residual'],classification='DIAGNOSTIC_ONLY',coarse_grid_membership='UNCHANGED'))
    csvout('multistart.csv',attempts)
if __name__=='__main__':main()
