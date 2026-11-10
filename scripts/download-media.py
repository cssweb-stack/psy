"""Download only inline media referenced by the migrated PSY pages."""
import json,sys,subprocess,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'reference/migration-report.json').read_text())
def fetch(pair):
 url,dest=pair;p=ROOT/'src'/dest.lstrip('/')
 try:
  if p.exists() and p.stat().st_size:return {'source':url,'file':dest,'bytes':p.stat().st_size,'status':'downloaded'}
  data=subprocess.run(['curl','--fail','--location','--silent','--show-error','--max-time','25',url],check=True,capture_output=True).stdout
  if not data.startswith((b'\xff\xd8\xff',b'\x89PNG',b'RIFF',b'<svg',b'<?xml')):raise ValueError('Response is not a recognized image')
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  return {'source':url,'file':dest,'bytes':len(data),'status':'downloaded'}
 except Exception as e:return {'source':url,'file':dest,'status':'failed','error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(fetch,m['media'].items()))
(ROOT/'reference/media-downloads.json').write_text(json.dumps(results,indent=2)+'\n')
print('Downloaded',sum(r['status']=='downloaded' for r in results),'of',len(results),'images.')
for r in results:
 if r['status']=='failed':print(r['source'],r['error'])
if any(r['status']=='failed' for r in results):sys.exit(1)
