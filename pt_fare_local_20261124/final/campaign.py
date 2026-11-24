"""Resume-safe bounded campaign; skips only cases with a saved COMPLETE record."""
from extension import *
from experiment import solve
os.chdir(ROOT)
assert json.loads((ROOT/'audit/GATE.json').read_text())['status']=='PASS_MODEL_REPLAY_AND_TARIFF_INVARIANCE'
for tariff in ['link','flat']:
 for sc in ['A','C']:
  guess=f'results/link_{sc}_primary/state.npy' if tariff=='flat' else None
  solve(tariff,sc=='C',guess=guess)
write(ROOT/'campaign_status.json',dict(stage='PRIMARY_COMPLETE',remaining='two price/traffic starts for each accepted primary case'))
for tariff in ['link','flat']:
 for sc in ['A','C']:
  p=ROOT/'results'/f'{tariff}_{sc}_primary'
  if json.loads((p/'metrics.json').read_text())['status']!='STRICT_PASS':continue
  for start in ['0.8','1.2']:solve(tariff,sc=='C',start=start,guess=str(p/'state.npy'),budget=2500)
write(ROOT/'campaign_status.json',dict(stage='FINISHED',primary_cases=4,multistarts_requested=8,zone_scenario='NOT_RUN_NO_ZONE_MAP',new_grids=False))
