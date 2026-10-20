import numpy as np
import pytest
from floater_finder.panda_topology import label_mask,overview_components,add_observed_tiles


def test_observed_connectivity_respects_gaps_and_real_continuity():
    mask=np.zeros((10,20),bool);mask[2:8,1:6]=True;mask[2:8,12:18]=True
    labels,objects=label_mask(mask)
    assert len(objects)==2 and labels[4,5]!=labels[4,12] and labels[4,8]==0
    mask[4,6:12]=True
    assert len(label_mask(mask)[1])==1
    diagonal=np.eye(3,dtype=bool)
    assert len(label_mask(diagonal)[1])==1


def test_overview_groups_sparse_samples_without_inventing_a_missing_pixel_bridge():
    mask=np.zeros((10,20),bool);mask[1:8,1:9]=True;mask[1:8,13:19]=True
    parts,quality=overview_components(mask,[[1,1],[6,1],[14,1]],[2,2],[1,1])
    assert [p['indices'] for p in parts]==[[0,1],[2]]
    assert quality['mapping_fraction']==1
    assert parts[0]['observed_tissue_area_mm2']==56/1e6
    assert parts[0]['isolation_bbox_lower_bound_mm']==.004


def test_ambiguous_membership_is_not_forced_and_injection_uses_rgb_foreground():
    mask=np.zeros((6,12),bool);mask[:,0:3]=True;mask[:,5:8]=True
    parts,q=overview_components(mask,[[0,0]],[8,6],[1,1])
    assert not parts and q['unassigned_indices']==[0]
    rgb=np.full((4,4,3),255,dtype=np.uint8);rgb[1:3,1:3]=[150,70,130]
    mixed=add_observed_tiles(np.zeros((6,6),bool),np.array([[8.,0.]]),[4,4],[1,1],[rgb])
    assert mixed.shape==(6,12) and mixed.sum()==4 and not mixed[0,8]
    with pytest.raises(ValueError):label_mask(np.zeros((2001,2001),bool))
