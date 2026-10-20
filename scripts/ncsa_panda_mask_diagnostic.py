#!/usr/bin/env python3
"""Read-only, bounded two-decoder diagnosis of a failed PANDA annotation mask."""
import argparse,json,os,warnings
from pathlib import Path
import numpy as np
from PIL import Image,features
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256
from floater_finder.panda import panda_input,panda_readers,LABELS
from floater_finder.panda_masks import audit_mask


def run(root,manifest,image_id,output,max_native_pixels=150_000_000):
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('Native mask diagnosis requires Slurm')
    if type(max_native_pixels) is not int or not 1<=max_native_pixels<=200_000_000:raise ValueError('Independent mask bound must be at most 200 million pixels')
    item=panda_input(root,image_id,manifest);mask_path=item['mask_path']
    report=dict(image_id=image_id,slurm_job_id=os.environ['SLURM_JOB_ID'],mask_path=str(mask_path),
        mask_sha256=file_sha256(mask_path),pillow_libtiff_version=features.version('libtiff'),inputs_modified=False,max_independent_native_pixels=max_native_pixels)
    try:
        with panda_readers(item['image_path'],mask_path) as (_,mask,meta):
            report['header']=meta;report['openslide_audit']=audit_mask(mask,meta['measured_mpp_xy'])
    except Exception as error:
        report['openslide_error']=dict(type=type(error).__name__,message=str(error)[:500])
    Image.MAX_IMAGE_PIXELS=max_native_pixels
    try:
        with Image.open(mask_path) as image:
            if image.width*image.height>max_native_pixels:raise ValueError('Mask exceeds bounded independent full-plane diagnostic')
            with warnings.catch_warnings(record=True) as caught:
                image.load();array=np.asarray(image)
            if caught:raise ValueError('Independent decoder emitted warnings')
            if array.ndim!=3 or array.shape[2] not in (3,4):raise ValueError('Unexpected mask channels')
            counts=np.zeros(6,dtype=np.int64)
            for y in range(0,image.height,512):
                block=array[y:y+512,:,0]
                if not np.isin(block,range(6)).all():raise ValueError('Invalid Radboud labels')
                counts+=np.bincount(block.ravel(),minlength=6)
            report['pillow_native_pixel_counts']=dict(zip(LABELS,map(int,counts)))
            report['pillow_native_decode_passed']=True
    except Exception as error:
        report['pillow_native_decode_passed']=False
        report['pillow_error']=dict(type=type(error).__name__,message=str(error)[:500])
    report['mask_sha256_after']=file_sha256(mask_path)
    assert report['mask_sha256']==report['mask_sha256_after']
    write_json(output,report);print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','manifest','image-id','output'):p.add_argument('--'+name,required=True)
    p.add_argument('--max-native-pixels',type=int,default=150_000_000)
    a=p.parse_args();run(a.root,a.manifest,a.image_id,a.output,a.max_native_pixels)
