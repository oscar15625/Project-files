"""Bounded-budget full-demand Sioux Falls tariff counterfactuals; checkpoint every 25 H calls."""
from extension import *
from scipy.optimize import root,least_squares,minimize_scalar
from scipy.special import logsumexp
import argparse
class Budget(Exception):pass
def validate(m,y,x):
 m.optimize_fares=False;h,r=m.evaluate(y.copy(),True);f=m.last_flows.copy();mask=m.congest
 od=np.asarray(m.last_od).copy();ha=h.copy();ha[:m.nt][mask]=m.cap[mask]*x[:m.nt][mask]-f[mask]
 direct=float(np.linalg.norm(y-m.project(y-1e-4*h)));aux=float(np.linalg.norm(y-m.project(y-1e-4*ha)))
 cap=float(np.maximum(f[~mask]-m.cap[~mask],0).max());comp=float(np.max(abs((y[:m.nt]-m.t0)[~mask]*(m.cap-f)[~mask])))
 v=np.zeros(m.nt+2);v[:m.nt][mask]=x[:m.nt][mask]-f[mask]/m.cap[mask];v[:m.nt][~mask]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~mask]
 v[-2:]=y[-2:]-np.clip(y[-2:]-h[-2:]/np.maximum(m.retail_volume,1e-8),0,200)
 score=float(np.max(abs((od[:,3]-od[:,8]-od[:,9])*(1-od[:,6])/m.mode_theta-1))) if m.maas else 0.
 # Independent Markov node balance and paid-unit aggregation, including transfer OD.
 paid=0.;balance=0.;non_units=[]
 for ids,gr in m.graphs:
  kinds=list(gr);sol={k:g.solve(y[:m.nt],y[-2:],m.wholesale,k) for k,g in gr.items()}
  vals=np.array([sol[k][0]-(m.fixed if k=='drive' else y[m.nt:-2][ids] if k=='maas' else 0) for k in kinds]).T
  probs=np.exp(vals/m.mode_theta-logsumexp(vals/m.mode_theta,axis=1)[:,None]);assert np.max(abs(probs.sum(axis=1)-1))<1e-12
  for j,k in enumerate(kinds):
   g=gr[k];q=m.ods[ids,2]*probs[:,j];flow=sol[k][-1](q)
   inflow=np.bincount(g.j[g.internal],weights=flow[g.internal],minlength=g.n);outflow=np.bincount(g.i,weights=flow,minlength=g.n)
   injection=np.zeros(g.n);np.add.at(injection,g.gates,q);balance=max(balance,float(np.max(abs(outflow-inflow-injection))))
   if k=='non':paid+=float(flow@g.attr[:,3])
  # Per OD paid units retain MoD -> PT first-boarders, not just PT-station endpoints.
  g=gr['non']
  for j,idx in enumerate(ids):
   q=np.zeros(len(ids));q[j]=m.ods[idx,2]*probs[j,kinds.index('non')];fl=sol['non'][-1](q)
   non_units.append(dict(origin=int(m.ods[idx,0]),destination=int(m.ods[idx,1]),non_demand=float(q.sum()),paid_units=float(fl@g.attr[:,3])))
 revenue_err=abs(paid*y[-1]-r['retail_pt'])
 deviations=[];fd=[]
 for i,key in [(-2,'profit_mod'),(-1,'profit_pt')]:
  def value(p):
   yy=y.copy();yy[i]=p;return m.evaluate(yy)[1][key]
  grid=np.unique(np.r_[np.linspace(0,max(8,y[i]*2),25),[25,50,100,200],y[i]])
  vals=np.array([value(p) for p in grid]);j=int(vals.argmax());op=minimize_scalar(lambda p:-value(p),bounds=(grid[max(j-1,0)],grid[min(j+1,len(grid)-1)]),method='bounded',options={'xatol':1e-10})
  gain=max(0,float(vals.max()-r[key]),float(-op.fun-r[key]));deviations.append(dict(variable=i,gain=gain))
  # Five-point finite difference reduces truncation/cancellation at full-demand scale.
  eps=1e-3;df=(value(y[i]-2*eps)-8*value(y[i]-eps)+8*value(y[i]+eps)-value(y[i]+2*eps))/(12*eps)
  fd.append(dict(variable=i,analytic=-float(h[i]),finite_difference=df,absolute_error=abs(df+h[i])))
 exact=0.
 if m.maas:
  m.optimize_fares=True;yy=y.copy();exact=max(0,float(m.evaluate(yy)[1]['profit_maas']-r['profit_maas']));m.optimize_fares=False
 gain=max([d['gain'] for d in deviations]+[exact]);fderr=max(d['absolute_error'] for d in fd)
 passed=direct<1e-6 and aux<1e-6 and np.linalg.norm(v)<1e-6 and score<1e-6 and cap<1e-4 and comp<1e-3 and abs(r['accounting_error'])<1e-6 and balance<1e-6 and revenue_err<1e-6 and gain<1e-4 and fderr<1e-5 and y.max()<199.999
 return dict(status='STRICT_PASS' if passed else 'FAILED_VALIDATION',**r,natural_direct=direct,natural_aux=aux,full_scaled=float(np.linalg.norm(v)),fare_score_max=score,capacity_violation=cap,complementarity=comp,markov_node_balance_error=balance,PT_revenue_error=revenue_err,price_deviation_gain=gain,exact_maas_deviation_gain=exact,finite_difference_error=fderr,retail_gradient_checks=fd,deviations=deviations,od=od.tolist(),PT_paid_units=paid,od_paid_units=non_units)
def solve(tariff,maas,start='primary',guess=None,budget=4000):
 os.chdir(ROOT);dest=ROOT/'results'/f'{tariff}_{"C" if maas else "A"}_{start}'
 if (dest/'COMPLETE.json').exists():return json.loads((dest/'metrics.json').read_text())
 dest.mkdir(parents=True,exist_ok=True);m=make('sioux',tariff,maas);m.optimize_fares=maas;mask=m.congest
 yy=m.initial() if guess is None else np.load(guess).copy()
 if start!='primary':yy[-2:]*=float(start);yy[:m.nt]=m.t0+(yy[:m.nt]-m.t0)*(1+(.01 if float(start)>1 else -.01))
 x=np.r_[yy[:m.nt],yy[-2:]];x[:m.nt][mask]=(np.maximum(x[:m.nt][mask]/m.t0[mask]-1,0)/.15)**.25
 used={int(i) for _,gr in m.graphs for g in gr.values() for i in g.res if i>=0}
 # Exclude only resources absent from every graph, never capacity-active links.
 active=np.array([i for i in range(m.nt+2) if i>=m.nt or i in used]);lo=np.r_[np.where(mask,0,m.t0),[0,0]];hi=np.full(len(x),200.);hi[:m.nt][mask]=((200/m.t0[mask]-1)/.15)**.25
 x[[i for i in range(m.nt) if i not in used]]=lo[[i for i in range(m.nt) if i not in used]]
 calls=0;tick=time.perf_counter();trace=[];best=[float('inf'),x.copy()];phase='HYBR';solving=True
 def decode(xx):
  t=xx[:m.nt].copy();t[mask]=m.t0[mask]*(1+.15*np.maximum(xx[:m.nt][mask],0)**4);t=np.maximum(t,m.t0)
  return np.r_[t,np.zeros(m.nod) if maas else [],np.clip(xx[-2:],0,200)]
 def fun(z):
  nonlocal calls
  if solving and (calls>=budget or time.perf_counter()-tick>600):raise Budget()
  xx=x.copy();xx[active]=z;yy=decode(xx);calls+=1
  h,_=m.evaluate(yy);flow=m.last_flows
  v=np.zeros_like(xx);v[:m.nt][mask]=xx[:m.nt][mask]-flow[mask]/m.cap[mask]
  v[:m.nt][~mask]=(xx[:m.nt]-np.maximum(m.t0,xx[:m.nt]-h[:m.nt]/m.cap))[~mask]
  v[-2:]=xx[-2:]-np.clip(xx[-2:]-h[-2:]/np.maximum(m.retail_volume,1e-8),0,200)
  nr=float(np.linalg.norm(v));
  if nr<best[0]:best[:]=[nr,xx.copy()]
  if calls%25==1:
   trace.append(dict(H=calls,seconds=time.perf_counter()-tick,residual=nr,best=best[0],phase=phase));write(dest/'trace.json',trace);np.save(dest/'checkpoint_coordinates.npy',best[1]);np.save(dest/'checkpoint_state.npy',decode(best[1]))
   print(dest.name,calls,phase,nr,'best',best[0],flush=True)
  return v[active]
 write(dest/'protocol.json',dict(model=m.config(),tariff=tariff,start=start,start_source=str(Path(guess).name) if guess else 'Model.initial',H_budget=budget,wall_budget_seconds=600,price_elimination='Exact lambda=1 conditional MaaS fare root; retail residual remains fixed-time partial derivative',scope='Full528OD; no demand scaling; no empirical zones'))
 errors=[]
 try:
  opt=root(fun,x[active],method='hybr',options={'xtol':1e-10,'maxfev':min(1000,budget),'factor':.3});errors.append(dict(phase=phase,message=str(opt.message),success=bool(opt.success),nfev=int(opt.nfev)))
  if best[0]>1e-8:
   phase='TRF';xx=best[1];opt=least_squares(fun,np.clip(xx[active],lo[active]+1e-10,hi[active]-1e-10),bounds=(lo[active],hi[active]),xtol=1e-12,ftol=1e-12,gtol=1e-13,x_scale='jac',max_nfev=80)
   errors.append(dict(phase=phase,message=str(opt.message),success=bool(opt.success),nfev=int(opt.nfev)))
 except Budget:errors.append(dict(phase=phase,message='H_OR_WALL_BUDGET_EXHAUSTED'))
 except Exception as e:errors.append(dict(phase=phase,message=repr(e)))
 solving=False;xx=best[1].copy();yy=decode(xx);m.evaluate(yy)
 snap=(~mask)&(yy[:m.nt]-m.t0<1e-6)&(m.cap-m.last_flows>1e-3);xx[:m.nt][snap]=m.t0[snap]
 yy=decode(xx);m.evaluate(yy,True);np.save(dest/'state.npy',yy);np.save(dest/'coordinates.npy',xx)
 solver_seconds=time.perf_counter()-tick;rr=validate(m,yy,xx);rr.update(tariff=tariff,maas=maas,start=start,solver_H_calls=calls,solver_seconds=solver_seconds,total_seconds=time.perf_counter()-tick,stages=errors,config=m.config())
 write(dest/'metrics.json',rr);write(dest/'COMPLETE.json',dict(status=rr['status']));write(dest/'trace.json',trace)
 print('DONE',dest.name,rr['status'],rr['natural_direct'],rr['full_scaled'],rr['profit_pt'],flush=True);return rr
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('tariff',choices=['link','flat']);ap.add_argument('scenario',choices=['A','C']);ap.add_argument('--start',default='primary');ap.add_argument('--guess');args=ap.parse_args();solve(args.tariff,args.scenario=='C',args.start,args.guess)
