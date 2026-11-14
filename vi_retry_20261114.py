"""Registered initialization sensitivity for the preserved B lambda .65 failure."""
from vi_robust_20261114 import *
def main():
    assert read(P/'campaign_status.json')['status']=='FINISHED'
    original=read(P/'runs/B_lambda0.65_SCORE_1/metrics.json');assert not original['strict_original_time_pass']
    write(P/'fallback_protocol.json',dict(case='B_lambda0.65',factors=[.95,1.05],reason='Original start exhausted 8000 solver H with failed traffic complementarity; preserved unchanged.',h_budget_per_attempt=8000,solver_settings_unchanged=True,no_equilibrium_warm_start=True))
    cfg=read(P/'cloud_reference/B_lambda0.65/config.json')
    for f in [.95,1.05]:
        dest=P/'runs'/f'B_lambda0.65_SCORE_{f:g}';dest.mkdir(parents=True,exist_ok=True)
        write(dest/'job.json',dict(label='B_lambda0.65',cfg=cfg,factor=f,score='SCORE'))
        if (dest/'COMPLETE.json').exists():continue
        with (dest/'execution.log').open('a',encoding='utf-8') as log:run=subprocess.run([sys.executable,str(ROOT/'vi_robust_20261114.py'),'worker',str(dest/'job.json')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        assert run.returncode==0
        r=read(dest/'metrics.json');print(f,r['status'],r['strict_original_time_pass'],r['solver_h_calls'],flush=True)
    write(P/'fallback_status.json',dict(status='FINISHED',attempts=2))
if __name__=='__main__':main()
