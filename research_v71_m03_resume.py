"""M03 only: unchanged nested numerical protocol, separate attempt, progress evidence."""
from research_v71_extra import *
import inspect

DEST=O/'m03_followup_20261110/NESTED_SAME_VI_attempt2'
def main():
    assert not (DEST/'metrics.json').exists(), 'Completed attempt must not be overwritten.'
    DEST.mkdir(parents=True,exist_ok=True)
    src=inspect.getsource(nested_worker)
    src=src.replace('def nested_worker(method):','def run_nested(method):')
    src=src.replace("dest=O/'m03_runs'/method", "dest=DEST")
    needle='tick=time.perf_counter();cpu=time.process_time()'
    src=src.replace(needle,needle+"\n    write(dest/'configuration.json',dict(method=method,config=m.config(),start='original reference with all prices multiplied by 1.03',inner_max_nfev=100,outer_max_nfev=50,outer_diff_step=1e-4,numerical_protocol='identical to original nested_worker; output and progress instrumentation only',previous_attempt='m03_runs/NESTED_SAME_VI',joint_reused='m03_runs/JOINT_AUX',original_source_sha256=digest(ROOT/'research_v71_extra.py')))" )
    src=src.replace('        return xx',"        np.save(dest/'last_inner_coordinates.npy',xx)\n        write(dest/'last_inner.json',dict(inner_solves=inners,inner_failures=inner_fail,h_calls=extra[0],pumcm_calls=graph_calls[0],seconds=time.perf_counter()-tick,prices=p.tolist(),checkpoint_scope='last completed inner solve; not a restartable scipy outer-optimizer state'))\n        print('INNER',inners,'H',extra[0],'failures',inner_fail,flush=True)\n        return xx")
    src=src.replace('    def count(self,y,details=False):extra[0]+=1;return original(self,y,details)',"    def count(self,y,details=False):\n        extra[0]+=1\n        if extra[0]%5000==0:\n            write(dest/'progress.json',dict(status='RUNNING',h_calls=extra[0],inner_solves=inners,inner_failures=inner_fail,seconds=time.perf_counter()-tick,pid=os.getpid()))\n            print('PROGRESS',extra[0],inners,flush=True)\n        return original(self,y,details)")
    (DEST/'executed_worker.py').write_text(src,encoding='utf-8')
    write(DEST/'launch.json',dict(status='RUNNING',pid=os.getpid(),scope='M03 nested only; no other experiment rerun',previous_interruption_preserved=True))
    namespace=dict(globals());exec(compile(src,str(DEST/'executed_worker.py'),'exec'),namespace)
    namespace['run_nested']('NESTED_SAME_VI')
    write(DEST/'launch.json',dict(status='FINISHED',pid=os.getpid(),result_status=read(DEST/'metrics.json')['status']))
if __name__=='__main__':main()
