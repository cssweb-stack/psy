"""Rebuild PSY's reviewed content from a WordPress WXR export.
Usage: python3 scripts/migrate-wordpress.py export.xml shared-repository
The export is treated as data; scripts, styles, and page-builder layout are discarded.
"""
import sys, json, re, html, hashlib, shutil
from pathlib import Path
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(sys.argv[1]); SHARED=Path(sys.argv[2]).resolve()
NS={'wp':'http://wordpress.org/export/1.2/','content':'http://purl.org/rss/1.0/modules/content/'}
def wp(i,k):return i.findtext('wp:'+k,'',NS)
items=ET.parse(SOURCE).findall('./channel/item')
pages={wp(i,'post_name'):i for i in items if wp(i,'post_type')=='page'}
# Explicit second-pass information architecture approved against the PSY worksheet.
M={
'home':('/','Home'),
'diversity':('/diversity/','Diversity'),
'diversity-committee':('/diversity/committee.html','Diversity Committee'),
'diversity-courses':('/diversity/courses.html','Diversity Courses'),
'funding-opportunities':('/diversity/funding-opportunities.html','Funding Opportunities'),
'undergraduate':('/undergraduate/','Undergraduate Overview'),
'minor':('/undergraduate/minor.html','Minor'),
'ba-degree':('/undergraduate/major-ba.html','Major (BA)'),
'bs-degree':('/undergraduate/major-bs.html','Major (BS)'),
'hybrid-online-ba':('/undergraduate/hybrid-online-ba.html','Hybrid Online (BA)'),
'bam':('/undergraduate/psy-bam.html','BA/MA Pathway (BAM)'),
'honors-track':('/undergraduate/honors-track.html','Honors Track'),
'undergraduate-advising':('/undergraduate/advising-support.html','Advising & Support'),
'psi-chi':('/undergraduate/psi-chi.html','Psi Chi'),
'psi-sigma':('/undergraduate/psi-sigma.html','Psi Sigma'),
'student-learning-outcomes':('/undergraduate/student-learning-outcomes.html','Student Learning Outcomes'),
'research-project-summary':('/undergraduate/research-project-summary.html','Research Project Summary'),
'psy-courses':('/undergraduate/psy-courses.html','PSY Courses'),
'graduate':('/graduate/','Graduate Overview'),
'ma-degree':('/graduate/master-ma.html','Master’s (MA)'),
'phd-degree':('/graduate/doctorate-phd.html','Doctorate (PhD)'),
'graduate-program-areas':('/graduate/program-areas/','Program Areas'),
'community-cultural-developmental':('/graduate/program-areas/community-cultural-developmental.html','Community, Cultural, and Developmental'),
'cognition-neuroscience-social':('/graduate/program-areas/cognition-neuroscience-social.html','Cognition, Neuroscience, & Social'),
'psychological-clinical-science':('/graduate/program-areas/psychological-clinical-science.html','Psychological Clinical Science'),
'ccbt':('/graduate/program-areas/ccbt.html','Center for Cognitive Behavior Therapy (CCBT)'),
'graduate-students':('/graduate/current-cohort.html','Current Cohort'),
'prospective-student-information':('/graduate/prospective-students.html','Prospective Students'),
'applications-admissions':('/graduate/applications-admissions.html','Applications & Admissions'),
'standards-and-evaluations':('/graduate/standards-evaluations.html','Standards and Evaluations'),
'learning-objectives':('/graduate/learning-objectives.html','Learning Objectives'),
'give-a-gift':('/support-psy.html','Support PSY'),
'contact':('/contact.html','Contact'),
}
FACULTY=[
('Sakaria Laisene Auelua-Toomey','sakaria-laisene-auelua-toomey'),('Charlene Baker','charlene-baker'),('John (Jack) Barile','john-barile'),('Patricia Couvillon','patricia-couvillon'),('Patrick Goh','patrick-goh'),('Krista A. Haapanen','krista-a-haapanen'),('Cassandra L. Hendrix','cassandra-l-hendrix'),('I sak Kim','i-sak-kim'),('Janet Latner','janet-latner'),('Arkadiy Maksimovskiy','arkadiy-maksimovskiy'),('Akihiko Masuda','akihiko-masuda'),('Ashley Maynard','ashley-maynard'),('Christina Moyer','christina-moyer'),('Brad Nakamura','brad-nakamura'),('Anthony Papa','tony-papa'),('Santiago Papini','santiago-papini'),('Kristin Pauker','kristin-pauker'),('Joni Sasaki','joni-sasaki'),('Scott Sinnett','scott-sinnett'),('Jonas Vibell','jonas-vibell'),('Yiyuan Xu','yiyuan-xu')]
for name,slug in FACULTY:M[slug]=('/faculty/'+('anthony-papa' if slug=='tony-papa' else slug)+'.html',name)
faculty_slugs={s for _,s in FACULTY}
assert all(slug in pages for slug in M),set(M)-set(pages)
links={urlsplit(pages[s].findtext('link')).path.rstrip('/') or '/':dest for s,(dest,title) in M.items()}
links.update({'/faculty':'/faculty/','/privacy-policy':'/privacy.html','/clinical-psychology':M['psychological-clinical-science'][0],'/old-applications-admissions':M['applications-admissions'][0]})
ids={wp(i,'post_id'):links.get(urlsplit(i.findtext('link')).path.rstrip('/') or '/') for i in pages.values()}
assets={};retained=set();iframes=[]

def local_link(value):return '{{ '+repr(value)+' | url }}'
def rewrite(value):
 value=html.unescape(value.strip());u=urlsplit(value)
 if u.scheme in ('mailto','tel'):return html.escape(value,quote=True)
 if u.scheme and u.scheme not in ('https','http'):return '#'
 internal=u.hostname in ('psychology.manoa.hawaii.edu','www.psychology.manoa.hawaii.edu') or (not u.scheme and not u.netloc)
 if internal:
  if not u.path and u.fragment:return html.escape(value,quote=True)
  key=unquote(u.path).rstrip('/') or '/';dest=links.get(key)
  if key.startswith('/wp-content/uploads/') and Path(key).suffix.lower() in ('.png','.jpg','.jpeg','.webp','.svg'):
   absolute='https://psychology.manoa.hawaii.edu'+u.path
   name=hashlib.sha256(absolute.encode()).hexdigest()[:8]+'-'+re.sub(r'[^a-zA-Z0-9_.-]','-',unquote(Path(u.path).name))
   assets[absolute]='/media/content/'+name
   return local_link(assets[absolute]+('#'+u.fragment if u.fragment else ''))
  if not dest and 'page_id=' in u.query:dest=ids.get(u.query.split('page_id=')[-1].split('&')[0])
  if dest:return local_link(dest+('?' +u.query if u.query and 'page_id=' not in u.query else '')+('#'+u.fragment if u.fragment else ''))
  absolute=value if u.netloc else 'https://psychology.manoa.hawaii.edu/'+value.lstrip('/')
  retained.add(absolute);return html.escape(absolute,quote=True)
 return html.escape(value,quote=True)

class Node:
 def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
 def text(self):return ''.join(c if isinstance(c,str) else c.text() for c in self.children)
class Parser(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root]
 def handle_starttag(self,t,a):
  if t in ('p','li','tr','td','th') and self.stack[-1].tag==t:self.stack.pop()
  n=Node(t,a);self.stack[-1].children.append(n)
  if t not in {'img','br','hr','input','meta','link','source','wbr','embed','area','col','param'}:self.stack.append(n)
 def handle_startendtag(self,t,a):
  self.handle_starttag(t,a)
  if self.stack[-1].tag==t:self.stack.pop()
 def handle_endtag(self,t):
  for j in range(len(self.stack)-1,0,-1):
   if self.stack[j].tag==t:self.stack=self.stack[:j];break
 def handle_data(self,d):self.stack[-1].children.append(d)

def descendants(n,tag):
 result=[]
 for c in n.children:
  if isinstance(c,Node):
   if c.tag==tag:result.append(c)
   else:result.extend(descendants(c,tag))
 return result

def media(n):
 src=n.attrs.get('src','');alt=n.attrs.get('alt','')
 if not src:return ''
 if 'uhf_left' in src:return '<img class="img-fluid" src="'+local_link('/media/branding/logos/uhf.svg')+'" alt="University of Hawaiʻi Foundation" width="230" height="59">'
 u=urlsplit(src)
 if u.scheme not in ('https','http'):return ''
 name=unquote(Path(u.path).name);name=re.sub(r'[^a-zA-Z0-9_.-]','-',name)
 name=hashlib.sha256(src.encode()).hexdigest()[:8]+'-'+name
 dest='/media/content/'+name;assets[src]=dest
 attrs=''
 for key in ('width','height'):
  if n.attrs.get(key,'').isdigit():attrs+=' '+key+'="'+n.attrs[key]+'"'
 return '<img class="img-fluid" src="'+local_link(dest)+'" alt="'+html.escape(alt,quote=True)+'"'+attrs+' loading="lazy" decoding="async">'

allowed={'p','h1','h2','h3','h4','h5','h6','ul','ol','li','a','strong','em','sup','sub','blockquote','cite','br','hr','dl','dt','dd','address','abbr','time','figure','figcaption'}
blocks={'p','h1','h2','h3','h4','h5','h6','ul','ol','li','blockquote','dl','dt','dd','address','hr','figure','figcaption'}
drop={'script','style','svg','video','audio','source','noscript','form','input','button','meta','link'}

def table(n):
 rows=descendants(n,'tr');groups=[];headers=[];current=[]
 for row in rows:
  cells=[c for c in row.children if isinstance(c,Node) and c.tag in ('td','th')]
  if not cells:continue
  if all(c.tag=='th' for c in cells):
   if current:groups.append((headers,current));current=[]
   headers=cells
  else:current.append(cells)
 if current:groups.append((headers,current))
 result=[]
 for hs,rs in groups:
  labels=[h.text().strip() for h in hs]
  caption=''
  width=max(len(r) for r in rs)
  if len(hs)==1 and int(hs[0].attrs.get('colspan','1'))>1:
   caption='<caption>'+html.escape(labels[0])+'</caption>';labels=['Role','Name','Email'] if width==3 else ['Column '+str(k+1) for k in range(width)]
  if not labels:labels=['Column '+str(k+1) for k in range(width)]
  out='<table class="content-table content-table--responsive" role="table">'+caption+'<thead role="rowgroup"><tr role="row">'
  out+=''.join('<th scope="col" role="columnheader">'+html.escape(l)+'</th>' for l in labels)+'</tr></thead><tbody role="rowgroup">'
  for cells in rs:
   out+='<tr role="row">'
   for k,c in enumerate(cells):
    label=labels[min(k,len(labels)-1)];span=''
    for attr in ('colspan','rowspan'):
     if c.attrs.get(attr,'').isdigit():span+=' '+attr+'="'+c.attrs[attr]+'"'
    out+='<td role="cell"'+span+'><span class="content-table-label" aria-hidden="true">'+html.escape(label)+'</span><span>'+''.join(render(x) for x in c.children).strip()+'</span></td>'
   out+='</tr>'
  out+='</tbody></table>\n';result.append(out)
 return ''.join(result)

def render(n):
 if isinstance(n,str):return html.escape(n,quote=False)
 if n.tag in drop:return ''
 if n.tag=='img':return media(n)
 if n.tag=='iframe':
  src=n.attrs.get('src','');iframes.append(src)
  if src and urlsplit(src).scheme in ('https','http') and 'google.com/maps' not in src:return '<p><a href="'+html.escape(src,quote=True)+'">'+html.escape(n.attrs.get('title') or 'View embedded resource')+'</a></p>\n'
  return ''
 if n.tag=='table':return table(n)
 if n.tag in ('b','i'):n.tag={'b':'strong','i':'em'}[n.tag]
 inner=''.join(render(c) for c in n.children)
 if n.tag not in allowed:return inner
 if not inner.strip() and n.tag not in ('br','hr'):return ''
 attrs=''
 for k,v in n.attrs.items():
  if k=='href' and n.tag=='a':attrs+=' href="'+rewrite(v or '')+'"'
  elif k=='id' or (n.tag=='ol' and k=='start') or (n.tag=='abbr' and k=='title'):attrs+=' '+k+'="'+html.escape(v or '',quote=True)+'"'
 if n.tag=='a' and 'href=' not in attrs:return inner
 if n.tag in ('br','hr'):return '<'+n.tag+attrs+'>'
 return '<'+n.tag+attrs+'>'+inner.strip()+'</'+n.tag+'>'+('\n' if n.tag in blocks else '')

def normalize(text):
 # Give former standalone sidebar buttons ordinary paragraph structure.
 p=Parser();p.feed(text)
 out=[];inline=[]
 def flush():
  v=''.join(inline).strip();inline.clear()
  if v:out.append('<p>'+v+'</p>')
 for c in p.root.children:
  if isinstance(c,Node) and c.tag=='a':
   flush();out.append('<p>'+render_normal(c)+'</p>')
  elif isinstance(c,Node) and c.tag in blocks|{'table'}:
   flush();out.append(render_normal(c))
  else:inline.append(render_normal(c))
 flush()
 return '\n'.join(out)

def render_normal(n):
 if isinstance(n,str):return html.escape(n,quote=False)
 # Already-sanitized HTML only: do not run link/media rewriting a second time.
 attrs=''.join(' '+k+'="'+html.escape(v or '',quote=False).replace(chr(34),'&quot;')+'"' for k,v in n.attrs.items())
 if n.tag in ('br','hr','img'):return '<'+n.tag+attrs+'>'
 return '<'+n.tag+attrs+'>'+''.join(render_normal(c) for c in n.children)+'</'+n.tag+'>'

def clean(slug):
 raw=pages[slug].findtext('content:encoded','',NS)
 if slug in faculty_slugs:
  m=re.search(r'<h[1-6][^>]*>\s*Background\s*</h[1-6]>',raw,re.I)
  if not m:raise ValueError('Missing faculty bio boundary: '+slug)
  raw=raw[m.start():]
 p=Parser();p.feed(raw);text=render(p.root)
 text=re.sub(r'\n\s*\n','\n',text)
 # Preserve Nunjucks expressions through a second HTML parse.
 return normalize(text)

# Clean scaffold pages first so old placeholder paths cannot survive.
for p in (ROOT/'src').rglob('*.html'):p.unlink()
report=[];bodies={s:clean(s) for s in M}

def linked_list(entries):
 return '<ul>\n'+''.join('<li><a href="'+local_link(url)+'">'+html.escape(label)+'</a></li>\n' for label,url in entries)+'</ul>\n'

def append_links(body,heading,entries):
 # Only add destinations not already preserved from WordPress sidebars.
 missing=[(label,url) for label,url in entries if repr(url) not in html.unescape(body)]
 return body+ ('\n<h2>'+html.escape(heading)+'</h2>\n'+linked_list(missing) if missing else '')

# Move the broad program introductions to Why Study PSY, as requested during review.
overview_intros={}
for slug in ('undergraduate','graduate'):
 body=bodies[slug];m=re.search(r'<h1\b[^>]*>.*?</h1>',body,re.S)
 tail=body[m.end():] if m else body
 intro=[]
 while True:
  m=re.match(r'\s*(<p\b[^>]*>.*?</p>)',tail,re.S)
  if not m:break
  # The first link-only paragraph begins the old sidebar; leave it on Overview.
  plain=re.sub(r'<[^>]+>','',m[1]).strip()
  if re.fullmatch(r'<p>\s*<a\b.*?</a>\s*</p>',m[1],re.S):break
  intro.append(m[1]);tail=tail[m.end():]
 overview_intros[slug]='\n'.join(intro)
 bodies[slug]='<h1>'+('Undergraduate Overview' if slug=='undergraduate' else 'Graduate Overview')+'</h1>\n'+('<p class="intro">Explore psychology degrees, academic requirements, and resources for undergraduate students.</p>' if slug=='undergraduate' else '<p class="intro">Explore graduate study, program areas, academic requirements, and application resources in psychology.</p>')+'\n'+tail

why='<h1>Why Study PSY</h1>\n<h2>Undergraduate Study</h2>\n'+overview_intros['undergraduate']+'\n<h2>Graduate Study</h2>\n'+overview_intros['graduate']
why=append_links(why,'Explore Our Programs',[('Undergraduate Overview','/undergraduate/'),('Graduate Overview','/graduate/')])

honors=[('Psi Chi','/undergraduate/psi-chi.html'),('Psi Sigma','/undergraduate/psi-sigma.html')]
for slug in ('undergraduate','undergraduate-advising','minor','ba-degree','bs-degree'):
 bodies[slug]=append_links(bodies[slug],'Honor Societies',honors)
bodies['undergraduate']=append_links(bodies['undergraduate'],'Undergraduate Resources',[(M[s][1],M[s][0]) for s in ['student-learning-outcomes','research-project-summary','psy-courses']])
for slug in ('ba-degree','bs-degree'):
 bodies[slug]=append_links(bodies[slug],'Academic Resources',[(M[s][1],M[s][0]) for s in ['student-learning-outcomes','psy-courses']])
bodies['bs-degree']=append_links(bodies['bs-degree'],'Research Requirements',[(M['research-project-summary'][1],M['research-project-summary'][0])])
bodies['graduate']=append_links(bodies['graduate'],'Graduate Resources',[(M[s][1],M[s][0]) for s in ['standards-and-evaluations','learning-objectives','graduate-program-areas']])
bodies['graduate-program-areas']=append_links(bodies['graduate-program-areas'],'Clinical Training',[(M['ccbt'][1],M['ccbt'][0])])

# Contact uses the maintained shared building/contact block rather than the old map.
contact=bodies['contact'];heading=re.search(r'<h1.*?</h1>',contact,re.S)[0]
intro=re.search(r'<p>.*?</p>',contact,re.S)[0]
idx=contact.find('<table')
extra='<p>All inquiries regarding undergraduate study should be directed to <a href="mailto:psyadv@hawaii.edu">psyadv@hawaii.edu</a>.</p>\n<p>All inquiries regarding graduate study should be directed to <a href="mailto:gradpsy@hawaii.edu">gradpsy@hawaii.edu</a>.</p>'
office='''{% set building = common.buildings[site.building] %}
<h2>Main Office</h2>
<address>{% for line in site.address %}{{ line | escape }}{% if not loop.last %}<br>{% endif %}{% endfor %}</address>
<p>Telephone: <a href="{{ site.phone.href | escape }}">{{ site.phone.label | escape }}</a><br>Fax: (808) 956-4700<br>Email: <a href="{{ site.email.href | escape }}">{{ site.email.label | escape }}</a></p>
{% if building.mapEmbedUrl %}<iframe class="map-embed" title="Google Map showing Sakamaki Hall at UH Mānoa" src="{{ building.mapEmbedUrl | escape }}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>{% endif %}'''
bodies['contact']=heading+'\n'+intro+'\n'+office+'\n'+extra+'\n'+contact[idx:]

def section(body,gray=False):
 return '<div class="page-section'+(' page-section--gray' if gray else '')+'">\n<div class="container content-section">\n<div class="row gx-0 gx-sm-5 gx-lg-5">\n<div class="col-12">\n'+body.strip()+'\n</div>\n</div>\n</div>\n</div>\n'

def sections(body):
 # Tables receive the shared full-width gray treatment; surrounding prose stays white.
 pieces=re.split(r'(<table\b.*?</table>)',body,flags=re.S);out='';pending='';tabletext=''
 for piece in pieces:
  if piece.startswith('<table'):
   heading=''
   match=re.search(r'(<h([2-6])\b[^>]*>(?:(?!</h\2>).)*</h\2>)\s*$',pending,re.S)
   if match:
    heading=match[1]+'\n';pending=pending[:match.start()]
   if pending.strip():out+=section(pending)
   pending='';tabletext+=heading
   tabletext+=piece+'\n'
  else:
   if tabletext and piece.strip():out+=section(tabletext,True);tabletext=''
   pending+=piece
 if tabletext:out+=section(tabletext,True)
 if pending.strip():out+=section(pending)
 return out

all_urls=[]
def write(url,title,body,source=None):
 rel='index.html' if url=='/' else url.lstrip('/')+('index.html' if url.endswith('/') else '')
 p=ROOT/'src'/rel;p.parent.mkdir(parents=True,exist_ok=True)
 # Shared prose styling owns headings and list rhythm; strip presentation-only bold/italics.
 body=re.sub(r'</?(?:strong|em)>','',body)
 if '<h1' not in body:body='<h1>'+html.escape(title)+'</h1>\n'+body
 body=re.sub(r'(<h1\b[^>]*>.*?</h1>\s*)<p>',r'\1<p class="intro">',body,count=1,flags=re.S)
 p.write_text('---\nlayout: shell.njk\ntitle: '+json.dumps(title,ensure_ascii=False)+'\npermalink: '+json.dumps(url)+'\n---\n'+sections(body))
 all_urls.append(url)
 report.append({'source':source,'destination':url,'file':rel,'title':title})

for slug,(url,title) in M.items():write(url,title,bodies[slug],pages[slug].findtext('link'))
write('/about-psy/why-study-psy.html','Why Study PSY',why,'Undergraduate and Graduate overview introductions')
write('/faculty/','Faculty','<h1>Faculty</h1>\n'+linked_list([(name,M[slug][0]) for name,slug in FACULTY]),pages['faculty'].findtext('link'))
write('/courses.html','Courses','<h1>Courses</h1>\n<p class="intro">Find psychology class availability, course descriptions, and catalog information.</p>\n<p>For guidance on advanced topics, research, and practicum credits, see <a href="'+local_link('/undergraduate/psy-courses.html')+'">PSY Courses</a>.</p>\n{% include "layouts/content/course-resources.njk" %}')

placeholder='/media/heroes/saunders-mural/01.webp'
hero={'image':placeholder,'position':'center center','alt':'Temporary hero: detail of the Saunders Hall mural','credit':False}
(SHARED/'src/data/units/psy/heroes.json').write_text(json.dumps({'defaultHero':placeholder,'pages':{u:hero for u in all_urls+['/privacy.html']}},indent=2)+'\n')
(SHARED/'src/data/units/psy/catalog-courses.json').write_text(json.dumps({'prefix':'PSY','catalog':{'label':'UH Mānoa Catalog (PSY)','url':'https://manoa.hawaii.edu/catalog/category/social-sciences/psy/'}},indent=2)+'\n')
reference=ROOT/'reference';reference.mkdir(exist_ok=True)
shutil.copyfile(SOURCE,reference/SOURCE.name)
leftovers=[{'title':i.findtext('title'),'slug':s,'status':wp(i,'status'),'source':i.findtext('link')} for s,i in pages.items() if s not in M and s not in ('faculty','privacy-policy')]
manifest={'source':SOURCE.name,'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'sourcePageCount':len(pages),'pages':report,'facultyCount':len(FACULTY),'leftovers':leftovers,'sharedPrivacyReplaces':pages['privacy-policy'].findtext('link'),'media':assets,'retainedLegacyLinks':sorted(retained),'embedsConvertedToLinks':sorted(set(iframes)),'overviewContentMovedTo':'/about-psy/why-study-psy.html'}
(reference/'migration-report.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Created',len(report),'content pages,',len(FACULTY),'faculty bios;',len(leftovers),'leftovers;',len(assets),'inline assets.')
