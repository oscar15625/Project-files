"""Create append-only checkpoint/final archives; export curated files, not original history."""
from pathlib import Path
import sys,zipfile,json,hashlib,shutil,re,datetime
ROOT=Path(__file__).resolve().parent;REPRO=ROOT.parents[1]
stage=sys.argv[1];D=REPRO/'backups/pt_fare_20261124'/stage;assert not D.exists();D.mkdir(parents=True)
def sha(b):return hashlib.sha256(b).hexdigest()
selected=[]
for p in ROOT.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts:continue
 rel=p.relative_to(ROOT).as_posix()
 if rel.startswith('input/'):
  tail=rel.removeprefix('input/pt_fare_counterfactual/')
  if not (tail in ['fare_models.py','maas_cloud_study/solver.py','README.md','PT_TARIFF_COUNTERFACTUAL_REPORT_KR.md','audit.log','run.log'] or tail.startswith('results/')):continue
 if p.suffix in ['.pdf','.docx','.zip','.bundle']:continue
 selected.append(p)
inventory={};payload={}
for p in selected:
 rel=p.relative_to(ROOT).as_posix();b=p.read_bytes()
 if p.suffix in ['.py','.json','.md','.csv','.log','.txt']:
  s=b.decode('utf-8-sig')
  assert not re.search(r'ghp_[A-Za-z0-9]{20}|github_pat_[A-Za-z0-9]{20}|sk-proj-[A-Za-z0-9]{20}',s)
  s=re.sub(r'C:(?:\\+|/)Users(?:\\+|/)OSCAR','<LOCAL_USER>',s,flags=re.I)
  b=s.replace('<LOCAL_NAME>','<LOCAL_NAME>').encode('utf-8')
 inventory[rel]=dict(original_sha256=sha(p.read_bytes()),export_sha256=sha(b));payload[rel]=b
payload['EXPORT_PROVENANCE.json']=json.dumps(inventory,indent=2).encode()
payload['.gitattributes']=b'* -text\n'
manifest=dict(stage=stage,created='2026-11-24',source_commit='b682637921d843bc2edac8f154b5d03f21fa257a',original_ZIP_sha256=json.loads((ROOT/'PROVENANCE.json').read_text())['zip_sha256'],omitted='Unrelated E04/E05 cloud studies and original cloud model; pinned full-network model is provided instead.',files={n:sha(b) for n,b in payload.items()})
payload['RELEASE_MANIFEST.json']=json.dumps(manifest,indent=2).encode()
payload['SHA256SUMS.txt']=''.join(f'{sha(b)}  {n}\n' for n,b in sorted(payload.items())).encode()
archive=D/f'MaaS_PT_Fare_Local_20261124_{stage}.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in payload.items():z.writestr(n,b)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
(D/'DELIVERY.json').write_text(json.dumps(dict(stage=stage,zip=archive.name,sha256=sha(archive.read_bytes()),files=len(payload),bytes=archive.stat().st_size),indent=2))
# Additive snapshot in the existing research repository; checkpoint and final never overwrite one another.
target=REPRO/'MaaS_Codex_v6_All/research_run/pt_fare_local_20261124'/stage
assert not target.exists()
for n,b in payload.items():
 p=Path('\\\\?\\'+str((target/n).resolve())) if sys.platform=='win32' else target/n
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
print(json.dumps(dict(stage=stage,files=len(payload),archive=str(archive),sha256=sha(archive.read_bytes())),indent=2))
