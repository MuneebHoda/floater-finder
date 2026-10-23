"""Artificial raster software fixtures; no scientific tissue claim."""
import hashlib
import json
import numpy as np
from PIL import Image
import pytest
from floater_finder.research.pixel_controls import prepare


def plan(tmp_path):
    native=np.zeros((12,16,3),dtype=np.uint8);native[:6]=[200,80,100];native[6:]=[150,50,70]
    donor=np.zeros_like(native);donor[:]=[20,40,180]
    for name,pixels in [('host',native),('donor',donor)]:Image.fromarray(pixels).save(tmp_path/(name+'.png'))
    def source(name,sid,crop):
        p=tmp_path/(name+'.png')
        return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),slide_id=sid,tile_id=name,crop_box=crop)
    return dict(schema_version=1,source_kind='fixture',interpolation='bilinear',pairs=[dict(id='pair',
        host=source('host','native',[0,0,16,12]),donor=source('donor','foreign',[0,0,8,6]),
        native_sham=source('host','native',[0,0,8,6]))],placements=[dict(id='box',width_fraction=.5,height_fraction=.5,left_fraction=.5,top_fraction=.5)])


def write(tmp_path,p):
    f=tmp_path/'plan.json';f.write_text(json.dumps(p));return f


def test_composites_have_exact_masks_geometry_controls_and_provenance(tmp_path):
    p=plan(tmp_path);path=write(tmp_path,p);out=tmp_path/'out';m=prepare(path,out)
    assert m['variants']==4 and m['source_kind']=='fixture' and not m['encoder_inference_run'] and not m['scientific_results']
    records={r['variant']:r for r in m['records']}
    host=np.asarray(Image.open(tmp_path/'host.png'))
    for name,r in records.items():
        image=np.asarray(Image.open(out/r['files']['image']['path']))
        foreign=np.asarray(Image.open(out/r['files']['foreign_mask']['path']))
        assert r['destination_box_xyxy']==[8,6,16,12] and r['realized_area_fraction']==.25
        assert np.array_equal(image[:6],host[:6]) and np.array_equal(image[:,:8],host[:,:8])
        assert foreign.sum()==(48*255 if name=='foreign_patch' else 0)
        if name in ('cut_reinsert_null','unchanged'):assert np.array_equal(image,host)
        else:assert np.any(image!=host)
        for info in r['files'].values():assert hashlib.sha256((out/info['path']).read_bytes()).hexdigest()==info['sha256']
    assert records['foreign_patch']['interpolation']==records['native_sham']['interpolation']=='bilinear'
    with pytest.raises(FileExistsError):prepare(path,out)


def test_missing_sham_changed_hash_clipping_and_large_study_fail_before_writing(tmp_path):
    p=plan(tmp_path);p['pairs'][0].pop('native_sham')
    with pytest.raises(ValueError,match='sham'):prepare(write(tmp_path,p),tmp_path/'missing')
    assert not (tmp_path/'missing').exists()
    p=plan(tmp_path);p['pairs'][0]['donor']['sha256']='0'*64
    with pytest.raises(ValueError,match='hash changed'):prepare(write(tmp_path,p),tmp_path/'hash')
    p=plan(tmp_path);p['placements'][0]['left_fraction']=.8
    with pytest.raises(ValueError,match='clipping'):prepare(write(tmp_path,p),tmp_path/'clip')
    p=plan(tmp_path);p['placements']*=25
    with pytest.raises(ValueError,match='96'):prepare(write(tmp_path,p),tmp_path/'bulk')
    assert not any((tmp_path/name).exists() for name in ('hash','clip','bulk'))


def test_sham_relationship_null_patch_and_bounded_input_are_checked(tmp_path):
    p=plan(tmp_path);p['pairs'][0]['native_sham']['slide_id']='different'
    with pytest.raises(ValueError,match='host slide ID'):prepare(write(tmp_path,p),tmp_path/'wrong')
    p=plan(tmp_path);p['pairs'][0]['native_sham']['crop_box']=[8,6,16,12]
    with pytest.raises(ValueError,match='different native patch'):prepare(write(tmp_path,p),tmp_path/'null')
    p=plan(tmp_path);large=tmp_path/'large.png';Image.new('RGB',(1025,2)).save(large)
    p['pairs'][0]['donor'].update(path=str(large),sha256=hashlib.sha256(large.read_bytes()).hexdigest(),crop_box=[0,0,8,2])
    with pytest.raises(ValueError,match='bounded'):prepare(write(tmp_path,p),tmp_path/'large-out')
