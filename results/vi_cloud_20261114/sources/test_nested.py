"""Numerical and regression checks for nested root; no optimizer."""
import sys, pathlib, json
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from nested_extension import NestedModel, nested_root
from src.model import Model
BASE=pathlib.Path(__file__).resolve().parent.parent/'base'

def test():
 out=[]
 vals=np.array([[-3.,-2.,-4.],[-1.,-.5,-.25],[-4.,-5.,-2.]])
 for lam in [1.,.9,.7,.5]:
  s,v,j,g=nested_root(vals,['non','drive','maas'],mu=1.,lam=lam)
  assert np.max(abs(s.sum(axis=1)-1))<1e-14
  if lam==1:
   from scipy.special import logsumexp
   assert np.allclose(v,logsumexp(vals,axis=1),atol=1e-13)
  eps=1e-6
  vplus=vals.copy();vplus[:,0]+=eps
  vminus=vals.copy();vminus[:,0]-=eps
  fp=nested_root(vplus,['non','drive','maas'],mu=1.,lam=lam)[0]
  fm=nested_root(vminus,['non','drive','maas'],mu=1.,lam=lam)[0]
  assert np.max(abs((fp-fm)/(2*eps)-j))<5e-9,(lam,np.max(abs((fp-fm)/(2*eps)-j)))
  vplus=vals.copy();vplus[:,2]+=eps
  vminus=vals.copy();vminus[:,2]-=eps
  fp=nested_root(vplus,['non','drive','maas'],mu=1.,lam=lam)[0][:,2]
  fm=nested_root(vminus,['non','drive','maas'],mu=1.,lam=lam)[0][:,2]
  assert np.max(abs((fp-fm)/(2*eps)-g))<5e-9
  out.append(dict(check='kernel_probability_and_derivative',lambda_value=lam,status='PASS'))
 for scenario in ['A','B','C']:
  p=BASE/'representative_results'/f'{scenario}_reference';r=json.loads((p/'metrics.json').read_text());y=np.load(p/'state.npy',allow_pickle=False)
  m=Model(**r['config']);mn=NestedModel(**r['config'],nest_lambda=1.)
  h,or_=m.evaluate(y);hn,nr=mn.evaluate(y)
  maxh=float(np.max(abs(h-hn))); maxmetrics=max(abs(or_[k]-nr[k]) for k in or_ if k in nr)
  assert maxh<1e-8 and maxmetrics<1e-8,(scenario,maxh,maxmetrics)
  out.append(dict(check='mnl_nested_regression',scenario=scenario,max_h_error=maxh,max_metric_error=maxmetrics,status='PASS'))
 # Without MaaS the nest contains one product and must be invariant to lambda.
 ap=BASE/'representative_results/A_reference'; ar=json.loads((ap/'metrics.json').read_text()); ay=np.load(ap/'state.npy')
 am=Model(**ar['config']); ah,ae=am.evaluate(ay)
 for lam in [1.,.85,.75,.65,.55]:
  mm=NestedModel(**ar['config'],nest_lambda=lam);hh,ee=mm.evaluate(ay)
  err=max(float(np.max(abs(hh-ah))), max(abs(ee[k]-ae[k]) for k in ae if k in ee))
  assert err <1e-8,(lam,err)
  out.append(dict(check='no_maas_baseline_lambda_invariance',lambda_value=lam,max_error=err,status='PASS'))
 # check profit gradients at frozen t, fixed others, all leaders, at multiple lambda.
 for scenario in ['B','C']:
  r=json.loads((BASE/'representative_results'/f'{scenario}_reference'/'metrics.json').read_text());y=np.load(BASE/'representative_results'/f'{scenario}_reference'/'state.npy')
  for lam in [1.,.85,.65]:
   m=NestedModel(**r['config'],nest_lambda=lam);h,o=m.evaluate(y);errors=[];eps=1e-5
   for k in [m.nt, m.nt+1, m.nt+m.nod-1, len(y)-2, len(y)-1]:
    yp=y.copy();ym=y.copy();yp[k]+=eps;ym[k]-=eps
    op=m.evaluate(yp)[1];om=m.evaluate(ym)[1]
    label='profit_maas' if k<len(y)-2 else 'profit_mod' if k==len(y)-2 else 'profit_pt'
    fd=(op[label]-om[label])/(2*eps)
    errors.append(abs(fd+h[k]))
   maxerr=float(max(errors)); assert maxerr <1e-5,(scenario,lam,maxerr,errors)
   out.append(dict(check='finite_difference_profit_gradients',scenario=scenario,lambda_value=lam,max_error=maxerr,status='PASS'))
 return out

if __name__=='__main__':
 out=test();dest=pathlib.Path(__file__).resolve().parent/'kernel_validation.json';dest.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
