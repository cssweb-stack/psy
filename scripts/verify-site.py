"""Check the built site's local targets, hero coverage, and faculty bio migration."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json,re,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'_site'
prefix=sys.argv[1].rstrip('/') if len(sys.argv)>1 else ''
manifest=json.loads((ROOT/'reference/migration-report.json').read_text())
shared=ROOT.parent/'css-shared/src/data/units/psy'
hero_pages=json.loads((shared/'heroes.json').read_text())['pages']
faculty_hero_pages=json.loads((shared/'faculty-heroes.json').read_text())['pages']
errors=[];files=list(OUT.rglob('*.html'))
class Scan(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set();self.words=[]
 def handle_starttag(self,t,a):
  a=dict(a)
  if 'id' in a:
   if a['id'] in self.ids:errors.append('Duplicate id '+a['id'])
   self.ids.add(a['id'])
  if t in ('a','img','script','link'):
   v=a.get('href') if t in ('a','link') else a.get('src')
   if v:self.links.append((t,v))
 def handle_data(self,d):self.words.extend(d.split())
parsed={}
for f in files:
 scan=Scan();scan.feed(f.read_text());parsed[f]=scan
 html=f.read_text()
 if len(re.findall(r'<h1\b',html))!=1:errors.append(str(f)+': expected one H1')
 rel=str(f.relative_to(OUT))
 url='/' if rel=='index.html' else '/'+rel[:-10] if rel.endswith('index.html') else '/'+rel
 assigned=hero_pages.get(url) or faculty_hero_pages.get(url)
 if not assigned or assigned['image'] not in html:errors.append(str(f)+': missing assigned hero')
 elif ('/saunders-mural/' if url in faculty_hero_pages else '/students/') not in assigned['image']:errors.append(str(f)+': incorrect hero collection')
 main=html.split('<main',1)[1].split('</main>',1)[0]
 if '<aside' in main or 'fl-builder' in main or 'gb-headline' in main:errors.append(str(f)+': legacy layout remains')
 if '{{' in html or '{%' in html:errors.append(str(f)+': unrendered template')
 for tag,value in scan.links:
  u=urlsplit(value)
  if u.scheme or u.netloc:continue
  if u.path.startswith('/'):
   if prefix and not (u.path==prefix or u.path.startswith(prefix+'/')):
    errors.append(str(f)+': missing prefix '+value);continue
   path=u.path[len(prefix):] if prefix else u.path
   target=OUT/path.lstrip('/')
  else:target=f.parent/unquote(u.path) if u.path else f
  if target.is_dir():target=target/'index.html'
  if not target.exists():errors.append(str(f.relative_to(OUT))+': missing local target '+value)
# Faculty bios must keep the complete Background-and-beyond text, without contact blocks.
ns={'wp':'http://wordpress.org/export/1.2/','c':'http://purl.org/rss/1.0/modules/content/'}
xml=next((ROOT/'reference').glob('*.xml'))
source={i.findtext('link'):i for i in ET.parse(xml).findall('./channel/item')}
faculty=[p for p in manifest['pages'] if p['destination'].startswith('/faculty/') and p['destination']!='/faculty/']
for page in faculty:
 raw=source[page['source']].findtext('c:encoded','',ns)
 raw=raw[re.search(r'<h[1-6][^>]*>\s*Background\s*</h[1-6]>',raw).start():]
 scan=Scan();scan.feed(raw)
 actual=' '.join(parsed[OUT/page['file']].words)
 expected=' '.join(scan.words)
 # Inline element boundaries may change whitespace; compare without whitespace.
 if re.sub(r'\s','',expected) not in re.sub(r'\s','',actual):errors.append(page['file']+': faculty bio differs from source')
 text=(ROOT/'src'/page['file']).read_text()
 if 'mailto:' in text or '<img' in text or 'Telephone:' in text:errors.append(page['file']+': faculty contact/profile block remains')
assert len(faculty)==21
assert len(files)==len(manifest['pages'])+1,(len(files),len(manifest['pages']))
if errors:
 print('\n'.join(sorted(set(errors))));sys.exit(1)
print(f'Checked {len(files)} pages: local links/assets, one H1, assigned student/mural heroes, no sidebars, and all 21 complete faculty bios. Prefix: {prefix or "/"}.')
