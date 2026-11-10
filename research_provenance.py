"""Archive the phase-start runner code separately from mid-run backup commits."""
from research_experiments import *
records=[]
for phase in ['E01','E03_pilot','E03_coarse']:
    items=cases(phase); path=folder(phase,items[0][0])/'configuration.json'
    if not path.exists(): continue
    first=json.loads(path.read_text()); commit=first['git_sha']
    raw=subprocess.check_output(['git','show',commit+':research_experiments.py'])
    dest=OUT/'provenance'/(phase+'_executed_runner.py'); dest.parent.mkdir(exist_ok=True); dest.write_bytes(raw)
    records.append(dict(phase=phase,phase_start_commit=commit,runner_sha256=hashlib.sha256(raw).hexdigest(),runner_archive=str(dest.relative_to(ROOT)),note='Python imported the runner at phase start. Per-case git_sha can advance with local backup commits; economic model and solver sources were unchanged. Later runner changes concern restart handling only.'))
raw=Path(__file__).with_name('research_experiments.py').read_bytes()
dest=OUT/'provenance/E03_coarse_resumed_20261108_runner.py'; dest.write_bytes(raw)
records.append(dict(phase='E03_coarse_resume',date='2026-11-08',runner_sha256=hashlib.sha256(raw).hexdigest(),runner_archive=str(dest.relative_to(ROOT)),note='Recovery-enhanced runner used for the final MoD=3.5 row. Economic model and numerical rules unchanged; original configuration metadata retained.'))
write(OUT/'execution_provenance.json',records)
print('Archived runner versions for',len(records),'phases')
