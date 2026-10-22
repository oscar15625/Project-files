import json
from pathlib import Path
tags=[]
def paired(prefix): tags.extend([prefix+'_without',prefix+'_with'])
for name in ['sioux','small']:
    for ms,ps,total in [('node','node',0),('aggregate','node',0),('aggregate','line_node',0),('node','node',1)]: paired(f'{name}_{ms}_{ps}_total{total}')
    for family in ['common','mode']:
        for scale in [.5,.2,.1,.05,.03,.01]: paired(f'{name}_{family}_{scale:g}')
for ps,total in [('node',0),('line_node',0),('node',1)]: paired(f'small_aggregate_{ps}_total{total}_warm')
for scale in [.5,.2]: paired(f'sioux_mixed_common_{scale:g}')
for scope in ['node','aggregate']:
    for variant in ['figure_pt','figure_pt_reverse23']: paired(f'small_{scope}_{variant}')
missing=[tag for tag in tags if not (Path('results/v4')/tag/'metrics.json').exists() and not (Path('results/v4')/tag/'error.txt').exists()]
result=dict(planned_primary_trials=len(tags),finished_primary_trials=len(tags)-len(missing),unfinished=missing)
Path('results/v4/campaign_completion.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
if missing: raise SystemExit(1)
