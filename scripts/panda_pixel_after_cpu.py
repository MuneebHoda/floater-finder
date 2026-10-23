#!/usr/bin/env python3
"""Resolve a successful frozen CPU preparation before the approved GPU runner."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def resolve(project,source_manifest_sha256,source_commit,config_sha256,cpu_job):
    project=Path(project).resolve();manifest_path=project.parent/'source_manifest.json'
    if sha(manifest_path)!=source_manifest_sha256:raise ValueError('Frozen runtime source manifest changed')
    source=json.loads(manifest_path.read_text())
    if source['source_commit']!=source_commit:raise ValueError('Frozen runtime source commit changed')
    for name,digest in source['files'].items():
        path=(project/name).resolve()
        if not path.is_relative_to(project) or sha(path)!=digest:raise ValueError('Frozen runtime source file changed')
    # Import only after verifying the unchanged runtime bundle; no encoder/model call here.
    from floater_finder.research.pixel_study import preflight,prepared_inputs
    c=preflight(project/'configs/panda_pixel_contamination_v1.json',config_sha256,project,True)
    preparation=Path(c['preparation_output']);completion_path=preparation/'completion.json'
    completion=json.loads(completion_path.read_text())
    if (completion['status']!='prepared_verified_no_inference' or completion['source_commit']!=source_commit or
            completion['protocol_sha256']!=config_sha256 or completion['images']!=96):
        raise ValueError('Successful frozen CPU completion required')
    digest=sha(preparation/'image_manifest.json');m=prepared_inputs(preparation,digest)
    pairs=[{k:p[k] for k in ('id','task','host','donor')} for p in m['pairs']]
    if (m['slurm_job_id']!=cpu_job or m['source_commit']!=source_commit or m['protocol_sha256']!=config_sha256 or
            m['source_kind']!='real' or m['experiment_id']!=c['experiment_id'] or pairs!=c['pairs'] or
            m['inference_executed'] or m['scientific_effects_measured'] or m['final_test_accessed']):
        raise ValueError('Exact successful training-only CPU job and predetermined pairs required')
    if Path(c['gpu_output']).exists():raise FileExistsError('Preserve existing GPU output; never duplicate inference')
    command=['/bin/bash',str(project/'scripts/slurm/panda_pixel_encode.sbatch')]
    receipt=dict(status='real_manifest_frozen_before_encoder',cpu_job_id=cpu_job,source_commit=source_commit,
        source_manifest_sha256=source_manifest_sha256,protocol_sha256=config_sha256,
        preparation=str(preparation),manifest_sha256=digest,completion_sha256=sha(completion_path),images=96,
        inference_executed=False,scientific_results=False)
    return c,command,receipt


def execute(a):
    if not os.environ.get('SLURM_JOB_ID') or not os.environ.get('SLURM_JOB_GPUS'):
        raise RuntimeError('Approved dependent GPU Slurm allocation required')
    c,command,receipt=resolve(a.project,a.source_manifest_sha256,a.source_commit,a.config_sha256,a.cpu_job)
    receipt['gpu_job_id']=os.environ['SLURM_JOB_ID']
    path=Path(c['gpu_output']).parent/('pixel-contamination-gpu-launch-'+receipt['gpu_job_id']+'.json')
    with path.open('x') as handle:json.dump(receipt,handle,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps(dict(status=receipt['status'],manifest_sha256=receipt['manifest_sha256'],cpu_job_id=a.cpu_job)),flush=True)
    command.extend([a.project,a.runtime,a.config_sha256,c['preparation_output'],receipt['manifest_sha256'],c['gpu_output'],a.source_commit])
    os.execv(command[0],command)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',required=True);p.add_argument('--runtime',required=True)
    p.add_argument('--source-manifest-sha256',required=True);p.add_argument('--source-commit',required=True)
    p.add_argument('--config-sha256',required=True);p.add_argument('--cpu-job',required=True)
    execute(p.parse_args())
