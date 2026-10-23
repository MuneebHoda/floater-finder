"""Bounded tile-level compositing preparation; no encoder or scientific inference."""
import hashlib
import json
import math
from pathlib import Path
import re
import numpy as np
from PIL import Image

VARIANTS = ('foreign_patch', 'native_sham', 'cut_reinsert_null', 'unchanged')
RESAMPLERS = {name: getattr(Image.Resampling, name.upper()) for name in ('nearest','bilinear','bicubic','lanczos')}
MAX_VARIANTS = 96
MAX_TILE_SIDE = 1024
MAX_TILE_BYTES = 16 * 1024 * 1024


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def _identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',value):
        raise ValueError('Safe nonempty identifiers required')
    return value


def _source(spec):
    if set(spec) != {'path','sha256','slide_id','tile_id','crop_box'}:
        raise ValueError('Each parent requires path, SHA256, slide ID, tile ID and crop box')
    path=Path(spec['path']).expanduser().resolve()
    if path.suffix.lower()!='.png' or not path.is_file():
        raise ValueError('Only explicitly supplied PNG tiles are accepted; no WSI reading')
    if path.stat().st_size>MAX_TILE_BYTES:raise ValueError('Input exceeds bounded PNG tile bytes')
    digest=spec['sha256']
    if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest) or sha256(path)!=digest:
        raise ValueError('Parent image hash changed or is invalid')
    _identifier(spec['slide_id']);_identifier(spec['tile_id'])
    with Image.open(path) as image:
        if max(image.size)>MAX_TILE_SIDE or min(image.size)<1 or image.format!='PNG':
            raise ValueError('Input exceeds bounded PNG tile dimensions')
        if image.mode not in ('RGB','RGBA','L'):
            raise ValueError('Only RGB, RGBA or grayscale PNG tiles are supported')
        original_mode=image.mode
        if original_mode=='RGBA':
            background=Image.new('RGBA',image.size,'white');background.alpha_composite(image);pixels=background.convert('RGB')
        else:pixels=image.convert('RGB')
    box=spec['crop_box']
    if (not isinstance(box,list) or len(box)!=4 or any(type(x) is not int for x in box)
            or not 0<=box[0]<box[2]<=pixels.width or not 0<=box[1]<box[3]<=pixels.height):
        raise ValueError('Source crop must be an integer rectangle inside the supplied tile')
    return pixels,dict(spec,path=str(path),original_mode=original_mode,rgb_dimensions=list(pixels.size))


def _destination(placement,size):
    if set(placement)!={'id','width_fraction','height_fraction','left_fraction','top_fraction'}:
        raise ValueError('Explicit fractional destination geometry required')
    _identifier(placement['id'])
    w,h,x,y=[placement[k] for k in ('width_fraction','height_fraction','left_fraction','top_fraction')]
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (w,h,x,y)):
        raise ValueError('Finite fractional destination geometry required')
    if not (0<w<=1 and 0<h<=1 and 0<=x<1 and 0<=y<1 and x+w<=1+1e-12 and y+h<=1+1e-12):
        raise ValueError('Destination clipping is forbidden; box must be inside host')
    width=max(1,round(size[0]*w));height=max(1,round(size[1]*h))
    left=round(size[0]*x);top=round(size[1]*y)
    box=(left,top,left+width,top+height)
    if box[2]>size[0] or box[3]>size[1]:raise ValueError('Rounded destination exceeds host; no clipping')
    return box


def prepare(plan_path,output):
    """Write four controls for each pair/placement, plus pixel masks/provenance.

    Parent identity is asserted by the supplied provenance and content hashes;
    this preparation does not independently authenticate a slide ID or patient.
    The cut/reinsert image is an identity null edit, not a matched foreign seam.
    """
    plan_path=Path(plan_path);plan_bytes=plan_path.read_bytes();plan=json.loads(plan_bytes)
    if set(plan)!={'schema_version','source_kind','pairs','placements','interpolation'} or plan['schema_version']!=1:
        raise ValueError('Versioned explicit pixel-control plan required')
    if plan['source_kind'] not in ('real','fixture') or plan['interpolation'] not in RESAMPLERS:
        raise ValueError('Explicit real/fixture provenance and supported interpolation required')
    if not plan['pairs'] or not plan['placements'] or len(plan['pairs'])*len(plan['placements'])*4>MAX_VARIANTS:
        raise ValueError('A nonempty study of at most 96 variants is required')
    if len({_identifier(p['id']) for p in plan['pairs']})!=len(plan['pairs']):raise ValueError('Duplicate pair IDs')
    if len({_identifier(p['id']) for p in plan['placements']})!=len(plan['placements']):raise ValueError('Duplicate placement IDs')
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve existing output; choose a new study directory')
    prepared=[]
    # Validate every supplied image, geometry and mandatory sham before any output.
    for pair in plan['pairs']:
        if set(pair)!={'id','host','donor','native_sham'}:raise ValueError('Foreign, same-source sham and host parents required')
        loaded={role:_source(pair[role]) for role in ('host','donor','native_sham')}
        if pair['host']['slide_id']==pair['donor']['slide_id']:raise ValueError('Foreign donor must have a distinct supplied slide ID')
        if pair['host']['slide_id']!=pair['native_sham']['slide_id']:raise ValueError('Native sham must have the supplied host slide ID')
        host=loaded['host'][0]
        if pair['host']['crop_box']!=[0,0,host.width,host.height]:raise ValueError('Host crop must retain the entire supplied tile')
        boxes=[_destination(p,host.size) for p in plan['placements']]
        if len(set(boxes))!=len(boxes):raise ValueError('Rounded placements duplicate one another')
        for box in boxes:
            if loaded['native_sham'][1]['path']==loaded['host'][1]['path'] and tuple(pair['native_sham']['crop_box'])==box:
                raise ValueError('Native sham must copy a different native patch; null edit is a separate control')
        prepared.append((pair,loaded,boxes))
    output.mkdir(parents=True,exist_ok=False);records=[]
    for pair,loaded,boxes in prepared:
        host=loaded['host'][0];host_pixels=np.asarray(host)
        for placement,box in zip(plan['placements'],boxes):
            target=np.zeros((host.height,host.width),dtype=np.uint8);target[box[1]:box[3],box[0]:box[2]]=255
            extent=(box[2]-box[0],box[3]-box[1])
            for variant in VARIANTS:
                image=host.copy();source_role=None;source_box=None
                if variant in ('foreign_patch','native_sham'):
                    source_role='donor' if variant=='foreign_patch' else 'native_sham'
                    source_box=loaded[source_role][1]['crop_box']
                    patch=loaded[source_role][0].crop(source_box).resize(extent,RESAMPLERS[plan['interpolation']])
                    image.paste(patch,box[:2])
                elif variant=='cut_reinsert_null':
                    source_role='host';source_box=list(box)
                    image.paste(host.crop(box),box[:2])
                pixels=np.asarray(image);changed=(pixels!=host_pixels).any(axis=2).astype(np.uint8)*255
                foreign=target if variant=='foreign_patch' else np.zeros_like(target)
                stem=pair['id']+'__'+placement['id']+'__'+variant
                files={}
                for suffix,raster in [('image',image),('target_mask',Image.fromarray(target)),
                        ('foreign_mask',Image.fromarray(foreign)),('changed_mask',Image.fromarray(changed))]:
                    name=stem+'__'+suffix+'.png';raster.save(output/name)
                    files[suffix]=dict(path=name,sha256=sha256(output/name))
                records.append(dict(pair_id=pair['id'],placement_id=placement['id'],variant=variant,
                    host_slide_id=pair['host']['slide_id'],donor_slide_id=pair['donor']['slide_id'],
                    destination_box_xyxy=list(box),requested_geometry=placement,source_role=source_role,source_box_xyxy=source_box,
                    image_dimensions=list(host.size),requested_area_fraction=placement['width_fraction']*placement['height_fraction'],
                    realized_area_fraction=float((target>0).mean()),changed_pixel_fraction=float((changed>0).mean()),
                    composition='hard rectangular paste; no feathering or color harmonization' if variant in ('foreign_patch','native_sham') else 'identity/null operation',
                    interpolation=plan['interpolation'] if variant in ('foreign_patch','native_sham') else 'none',
                    clipping='none; out-of-bounds inputs rejected',pixel_sha256=hashlib.sha256(pixels.tobytes()).hexdigest(),files=files))
    parents=[dict(pair_id=p['id'],parents={role:spec for role,(_,spec) in loaded.items()}) for p,loaded,_ in prepared]
    for pair in parents:
        for parent in pair['parents'].values():
            if sha256(parent['path'])!=parent['sha256']:raise RuntimeError('Parent changed during preparation; incomplete outputs retained')
    if plan_path.read_bytes()!=plan_bytes:raise RuntimeError('Plan changed during preparation; incomplete outputs retained')
    manifest=dict(schema_version=1,source_kind=plan['source_kind'],plan_sha256=hashlib.sha256(plan_bytes).hexdigest(),
        variants=len(records),parents=parents,records=records,encoder_inference_run=False,scientific_results=False,
        color_processing='convert RGB; RGBA composited on white; no EXIF rotation',
        geometry_rounding='Python round to nearest integer, ties to even; minimum one pixel; no clipping',
        mask_semantics=dict(target_mask='requested rectangular footprint, including controls',foreign_mask='donor source footprint only; zero for all controls',
            changed_mask='RGB inequality to original host, not foreignness ground truth'),
        limitations=['Tile composites are not physical embedded tissue fragments',
            'Cut/reinsert is a pixel-identical null edit and does not match foreign-seam morphology',
            'Same-source sham uses the same hard boundary and interpolation but cannot eliminate all seam/morphology confounding',
            'Supplied slide IDs and same-source relationships require upstream verification; hashes establish byte identity only',
            'No new CONCH inference; encoder/GPU study requires explicit approval'])
    with (output/'manifest.json').open('x') as handle:json.dump(manifest,handle,indent=2,allow_nan=False);handle.write('\n')
    return manifest
