#!/usr/bin/env python3
"""Verify submission source identities, reported endpoints and native PPTX data.

Read-only. Does not open embeddings, WSI, test labels or run predictions.
Visual and native-app round-trip checks remain separate from these assertions.
"""
from pathlib import Path
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
    manifest=json.loads((HERE/'evidence_manifest.json').read_text())
    for path,expected in manifest['source_files_sha256'].items():
        assert sha(ROOT/path)==expected, f'Evidence changed: {path}'
    for r in read(HERE.relative_to(ROOT)/'media/provenance.json'):
        assert sha(ROOT/r['path'])==r['sha256']
        if 'source_sha256' in r:assert sha(ROOT/r['source_path'])==r['source_sha256']
    spec=json.loads((HERE/'slide_content.json').read_text());assert len(spec)==19
    assert sum(s['seconds'] for s in spec)==480
    words=sum(len(s['notes'].split()) for s in spec if s['seconds']);assert 900<=words<=1050
    baseline=read('reports/panda_clean_baseline_23055022.json')['metrics']['calibration/benign_cancer/top5pct']
    assert baseline['confusion_rows_truth_columns_prediction']==[[5,3],[1,15]] and baseline['slides']==24
    s1=read('reports/panda_s1_summary_23065666.json')
    assert (s1['trials'],s1['distinct_host_slides'],s1['distinct_donor_slides'])==(192,32,21)
    v1=read('reports/panda_review_selection_v1.json');assert v1['operating_point_supported'] is False
    for method,hits,alerts in [('combined',0,0),('visual_only',0,0),('decision_only',8,4),('spatial_only',32,19)]:
        m=v1['comparison'][method]['calibration']
        assert round(m['fragment_recall']*m['positive_trials'])==hits and m['unmodified_alerts']==alerts
    s2=read('reports/panda_s2_development_v1/summary.json')
    assert (s2['trials'],s2['oracle_exact_passes'],s2['distinct_host_slides'],s2['distinct_donor_slides'],s2['exclusions'])==(760,760,32,37,8)
    assert s2['test_slides_scored'] is False and s2['primary_pooling']=='mean'
    a=read('reports/panda_s2_development_v1/analysis.json')
    rows=[r for r in a['per_dose_uncertainty'] if r['split']=='calibration' and r['condition']=='high_gp45' and r['pooling']=='mean']
    assert len(rows)==6 and all(r['originally_correct_low_hosts']==8 and r['newly_induced_low_to_high_errors']==0 for r in rows)
    v2=read('reports/panda_review_v2_results.json');assert v2['operating_point_supported'] is False
    assert v2['final_test_slides_scored'] is False and v2['final_test_predictions_authorized'] is False
    m=v2['methods']['combined_rank']['splits']['calibration']['metrics'];assert m['fragment_recall']==0 and m['unmodified_alerts']==1 and m['clean_hypothetical_damage']==0
    pptx=HERE/'floater_finder_ashby_v2_final.pptx';ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
    with ZipFile(pptx) as z:
        slides=[n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)]
        charts=[n for n in z.namelist() if re.fullmatch(r'ppt/charts/chart\d+\.xml',n)]
        tables=sum(z.read(n).count(b'<a:tbl>') for n in slides)
        assert len(slides)==19 and len(charts)==1 and tables==4
        for n in z.namelist():
            if n.endswith('.rels'):
                for rel in ET.fromstring(z.read(n)):
                    assert not (rel.attrib.get('TargetMode')=='External' and rel.attrib['Type'].endswith(('/image','/video','/audio'))),'Linked external media'
        chart=ET.fromstring(z.read(charts[0]));actual={}
        for series in chart.findall('.//c:ser',ns):
            name=series.find('.//c:tx//c:v',ns).text
            actual[name]=[float(v.text) for v in series.findall('.//c:val//c:v',ns)]
        expected=next(o for o in spec[6]['objects'] if o['kind']=='chart')
        assert actual==dict(zip(expected['row_names'],expected['data']))
        for i,s in enumerate(spec,1):
            notes=ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml'))
            rendered=' '.join(n.text or '' for n in notes.findall('.//a:t',ns))
            assert ' '.join(s['notes'].split()) in ' '.join(rendered.split()),f'Script mismatch on slide{i}'
    info=subprocess.check_output(['pdfinfo',str(HERE/'floater_finder_ashby_v2_final.pdf')],text=True)
    assert re.search(r'Pages:\s+19\b',info)
    print(json.dumps(dict(status='pass',source_files_verified=len(manifest['source_files_sha256']),slides=19,native_tables=tables,native_charts=1,linked_external_media=0,spoken_words=words,seconds=480,held_out_predictions_computed=False)))
if __name__=='__main__':main()
