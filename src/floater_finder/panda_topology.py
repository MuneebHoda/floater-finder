"""Observed RGB-pyramid tissue connectivity; no dilation, closing or gap bridging."""
import numpy as np
from PIL import Image


def tissue_mask(rgb, maximum=220, chroma=10):
    rgb=np.asarray(rgb)
    if rgb.ndim!=3 or rgb.shape[2]!=3 or rgb.dtype!=np.uint8:raise ValueError('uint8 RGB required')
    return (rgb.min(axis=2)<maximum)&(rgb.max(axis=2).astype(int)-rgb.min(axis=2)>chroma)


def label_mask(mask):
    """Eight-connected binary pixels via row runs, with bounded label-image memory."""
    mask=np.asarray(mask,dtype=bool)
    if mask.ndim!=2 or not 1<=mask.size<=4_000_000:raise ValueError('Mask exceeds four-million-pixel bound')
    parents=[0];runs=[];previous=[]
    def find(x):
        while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
        return x
    for y,row in enumerate(mask):
        changes=np.flatnonzero(np.diff(np.r_[False,row,False]));current=[];j=0
        for start,end in changes.reshape(-1,2):
            label=len(parents);parents.append(label)
            while j<len(previous) and previous[j][1]<start:j+=1
            k=j
            while k<len(previous) and previous[k][0]<=end:
                root=find(previous[k][2]);other=find(label)
                if root!=other:parents[max(root,other)]=min(root,other)
                k+=1
            current.append((int(start),int(end),label));runs.append((y,int(start),int(end),label))
        previous=current
    labels=np.zeros(mask.shape,dtype=np.int32);roots={};counts={};bounds={}
    for y,a,b,label in runs:
        root=find(label);number=roots.setdefault(root,len(roots)+1);labels[y,a:b]=number
        counts[number]=counts.get(number,0)+b-a
        old=bounds.get(number,[a,y,b,y+1]);bounds[number]=[min(old[0],a),min(old[1],y),max(old[2],b),max(old[3],y+1)]
    return labels,{k:dict(pixels=counts[k],bbox_xyxy=bounds[k]) for k in counts}


def overview_components(mask,coords_um,tile_size_um,pixel_um,purity=.8):
    coords=np.asarray(coords_um,dtype=float);size=np.asarray(tile_size_um,dtype=float);scale=np.asarray(pixel_um,dtype=float)
    if (coords.ndim!=2 or coords.shape[1]!=2 or size.shape!=(2,) or scale.shape!=(2,) or
            not np.isfinite(coords).all() or not np.isfinite([size,scale]).all() or np.any(coords<0) or np.any(size<=0) or np.any(scale<=0)):
        raise ValueError('Measured physical coordinates/scale required')
    labels,objects=label_mask(mask);assignments=[];quality=[]
    for point in coords:
        a=np.floor(point/scale).astype(int);b=np.ceil((point+size)/scale).astype(int)
        region=labels[max(0,a[1]):min(labels.shape[0],b[1]),max(0,a[0]):min(labels.shape[1],b[0])]
        values,counts=np.unique(region[region>0],return_counts=True)
        fraction=float(counts.max()/counts.sum()) if len(counts) else 0.
        coverage=float(counts.sum()/region.size) if region.size else 0.
        number=int(values[np.argmax(counts)]) if len(counts) and fraction>=purity and coverage>=.1 else 0
        assignments.append(number);quality.append(dict(component_purity=fraction,foreground_coverage=coverage))
    components=[];numbers=list(objects)
    all_boxes=np.array([objects[k]['bbox_xyxy'] for k in numbers],dtype=float).reshape(-1,4)*np.tile(scale,2)
    for number in sorted(set(assignments)-{0}):
        obj=objects[number];bbox=np.array(obj['bbox_xyxy'],dtype=float)*np.tile(scale,2)
        others=all_boxes[np.array(numbers)!=number]
        gaps=np.maximum(np.maximum(bbox[:2]-others[:,2:],others[:,:2]-bbox[2:]),0)
        isolation=float(np.linalg.norm(gaps,axis=1).min()/1000) if len(others) else None
        components.append(dict(component_id=number,indices=np.flatnonzero(np.array(assignments)==number).tolist(),
            observed_tissue_area_mm2=float(obj['pixels']*np.prod(scale)/1e6),bbox_um=bbox.tolist(),
            isolation_bbox_lower_bound_mm=isolation))
    return components,dict(mapped_tiles=sum(x>0 for x in assignments),tiles=len(coords),
        mapping_fraction=sum(x>0 for x in assignments)/len(coords),unassigned_indices=np.flatnonzero(np.array(assignments)==0).tolist(),
        foreground_components=len(objects),components_with_saved_tiles=len(components),assignment_quality=quality)


def add_observed_tiles(host_mask,coords_um,tile_size_um,pixel_um,tile_rgbs,maximum=220,chroma=10):
    """Union actual exported donor RGB foreground with the observed host mask at recorded placement."""
    scale=np.asarray(pixel_um);size=np.asarray(tile_size_um);coords=np.asarray(coords_um)
    if len(coords)!=len(tile_rgbs) or not len(coords):raise ValueError('Aligned nonempty RGB tile list required')
    width=max(host_mask.shape[1],int(np.ceil((coords[:,0]+size[0]).max()/scale[0])))
    height=max(host_mask.shape[0],int(np.ceil((coords[:,1]+size[1]).max()/scale[1])))
    if width*height>4_000_000:raise ValueError('Synthetic overview exceeds bounded canvas')
    canvas=np.zeros((height,width),dtype=bool);canvas[:host_mask.shape[0],:host_mask.shape[1]]=host_mask
    for point,rgb in zip(coords,tile_rgbs):
        a=np.floor(point/scale).astype(int);b=np.ceil((point+size)/scale).astype(int)
        foreground=tissue_mask(rgb,maximum,chroma)
        raw_x=((np.arange(a[0],b[0])+.5)*scale[0]-point[0])/size[0]*foreground.shape[1]
        raw_y=((np.arange(a[1],b[1])+.5)*scale[1]-point[1])/size[1]*foreground.shape[0]
        xs=np.clip(raw_x,0,foreground.shape[1]-1).astype(int);ys=np.clip(raw_y,0,foreground.shape[0]-1).astype(int)
        valid=((raw_y>=0)&(raw_y<foreground.shape[0]))[:,None]&((raw_x>=0)&(raw_x<foreground.shape[1]))[None,:]
        canvas[a[1]:b[1],a[0]:b[0]]|=foreground[np.ix_(ys,xs)]&valid
    return canvas
