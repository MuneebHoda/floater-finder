"""Artificial colored PNG fixtures only, including simulated real-input trust markers."""
from copy import deepcopy
import csv
from html.parser import HTMLParser
import json
from pathlib import Path
import pytest
from PIL import Image

from floater_finder.artifacts import Slide
from floater_finder.experiments import file_sha256
from floater_finder.review_previews import select_examples, attach_previews, render_preview_html
from floater_finder.review_report import build_report, evidence_from_case
from floater_finder.research import preview_export as export
from floater_finder.research.contracts import ExperimentRun,canonical
from floater_finder.research.registry import Registry
from floater_finder.research.context_safety import read_sealed
from floater_finder.detectors.context_eligibility import assess_context
from test_review_report import fixture

PROJECT=Path(__file__).resolve().parents[1]
CONFIG=PROJECT/'configs/panda_preview_export_v1.json'


def inputs(root,sid='a'*32):
    root.mkdir();case,t,s,p=fixture();case['host_id']=t['host_id']=s['host_id']=sid
    report=build_report(evidence_from_case(case),t,s,p);report['provenance']['checkpoint_sha256']='fixture-checkpoint'
    rows=[];hashes={}
    for i in range(4):
        path=root/f'tile-{i}.png';Image.new('RGB',(16,16),(i*50,20,60)).save(path)
        rows.append(dict(tile_id=f'tile-{i}',path=path.name,image_id=sid,x=i*100.,y=0.,area_mm2=.01))
        hashes[f'tile-{i}']=file_sha256(path)
    metadata=dict(slide_id=sid,source_kind='fixture',cohort_split='train',coordinate_units='microns',
        coordinate_reference='tile_top_left',microns_per_unit=1,tile_size=[100.,100.],export_pixels=16,
        project='PANDA',data_provider='radboud',extraction=dict(sampling_mode='representative',selection_uses_mask=False))
    return report,rows,metadata,hashes


def test_selector_is_deterministic_geometry_only_and_bounded():
    xy=[(float(i),float(i%3)) for i in range(10)]
    assert select_examples(set(range(10)),xy)==[0,3,6,9]
    assert select_examples([9,1,7,3,5],xy)==[1,3,5,9]
    assert select_examples([],xy)==[] and select_examples([4],xy)==[4]


def test_exact_png_bytes_physical_geometry_and_saved_predictions_are_preserved(tmp_path):
    source=tmp_path/'source';r,rows,m,hashes=inputs(source);before=deepcopy(r);out=tmp_path/'tiles';out.mkdir()
    upgraded,assets=attach_previews(r,rows,m,hashes,source,out,1024*1024)
    assert r==before and len(assets)==4
    for name,a in assets.items():assert (out/Path(name).name).read_bytes()==Path(a['source_path']).read_bytes()
    assert upgraded['baseline']==r['baseline'] and upgraded['review_alert'] is upgraded['foreignness'] is None
    assert upgraded['components'][0]['decision_change'] is True and upgraded['components'][0]['context']==r['components'][0]['context']
    assert upgraded['components'][0]['previews']['component'][1]['x_um']==100.
    assert upgraded['components'][0]['previews']['outside'][0]['tile_index']==2
    assert upgraded['components'][0]['previews']['component'][0]['field_um_xy']==[100.,100.]
    assert 'annotation' not in canonical(upgraded) and not upgraded['preview_policy']['spatial_reconstruction']


@pytest.mark.parametrize('damage',['hash','path','symlink','shape','scale','duplicate','budget'])
def test_invalid_image_identity_geometry_or_budget_fails_without_overwriting(tmp_path,damage):
    source=tmp_path/'source';r,rows,m,h=inputs(source);out=tmp_path/'tiles';out.mkdir();limit=1024*1024
    if damage=='hash':h['tile-0']='0'*64
    elif damage=='path':rows[0]['path']='../escape.png'
    elif damage=='symlink':
        escaped=tmp_path/'other.png';escaped.write_bytes((source/'tile-0.png').read_bytes());(source/'tile-0.png').unlink();(source/'tile-0.png').symlink_to(escaped)
    elif damage=='shape':m['export_pixels']=32
    elif damage=='scale':m['tile_size']=[112.,112.]
    elif damage=='duplicate':r['components'][1]['tile_indices']=[0,1]
    else:limit=0
    with pytest.raises(ValueError):attach_previews(r,rows,m,h,source,out,limit)
    assert not list(out.iterdir())


def test_unknown_mapping_and_empty_context_remain_visible_without_false_images(tmp_path):
    source=tmp_path/'source';r,rows,m,h=inputs(source);r['components']=r['components'][:1]
    out=tmp_path/'tiles';out.mkdir();up,_=attach_previews(r,rows,m,h,source,out,1024*1024)
    assert all(t['rgb_assignment']=='unknown' for t in up['components'][0]['previews']['outside'])
    page=render_preview_html(up);assert 'RGB assignment unknown' in page and 'not a spatial reconstruction' in page
    r['components'][0].update(tile_indices=[0,1,2,3],tile_count=4,occupied_tile_area_mm2=.04,
        decision_change=None,signed_cancer_margin_influence=None,context=assess_context(4,4,None),
        counterfactual=dict(status='not_evaluable_empty_exclusion',remaining_tile_count=0,result=None))
    out2=tmp_path/'tiles2';out2.mkdir();up,_=attach_previews(r,rows,m,h,source,out2,1024*1024)
    assert up['components'][0]['previews']['outside']==[]
    assert 'No saved outside tiles' in render_preview_html(up)


def test_html_only_uses_bound_local_pngs_and_rejects_asset_injection(tmp_path):
    source=tmp_path/'source';r,rows,m,h=inputs(source);out=tmp_path/'tiles';out.mkdir()
    up,assets=attach_previews(r,rows,m,h,source,out,1024*1024)
    class Images(HTMLParser):
        def __init__(self):super().__init__();self.sources=[]
        def handle_starttag(self,tag,attrs):
            if tag=='img':self.sources.extend(v for k,v in attrs if k=='src')
    parser=Images();parser.feed(render_preview_html(up));assert len(parser.sources)==8
    assert all(s.startswith('../tiles/') and s[3:] in assets for s in parser.sources)
    up['components'][0]['previews']['component'][0]['asset_path']='https://example.com/track.png'
    with pytest.raises(ValueError,match='Safe local'):render_preview_html(up)


def test_preflight_cpu_gate_and_no_slide_array_reads(monkeypatch,tmp_path):
    monkeypatch.setattr(Slide,'load',lambda *a,**k:pytest.fail('No NPZ or new inference allowed'))
    c=export.preflight(CONFIG,file_sha256(CONFIG),PROJECT);assert c['maximum_tile_references']==3112
    c['split']='test';p=tmp_path/'bad.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='training-only'):export.preflight(p,file_sha256(p),PROJECT)
    with pytest.raises(RuntimeError,match='CPU Slurm'):export.run(*([None]*5),execute=False)


def test_complete_72_slide_artificial_export_checks_receipts_and_seals_every_png(tmp_path,monkeypatch):
    c=json.loads(CONFIG.read_text());ids=[f'{i:032x}' for i in range(72)];paths=[];verified=[];oldroot=tmp_path/'old';encoded=tmp_path/'encoded'
    manifest=tmp_path/'manifest.csv'
    with manifest.open('w',newline='') as f:w=csv.writer(f);w.writerow(['image_id','split']);w.writerows((sid,'train') for sid in ids);w.writerow(['sealed-test','test'])
    old=Registry(oldroot,ExperimentRun('panda_dependence_export_v1','fixture software only',c['report_source_commit'],canonical({}),
        file_sha256(manifest),'train','fixture-checkpoint','fixture-text',canonical({'cpus':2})))
    old.status('planned');old.status('running');rendered={};(oldroot/'reports').mkdir()
    for sid in ids:
        source=tmp_path/sid;r,rows,m,h=inputs(source,sid);m['source_kind']=r['source_kind']='real'  # Simulate the real-input guards; images remain artificial.
        (source/'metadata.json').write_text(json.dumps(m))
        with (source/'tiles.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        dest=encoded/sid;dest.mkdir(parents=True)
        completion=dict(cohort_split='train',input_identity=dict(manifest_sha256=file_sha256(source/'tiles.csv'),metadata_sha256=file_sha256(source/'metadata.json'),png_sha256=h,checkpoint_sha256='fixture-checkpoint'))
        (dest/'completion.json').write_text(json.dumps(completion));verified.append(dict(image_id=sid,completion_sha256=file_sha256(dest/'completion.json')));paths.append(str(source))
        public=oldroot/'reports'/(sid+'.json');public.write_text(canonical(r)+'\n');rendered['reports/'+sid+'.json']=file_sha256(public)
        old.checkpoint('slide-'+sid,dict(report=r,evaluation_only_controls=[]))
    old.checkpoint('summary',dict(components=144,rendered_file_sha256=rendered,decision_changing_components=72,
        decision_changing_supported=0,decision_changing_abstained=72,annotation_positive_decisive_components=0,
        slides_with_decision_dependence=72));old.status('verified',validation=True)
    old_before={str(p):p.read_bytes() for p in oldroot.rglob('*') if p.is_file()}
    c['inputs']={};c['report_root']=str(oldroot);c['encoded_root']=str(encoded);c['components']=144;c['output']=str(tmp_path/'fixture-run')
    directories=tmp_path/'directories.json';directories.write_text(json.dumps(paths));verification=tmp_path/'verified.json';verification.write_text(json.dumps(dict(manifest_sha256=file_sha256(manifest),records=verified)))
    c['inputs']={k:dict(path=str(p),sha256=file_sha256(p)) for k,p in [('manifest',manifest),('directories',directories),('verification',verification)]}
    monkeypatch.setattr(export,'preflight',lambda *a,**k:c);monkeypatch.setenv('SLURM_JOB_ID','fixture');monkeypatch.delenv('SLURM_JOB_GPUS',raising=False)
    result=export.run(CONFIG,'fixture',PROJECT,c['output'],'b'*40,execute=True)
    assert result['unique_png_assets']==288 and result['tile_references']==576 and not result['source_pixels_changed']
    assert result['original_dependence_counts']['decision_changing_components']==72
    assert len(result['rendered_file_sha256'])==433
    assert all(file_sha256(Path(c['output'])/name)==digest for name,digest in result['rendered_file_sha256'].items())
    assert len(read_sealed(c['output'])[1])==73
    assert old_before=={str(p):p.read_bytes() for p in oldroot.rglob('*') if p.is_file()}
