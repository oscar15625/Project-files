"""Independent reconstruction of reported aggregate quantities from exported OD rows."""
import run,json
from pathlib import Path
import numpy as np
records=json.loads(Path('results/v4/manifest.json').read_text()); checks=[]
for r in records:
    if r['status']!='PASS': continue
    f=Path('results/v4')/r['run']; od=np.loadtxt(f/'od_results.csv',delimiter=',',skiprows=1,ndmin=2)
    q=od[:,2]; Q=q.sum(); err={}
    err['choice_probability_sum']=float(np.max(abs(od[:,4:7].sum(axis=1)-1)))
    for col,key in [(4,'share_non'),(5,'share_drive'),(6,'share_maas')]: err[key]=float(abs(100*q@od[:,col]/Q-r[key]))
    err['traveler_welfare']=float(abs(q@od[:,7]-r['traveler_welfare']))
    pi=q@(od[:,6]*(od[:,3]-od[:,8]-od[:,9]))
    err['platform_profit']=float(abs(pi-r['profit_maas']))
    err['platform_receipts']=float(abs(q@(od[:,6]*od[:,3])-r['maas_receipts']))
    if r['maas']:
        s=od[:,6]; margin=od[:,3]-od[:,8]-od[:,9]; mu=r['config']['mode_theta']
        err['fare_stationarity']=float(np.max(abs(q*s*(1-margin*(1-s)/mu))))
        assert pi+1e-6>=r['jensen_profit_lower_bound']
    assert max(err.values())<1e-5,(r['run'],err)
    checks.append(dict(run=r['run'],errors=err))
Path('results/v4/export_verification.json').write_text(json.dumps(checks,indent=2)); print('Verified',len(checks),'accepted OD exports; maximum discrepancy',max(max(c['errors'].values()) for c in checks))
