"""Artificial raster/vector fixtures only; no pathology or real-data results."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from floater_finder.artifacts import Slide
from floater_finder.research import pixel_study as ps


def test_native_area_mapping_and_background_eligibility():
    labels=np.array([[0,2],[4,5]],np.uint8)
    f=ps.crop_fractions(labels,[0,0,224,224]);assert f['background_fraction']==.25 and f['gleason4_fraction']==.25
    f=ps.crop_fractions(labels,[112,112,224,224]);assert f['gleason5_fraction']==1
    f=ps.crop_fractions(labels,[56,0,168,112]);assert f['background_fraction']==.5 and f['benign_fraction']==.5
    assert ps.eligible(f,'benign') and not ps.eligible(f,'gp45')
    assert ps.choose_crop(np.full((230,230),4,np.uint8),'gp45') is not None
    assert ps.choose_crop(np.zeros((230,230),np.uint8),'gp45') is None
    with pytest.raises(ValueError):ps.crop_fractions(np.array([[6]]),[0,0,1,1])
    with pytest.raises(ValueError):ps.crop_fractions(labels,[-1,0,1,1])


def test_scale_and_unchanged_drift_gate():
    m=dict(tile_size=[112.,112.],measured_mpp_xy=[.5,.5],footprint_level0_pixels_xy=[224,224],export_pixels=224)
    ps.assert_scale(m,m)
    with pytest.raises(ValueError,match='physical scale'):ps.assert_scale(m,dict(m,measured_mpp_xy=[.4,.4]))
    old=np.eye(2,dtype=np.float32)
    assert ps.drift_gate(old,old)['passed']
    assert not ps.drift_gate(old,old[::-1])['passed']
    with pytest.raises(ValueError):ps.drift_gate(old,np.full((2,2),np.nan))


def fixture_study(tmp_path,monkeypatch):
    c=dict(experiment_id='panda_pixel_contamination_v1',split='train',selection_seed=20261027,pairs=[],
        preview_root=str(tmp_path/'previews'),encoded_root=str(tmp_path/'encoded'),inputs={},models=[],
        checkpoint_sha256='c'*64,prompts_sha256='d'*64,embedding_model={},limitations=['fixture'])
    output=tmp_path/'prepared';c['preparation_output']=str(output)
    preview=Path(c['preview_root']);(preview/'reports').mkdir(parents=True);(preview/'checkpoints').mkdir()
    sources={};cohort=[];verified=[];summary=dict(rendered_file_sha256={});data={}
    for i in range(8):
        sid=f'{i+1:032x}';is_host=i<4;label=2 if i<2 else 3 if i<4 else 4
        directory=tmp_path/sid;directory.mkdir();tile_rows=[];hashes={};assets={}
        for j in range(3):
            tid=f'{sid}-x{j}-y0';p=directory/(tid+'.png')
            a=np.zeros((224,224,3),np.uint8);a[:]=[130+i*10+j,50+j*10,100];a[::3,::4]=[120,20+i,90]
            Image.fromarray(a).save(p);digest=ps.file_sha256(p);hashes[tid]=digest
            asset=f'{sid}-{j}.png';(preview/asset).write_bytes(p.read_bytes())
            assets[asset]=dict(source_path=str(p),sha256=digest)
            fractions={n+'_fraction':float(k==label) for k,n in enumerate(ps.LABELS)}
            tile_rows.append(dict(tile_id=tid,path=p.name,x_level0=str(j*224),y_level0='0',x=str(j*112),y='0',**fractions))
            data[(sid,j)]=(Image.fromarray(a),np.full((224,224),label,np.uint8))
        image=tmp_path/(sid+'.tiff');mask=tmp_path/(sid+'_mask.tiff');image.write_bytes(b'fixture image');mask.write_bytes(b'fixture mask')
        cohort.append(dict(image_id=sid,image_path=str(image),mask_path=str(mask),image_sha256=ps.file_sha256(image),mask_sha256=ps.file_sha256(mask)))
        meta=dict(tile_size=[112.,112.],measured_mpp_xy=[.5,.5],footprint_level0_pixels_xy=[224,224],export_pixels=224,extraction=dict(image_level=0))
        sources[sid]=(directory,tile_rows,meta,dict(png_sha256=hashes))
        (Path(c['encoded_root'])/sid).mkdir(parents=True)
        (Path(c['encoded_root'])/sid/'completion.json').write_text('{}')
        (Path(c['encoded_root'])/sid/'slide.npz').write_bytes(b'fixture, not loadable vectors')
        public='reports/'+sid+'.json';(preview/public).write_text('{}');summary['rendered_file_sha256'][public]=ps.file_sha256(preview/public)
        (preview/'checkpoints'/('slide-'+sid+'.json')).write_text(json.dumps(dict(png_assets=assets)))
        verified.append(dict(image_id=sid,completion_sha256=ps.verified_digest(c,sid)))
    manifest=tmp_path/'cohort.csv'
    import csv
    with manifest.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(cohort[0]));w.writeheader();w.writerows(cohort)
    verification=tmp_path/'verification.json';verification.write_text(json.dumps(dict(records=verified)))
    summ=tmp_path/'summary.json';summ.write_text(json.dumps(summary))
    c['inputs']={k:dict(path=str(p),sha256=ps.file_sha256(p)) for k,p in [('manifest',manifest),('verification',verification),('preview_summary',summ)]}
    c['pairs']=[dict(id=f'pair-{i+1}',task='s1' if i<2 else 's2',host=f'{i+1:032x}',donor=f'{i+5:032x}') for i in range(4)]
    @contextmanager
    def readers(image_path,mask_path,scale):
        sid=Path(image_path).stem
        class Mask:
            def read_region(self,origin,level,size):
                labels=data[(sid,origin[0]//224)][1];a=np.zeros((224,224,4),np.uint8);a[:,:,0]=labels;a[:,:,3]=255
                return Image.fromarray(a)
        yield sid,Mask(),dict(alignment_check='fixture matching geometry')
    monkeypatch.setattr(ps,'panda_readers',readers)
    monkeypatch.setattr(ps,'_rgb_region',lambda sid,origin,footprint,level,pixels:data[(sid,origin[0]//224)][0])
    monkeypatch.setattr(ps,'_load_source',lambda c,sid,cohort,verified:sources[sid])
    monkeypatch.setattr(ps,'encoding_contract',lambda:dict(fixture=True))
    monkeypatch.setattr(ps,'preflight',lambda *a:c)
    monkeypatch.setenv('SLURM_JOB_ID','fixture-only');monkeypatch.delenv('SLURM_JOB_GPUS',raising=False)
    return c,output,data


def test_all_96_images_source_masks_geometry_provenance_and_immutability(tmp_path,monkeypatch):
    c,out,data=fixture_study(tmp_path,monkeypatch)
    r=ps.prepare_real('fixture','e'*64,tmp_path,out,'fixture-source')
    assert r['images']==96 and len(r['records'])==96 and not r['inference_executed']
    assert len(list(out.rglob('*.png')))==392  # 384 composite/mask files + eight exact native label maps
    assert len(r['pairs'])==4 and all(not p['patient_independence_verified'] for p in r['pairs'])
    for pair in r['pairs']:
        assert pair['sources']['host']['tile_id']==pair['sources']['native_sham']['tile_id']
        assert pair['sources']['host']['slide_id']==pair['sources']['native_sham']['slide_id']
    for record in r['records']:
        d=record['nominal_patch_area_percent'];side={1:22,5:50,10:71}[d]
        assert record['realized_patch_area_percent']==pytest.approx(100*side**2/224**2)
        assert record['physical_patch_area_mm2']==pytest.approx(side**2*.5**2/1e6)
    digest=ps.file_sha256(out/'image_manifest.json');ps.prepared_inputs(out,digest)
    with pytest.raises(FileExistsError):ps.prepare_real('fixture','e'*64,tmp_path,out,'fixture-source')
    f=out/r['records'][0]['files']['image']['path'];f.write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):ps.prepared_inputs(out,digest)


def test_wrong_mask_or_source_change_stops_before_composition(tmp_path,monkeypatch):
    c,out,data=fixture_study(tmp_path,monkeypatch)
    for key,(im,labels) in data.items():
        if key[0]==c['pairs'][0]['donor']:data[key]=(im,np.zeros_like(labels))
    with pytest.raises(ValueError,match='fractions disagree'):ps.prepare_real('fixture','e'*64,tmp_path,out,'fixture-source')
    assert (out/'failure.json').exists() and not (out/'completion.json').exists()
    assert not list(out.glob('dose-*'))


def test_cpu_and_gpu_execution_guards(tmp_path,monkeypatch):
    monkeypatch.delenv('SLURM_JOB_ID',raising=False)
    with pytest.raises(RuntimeError,match='CPU Slurm'):ps.prepare_real('missing','x',tmp_path,tmp_path/'out','x')
    with pytest.raises(RuntimeError,match='GPU Slurm'):ps.encode_real('missing','x',tmp_path,'missing','x',tmp_path/'out','x')
    for name in ('panda_pixel_prepare.sbatch','panda_pixel_encode.sbatch'):
        text=(Path(__file__).parents[1]/'scripts/slurm'/name).read_text()
        assert 'HF_HUB_OFFLINE=1' in text and 'srun ' in text
    text=(Path(__file__).parents[1]/'scripts/slurm/panda_pixel_encode.sbatch').read_text()
    assert '--time=00:05:00' in text and '--gres=gpu:1' in text and '--cpus-per-task=4' in text and '--mem=16G' in text


def test_vector_measurements_exclude_truth_and_keep_intervention_doses_distinct():
    import inspect
    assert list(inspect.signature(ps.vector_signal).parameters)==['query','references']
    ref=np.tile([1.,0.],(6,1));assert ps.vector_signal([1.,0.],ref)==0 and ps.vector_signal([0.,1.],ref)==1
    with pytest.raises(ValueError):ps.vector_signal([1.,0.],ref[:4])
    model=dict(name='fixture',revision='fixture',checkpoint_sha256='fixture',preprocessing='fixture',projection=True,normalized=True)
    host=Slide(ref,np.zeros((6,2)),np.array([str(i) for i in range(6)]),
        dict(model=model,source_kind='fixture',slide_id='h',patient_id='fixture',project='fixture',organ='prostate',coordinate_units='microns',split='dev'))
    new=np.array([.6,.8]);bags=ps.intervention_slides(host,np.array([0.,1.]),2,new)
    assert np.array_equal(host.feats,ref) and len(bags['separate_donor_append'].feats)==7
    assert np.array_equal(bags['mixed_image_replacement'].feats[2],new)
    assert np.array_equal(bags['separate_donor_replacement'].feats[2],[0.,1.])
    assert np.array_equal(bags['mixed_image_replacement'].coords,host.coords)


def test_paired_measurements_keep_foreign_vs_sham_and_frozen_models_separate():
    model=dict(name='fixture',revision='fixture',checkpoint_sha256='fixture',preprocessing='fixture',projection=True,normalized=True)
    meta=dict(model=model,source_kind='fixture',slide_id='h',patient_id='fixture',project='fixture',organ='prostate',coordinate_units='microns',split='dev')
    host=Slide(np.tile([1.,0.],(6,1)),np.zeros((6,2)),np.array([str(i) for i in range(6)]),meta)
    donor=Slide(np.tile([0.,1.],(6,1)),host.coords,host.tile_ids,dict(meta,slide_id='d'))
    class Text:classes=['benign','cancer'];feats=np.eye(2)
    class Predictor:
        def score_slide(self,slide):
            scores=slide.feats.mean(axis=0);return dict(prediction='cancer' if scores[1]>scores[0] else 'benign',scores=scores.tolist())
    records=[dict(pair_id='pair-1-d1',variant=v,nominal_patch_area_percent=1,realized_patch_area_percent=.99,
        placement_id='upper_left',physical_patch_area_mm2=.001) for v in ('foreign_patch','native_sham','unchanged','cut_reinsert_null')]
    m=dict(pairs=[dict(id='pair-1',host='h',donor='d',task='s1',sources=dict(host=dict(tile_index=0),donor=dict(tile_index=0)))],records=records)
    features=np.array([[0.,1.],[.6,.8],[1.,0.],[1.,0.]])
    r=ps.measurements(dict(limitations=['fixture']),m,features,dict(h=(host,Text()),d=(donor,Text())),{('s1',role):Predictor() for role in ('primary','historical')})
    assert r['paired_comparisons'][0]['comparisons']['native_sham']['host_distance_difference']==pytest.approx(.6)
    assert r['records'][0]['edited_tile_percent_of_original_sampled_bag']==pytest.approx(100/6)
    assert r['records'][0]['mixed_donor_area_percent_of_original_sampled_bag']==pytest.approx(.99/6)
    assert r['records'][0]['morphology_similarity_delta']=={'benign':-1.,'cancer':1.}
    assert not r['pixel_localization_evaluated'] and r['tissue_action']=='none'


def test_gpu_unchanged_drift_aborts_before_any_composite_encoding(tmp_path,monkeypatch):
    """Fake CUDA/encoder: assert fail-closed order without any hardware/model call."""
    import sys
    from types import SimpleNamespace
    from floater_finder import conch
    from floater_finder.artifacts import TextEmbeddings
    monkeypatch.setenv('SLURM_JOB_ID','fixture-only');monkeypatch.setenv('SLURM_JOB_GPUS','0')
    torch=SimpleNamespace(cuda=SimpleNamespace(device_count=lambda:1),set_num_threads=lambda n:None,manual_seed=lambda s:None,
        backends=SimpleNamespace(cuda=SimpleNamespace(matmul=SimpleNamespace()),cudnn=SimpleNamespace()))
    monkeypatch.setitem(sys.modules,'torch',torch)
    model=dict(name='fixture',revision='fixture',checkpoint_sha256='fixture',preprocessing='fixture',projection=True,normalized=True)
    meta=dict(model=model,source_kind='fixture',slide_id='h',patient_id='fixture',project='fixture',organ='prostate',coordinate_units='microns',split='dev')
    text=TextEmbeddings(np.eye(2),['benign','cancer'],{k:['a','b','c'] for k in ('benign','cancer')},model,'fixture')
    encoded=tmp_path/'sources';encoded.mkdir();pairs=[]
    for i in range(4):
        pair=dict(id=f'pair-{i}',task='s1',host=f'h{i}',donor=f'd{i}',sources={})
        for role in ('host','donor'):
            sid=pair[role];d=encoded/sid;d.mkdir()
            Slide(np.tile([1.,0.],(6,1)),np.zeros((6,2)),np.array([str(j) for j in range(6)]),dict(meta,slide_id=sid)).save(d/'slide.npz')
            text.save(d/'text.npz');(d/'completion.json').write_text('{}')
            pair['sources'][role]=dict(tile_index=0,path='fixture-never-opened.png',saved_slide_sha256=ps.file_sha256(d/'slide.npz'),embedding_completion_sha256=ps.file_sha256(d/'completion.json'))
        pairs.append(pair)
    checkpoint=tmp_path/'checkpoint';checkpoint.write_bytes(b'fixture')
    output=tmp_path/'out'
    c=dict(preparation_output=str(tmp_path/'prepared'),gpu_output=str(output),checkpoint=str(checkpoint),checkpoint_sha256=ps.file_sha256(checkpoint),
        encoded_root=str(encoded),text_fingerprint=text.fingerprint(),drift_tolerances=dict(max_cosine_distance=1e-5,max_absolute_difference=5e-4))
    m=dict(protocol_sha256='fixture',encoding_contract={},embedding_model=model,pairs=pairs)
    monkeypatch.setattr(ps,'preflight',lambda *a:c);monkeypatch.setattr(ps,'prepared_inputs',lambda *a:m);monkeypatch.setattr(ps,'encoding_contract',lambda:{})
    calls=[]
    class Encoder:
        provenance=model
        def __init__(self,p):pass
        def images(self,paths,batch):
            calls.append(paths);return np.tile([0.,1.],(8,1)),.01
    monkeypatch.setattr(conch,'ConchEncoder',Encoder)
    with pytest.raises(RuntimeError,match='Unchanged-source drift'):
        ps.encode_real('fixture','fixture',tmp_path,c['preparation_output'],'fixture',output,'fixture-source')
    assert len(calls)==1 and not (output/'embeddings.npz').exists()
    assert not json.loads((output/'unchanged_drift_gate.json').read_text())['passed']
    assert (output/'failure.json').exists() and not (output/'completion.json').exists()
