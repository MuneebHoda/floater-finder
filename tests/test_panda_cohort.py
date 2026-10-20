from collections import Counter
import pytest
from floater_finder.panda_cohort import candidates, select, GROUPS


def fixture_rows():
    labels, files = [], []
    for group, grade in enumerate((0,1,4)):
        for i in range(48):
            sid=f'{group*100+i:032x}'
            labels.append(dict(image_id=sid,data_provider='radboud',isup_grade=str(grade),gleason_score='negative' if grade==0 else '3+3' if grade==1 else '4+4'))
            files.append(dict(name=f'train_images/{sid}.tiff',bytes=1000))
            if i%7:
                files.append(dict(name=f'train_label_masks/{sid}_mask.tiff',bytes=100))
    return labels,files


def test_catalog_selection_nested_deterministic_slide_disjoint_splits():
    labels, files=fixture_rows()
    exposed={labels[0]['image_id'],labels[48]['image_id'],labels[96]['image_id']}
    rows=candidates(labels,files,engineering_ids=exposed)
    small,large=select(rows,20),select(list(reversed(rows)),40)
    assert small==select(list(reversed(rows)),20)
    a={r['image_id']:r['split'] for r in small};b={r['image_id']:r['split'] for r in large}
    assert len(a)==60 and len(b)==120 and all(b[k]==v for k,v in a.items())
    assert all(r['split']=='train' for r in large if r['image_id'] in exposed)
    for group in GROUPS:
        assert Counter(r['split'] for r in small if r['group']==group)==dict(train=12,calibration=4,test=4)
        assert Counter(r['split'] for r in large if r['group']==group)==dict(train=24,calibration=8,test=8)
    assert all(not r['patient_id_known'] and not r['mask_usable_verified'] for r in rows)


def test_missing_catalog_or_duplicate_does_not_fabricate_available_slides():
    labels,files=fixture_rows()
    rows=candidates(labels,files[:4])
    with pytest.raises(ValueError,match='Insufficient'):select(rows,20)
    with pytest.raises(ValueError,match='Duplicate'):candidates(labels+labels[:1],files)
    with pytest.raises(ValueError,match='Duplicate/invalid'):candidates(labels,files+files[:1])
