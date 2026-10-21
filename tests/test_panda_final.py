"""Temporary software-contract fixtures, not scientific inputs or final evaluations."""
import json
from pathlib import Path
import numpy as np
import pytest
from floater_finder.experiments import file_sha256
from floater_finder.panda_final import preflight,require_execution,classification_summary,clustered_ratio_interval


def contract(tmp_path):
    source=tmp_path/'source';source.mkdir();(source/'code.py').write_text('# fixture')
    (tmp_path/'snapshot.json').write_text(json.dumps(dict(commit='fixture-source')))
    data=tmp_path/'data';data.mkdir();entries=[]
    for i in range(24):
        d=data/f'{i:032x}';d.mkdir();files={}
        for name in ('slide.npz','text.npz','timing.json','completion.json','tiles.csv','metadata.json','tile.png','image.tiff'):
            p=d/name;p.write_bytes(b'fixture bytes only, never decode');files[str(p)]=file_sha256(p)
        entries.append(dict(image_id=d.name,files=files,image_path=str(d/'image.tiff')))
    index=data/'blind.json';index.write_text(json.dumps(dict(entries=entries)))
    manifest=data/'manifest.csv';manifest.write_text('DO NOT DECODE TEST LABELS\n')
    verification=data/'verification.json';verification.write_text('{}')
    protocol=dict(schema_version=1,status='frozen',automatic_tissue_action='none',source=dict(commit='fixture-source',files={'code.py':file_sha256(source/'code.py')}),
        runtime_versions={},allowed_data_roots=[str(data)],data=dict(manifest=str(manifest),manifest_sha256=file_sha256(manifest),verification=str(verification),verification_sha256=file_sha256(verification),blinded_index=str(index),blinded_index_sha256=file_sha256(index)),
        test_ids=[r['image_id'] for r in entries],execution=dict(output=str(data/'final-output')),readiness=dict(operating_point_supported=False,reason='fixture unsupported'))
    path=tmp_path/'protocol.json';path.write_text(json.dumps(protocol))
    return path,source,protocol,entries


def test_preflight_hashes_only_and_never_loads_models_labels_or_feature_arrays(tmp_path,monkeypatch):
    path,source,protocol,entries=contract(tmp_path)
    monkeypatch.setattr(np,'load',lambda *a,**k:pytest.fail('Preflight decoded held-out arrays'))
    report=preflight(path,file_sha256(path),source)
    assert report['protocol_frozen'] and report['test_slides']==24
    assert not report['test_predictions_computed'] and not report['test_labels_decoded'] and not report['ready_for_final_predictions']
    assert not Path(protocol['execution']['output']).exists()
    Path(entries[0]['image_path']).write_bytes(b'changed fixture')
    with pytest.raises(ValueError,match='checksum mismatch'):preflight(path,file_sha256(path),source)


def test_preflight_and_execution_fail_closed_on_changed_protocol_source_or_reuse(tmp_path):
    path,source,protocol,entries=contract(tmp_path)
    with pytest.raises(ValueError,match='protocol checksum'):preflight(path,'0'*64,source)
    with pytest.raises(RuntimeError,match='explicit'):require_execution(protocol,False)
    with pytest.raises(RuntimeError,match='No supported'):require_execution(protocol,True)
    Path(protocol['execution']['output']).mkdir()
    with pytest.raises(FileExistsError,match='single execution'):preflight(path,file_sha256(path),source)
    Path(protocol['execution']['output']).rmdir();(source/'code.py').write_text('changed')
    with pytest.raises(ValueError,match='source file'):preflight(path,file_sha256(path),source)


def test_uncertainty_resamples_slides_and_preserves_zero_denominators():
    result=classification_summary([0,0,1,1],[0,1,1,1],repetitions=50)
    assert result['balanced_accuracy']==.75 and result['confusion_rows_truth_columns_prediction']==[[1,1],[0,2]]
    rows=[dict(host_id='A',hit=1,total=1),dict(host_id='A',hit=1,total=1),dict(host_id='B',hit=0,total=1)]
    interval=clustered_ratio_interval(rows,'hit','total',repetitions=50)
    assert interval['unique_host_slides']==2 and interval['estimate']==pytest.approx(2/3)
    assert clustered_ratio_interval([dict(host_id='A',hit=0,total=0)],'hit','total')['estimate'] is None
