#!/usr/bin/env python3
"""Rebuild 19 editable native slides and a standalone PDF on macOS.

Requires Keynote 14.4+, Pillow and the committed relative source figures/media.
Run from any directory. Existing outputs are never overwritten. For a new export,
copy this package into a fresh versioned submission folder and update output names.
No source WSI, embedding, model, GPU job or final-test data is opened.

The required artifact-tool runtime is absent. The user-required standalone export
uses native Keynote authoring/export as an approved fallback, with native editable
text, tables and line chart. Structural validators and visual PDF QA are separate.
"""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BUILD=ROOT/'results/submission'/HERE.name
DARK='#173042';TEAL='#116D77';GRAY='#586674'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def text(s,x,y,w,h,size=26,bold=False,color=DARK):return dict(kind='text',text=s,x=x,y=y,w=w,h=h,size=size,bold=bold,color=color)

def astr(s):return '"'+str(s).replace('\\','\\\\').replace('"','\\"')+'"'
def alist(v):return '{'+', '.join(alist(x) if isinstance(x,list) else astr(x) if isinstance(x,str) else str(x) for x in v)+'}'
def rgb(c):return '{'+', '.join(str(int(c[i:i+2],16)*257) for i in (1,3,5))+'}'
def build():
    BUILD.mkdir(parents=True,exist_ok=True)
    slides=json.loads((HERE/'slide_content.json').read_text())
    (HERE/'slide_content.json').write_text(json.dumps(slides,ensure_ascii=False,indent=2)+'\n')
    code=['tell application "Keynote"','set d to make new document with properties {document theme:theme "Basic White", width:1280, height:720}','tell d','set base slide of slide 1 to master slide "Blank"']
    assets=[]
    for n,s in enumerate(slides,1):
        if n>1:code.append('make new slide with properties {base slide:master slide "Blank"}')
        code+=['tell slide '+str(n)]
        title_size=58 if n==1 else 36
        objects=[text(s['title'],70,65,1140,85,title_size,True)]+s['objects']+[text(f'{n:02d}',1200,680,45,25,15,False,GRAY)]
        for i,o in enumerate(objects):
            ident=f'o{n}_{i}'
            props=f'position:{{{o["x"]},{o["y"]}}}, width:{o["w"]}, height:{o["h"]}'
            if o['kind']=='text':
                code += [f'set {ident} to make new text item with properties {{object text:{astr(o["text"])}, {props}}}',f'set font of object text of {ident} to {astr("Arial-BoldMT" if o["bold"] else "ArialMT")}',f'set size of object text of {ident} to {o["size"]}',f'set color of object text of {ident} to {rgb(o["color"])}']
            elif o['kind']=='image':
                p=ROOT/o['path'];assets.append(dict(path=o['path'],sha256=sha(p),used_on_slide=n,transformation='Embedded source bytes unchanged; fit inside specified rectangle'))
                # Resize in source aspect ratio, then center within layout box.
                from PIL import Image
                sw,sh=Image.open(p).size;scale=min(o['w']/sw,o['h']/sh);w=int(sw*scale);h=int(sh*scale);x=o['x']+(o['w']-w)//2;y=o['y']+(o['h']-h)//2
                code += [f'set {ident} to make new image with properties {{file:POSIX file {astr(p)},position:{{{x},{y}}},width:{w},height:{h},description:{astr(p.name)}}}']
            elif o['kind']=='table':
                rows=o['rows'];nr=len(rows);nc=len(rows[0]);widths=o['widths'] or [o['w']//nc]*nc
                code += [f'set {ident} to make new table with properties {{row count:{nr},column count:{nc},header row count:1,header column count:0,{props}}}',f'tell {ident}',f'set font name of cell range to "ArialMT"',f'set font size of cell range to {o["size"]}',f'set text color of cell range to {rgb(DARK)}',f'set text wrap of cell range to true',f'set background color of cell range to {{65535,65535,65535}}']
                for c,w in enumerate(widths,1):code.append(f'set width of column {c} to {w}')
                for r,row in enumerate(rows,1):
                    code.append(f'set height of row {r} to {o["h"]//nr}')
                    for c,value in enumerate(row,1):code.append(f'set value of cell "{chr(64+c)}{r}" to {astr(value)}')
                code += [f'set background color of row 1 to {rgb(TEAL)}','set text color of row 1 to {65535,65535,65535}','set font name of row 1 to "Arial-BoldMT"','end tell']
            elif o['kind']=='chart':
                code += [f'add chart row names {alist(o["row_names"])} column names {alist(o["column_names"])} data {alist(o["data"])} type line_2d group by chart row',f'set position of chart 1 to {{{o["x"]},{o["y"]}}}',f'set width of chart 1 to {o["w"]}',f'set height of chart 1 to {o["h"]}']
        code += ['set presenter notes to '+astr(s['notes']+'\n\nSources and disclosures:\n'+s['source']),'end tell']
    pptx=HERE/'floater_finder_ashby_v2_final.pptx';pdf=HERE/'floater_finder_ashby_v2_final.pdf'
    if pptx.exists() or pdf.exists():raise FileExistsError('Use a new version directory to preserve outputs')
    code += ['end tell',f'save d in POSIX file {astr(BUILD/"floater_finder_ashby_v2_final.key")}',f'export d to POSIX file {astr(pptx)} as Microsoft PowerPoint',f'export d to POSIX file {astr(pdf)} as PDF with properties {{PDF image quality:Best}}','end tell']
    script=BUILD/'build.applescript';script.write_text('\n'.join(code)+'\n')
    (HERE/'media_manifest.json').write_text(json.dumps(dict(original_evidence_commits={'S1_v1':'06c7b771399c26b9dbc390b7e4bd73b077878e95','S2':'35e0a8dae57e22808420b45ae040fc2f8c3710a5','v2':'668d9b8c4e3e8aa300bda6ff15e416c601c2e024'},source_kind='real training/calibration outputs; no held-out predictions',assets=assets,figure_source_records=['reports/panda_presentation_figure_manifest_v1.json','reports/figures/panda_piece_development_23065744/provenance.json'],microscopy_provenance='media/provenance.json'),indent=2)+'\n')
    subprocess.run(['osascript',str(script)],check=True,timeout=240)
    print(json.dumps(dict(pptx=str(pptx),pdf=str(pdf),slides=len(slides),script_seconds=sum(s['seconds'] for s in slides))))

if __name__=='__main__':build()
