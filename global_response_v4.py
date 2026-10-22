"""Use profitable deviations as additional starts, without claiming global convergence."""
import run,json
from pathlib import Path
import numpy as np
from src.model import Model
from batch_v4 import execute
from audit import audit
for source in ['sioux_common_0.2_without','sioux_mode_0.05_with','sioux_mode_0.03_with']:
    folder=Path('results/v4')/source
    if not (folder/'metrics.json').exists(): continue
    r=json.loads((folder/'metrics.json').read_text()); m=Model(**r['config']); y=np.load(folder/'state.npy')
    current='v4/'+source
    for attempt in range(1,4):
        a=audit(current)
        if a['all_retail_deviation_gains_below_1e-4']: break
        for idx,key in [(-2,'profit_mod'),(-1,'profit_pt')]:
            if a[key]['unilateral_gain']>1e-4: y[idx]=a[key]['best_tested_price']
        current=f'v4/{source}_deviation_start{attempt}'
        z,s=execute(m,current,y,maxiter=80)
        folder=Path('results')/current
        if z is not None: break
        if not (folder/'metrics.json').exists() or not s['converged']: break
        y=np.load(folder/'state.npy')
