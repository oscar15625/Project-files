"""Low-compute recovery: summarize completed files; never run a solver."""
from research_v71 import *
def main():
    completed=read(O/'m03_runs/JOINT_AUX/metrics.json')
    missing=dict(method='NESTED_SAME_VI',status='INTERRUPTED_NOT_COMPLETED',total_h_calls='UNKNOWN',total_pumcm_calls='UNKNOWN',inner_solves='UNKNOWN',full_scaled='nan',seconds='nan',evidence_class='NOT_COMPLETED',reason='Process ended before final metrics/state. No restart authorized in low-compute recovery.')
    assert not (O/'m03_runs/NESTED_SAME_VI/metrics.json').exists()
    outcsv('m03_same_vi_prototype.csv',[completed,missing])
    write(O/'recovery_scope.json',dict(date='2026-11-10',no_heavy_solver_launched=True,m01='27 completed attempts, 0 PASS',e03_boundary='9 PASS',m02='12 stored traffic probes',m03_joint='PASS',m03_nested='INTERRUPTED_NOT_COMPLETED',planned_light_tasks=['scalar boundary diagnostic','saved-state residual replay','report generation','artifact integrity','portable Small replay','backup and GitHub publication']))
    write(O/'m03_runs/NESTED_SAME_VI/interruption.json',dict(status='INTERRUPTED_NOT_COMPLETED',final_state_exists=False,execution_log_bytes=0,known_call_count=None,resumable_numerical_checkpoint=False,next_action='Do not run under current low-compute scope; later explicit authorization requires a separately logged fresh attempt, preserving this interruption.'))
    print('Recovery summary written; no solver executed.')
if __name__=='__main__':main()
