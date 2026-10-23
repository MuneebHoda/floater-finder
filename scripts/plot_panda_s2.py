#!/usr/bin/env python3
"""Reproduce S2 measured-result figures; does not load embeddings, images or held-out inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
a=parser.parse_args()
summary=json.loads((a.input_dir/'summary.json').read_text())
trials=json.loads((a.input_dir/'trials.json').read_text())
rows=summary['metrics']; a.output_dir.mkdir(parents=True,exist_ok=False)
colors={'high_gp45':'#AC3A40','same_grade_gp3_only':'#287C7F','high_gp4_only':'#C28B2F','high_gp5_positive':'#6B5B95'}
labels={'high_gp45':'High-slide GP4/5+','same_grade_gp3_only':'GG1 GP3+; no GP4/5','high_gp4_only':'GP4+; no GP5','high_gp5_positive':'GP5+ (GP3/4 allowed)'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','svg.hashsalt':'floater-s2-v1'})
fig,axes=plt.subplots(2,2,figsize=(13,9),layout='constrained')
for condition in colors:
    selected=[r for r in rows if r['split']=='calibration' and r['pooling']=='mean' and r['condition']==condition and r['hosts']]
    if not selected:continue
    xs=[r['requested_percent'] for r in selected]
    axes[0,0].plot(xs,[100*r['new_error_rate'] if r['new_error_rate'] is not None else np.nan for r in selected],'-o',color=colors[condition],label=labels[condition],markersize=4)
    axes[1,0].plot(xs,[r['mean_high_minus_low_margin_change'] for r in selected],'-o',color=colors[condition],markersize=4,label=labels[condition])
axes[0,0].set(title='Primary mean pooling: calibration new errors',xlabel='Foreign tiles / original host tiles (%)',ylabel='Originally correct low hosts becoming high (%)',ylim=(-3,103))
axes[0,0].legend(fontsize=8)
axes[0,0].text(.03,.80,'All observed primary calibration errors: 0/8 per dose\nGP5+ at 10% unavailable (connected capacity)',transform=axes[0,0].transAxes,fontsize=8,va='top')
for pooling,color in [('mean','#287C7F'),('top1pct','#AC3A40'),('top5pct','#C28B2F')]:
    selected=[r for r in rows if r['split']=='calibration' and r['pooling']==pooling and r['condition']=='high_gp45' and r['hosts']]
    if not selected:continue
    denominators='/'.join(map(str, sorted({r['originally_correct_low_hosts'] for r in selected})))
    axes[0,1].plot([r['requested_percent'] for r in selected],[100*r['new_error_rate'] if r['new_error_rate'] is not None else np.nan for r in selected],'-o',color=color,label=f'{pooling}; correct-host n={denominators}',markersize=4)
axes[0,1].set(title='GP4/5+ donor: pooling sensitivity',xlabel='Foreign tiles / original host tiles (%)',ylabel='New low-to-high errors (%)',ylim=(-3,103));axes[0,1].legend(fontsize=8)
axes[1,0].axhline(0,color='#888888',linewidth=.8)
axes[1,0].set(title='Primary mean pooling: raw margin shift',xlabel='Foreign tiles / original host tiles (%)',ylabel='Change in high-minus-low cosine margin')
for split,marker in [('train','o'),('calibration','s')]:
    data=[r for r in trials if r['split']==split and r['condition']=='high_gp45' and r['requested_percent']==10 and r['visual_distance_to_native_donor_context'] is not None]
    axes[1,1].scatter([r['visual_distance_to_native_donor_context'] for r in data],[r['visual_distance_to_host'] for r in data],label=f'{split} hosts (n={len(data)})',marker=marker,alpha=.7,s=30)
values=[v for r in trials if r['condition']=='high_gp45' and r['requested_percent']==10 for v in (r['visual_distance_to_native_donor_context'],r['visual_distance_to_host']) if v is not None]
if values:
    lo,hi=min(values),max(values);axes[1,1].plot([lo,hi],[lo,hi],'--',color='#777777',linewidth=1)
axes[1,1].set(title='Same 10% fragment, different observed contexts',xlabel='Median nearest-5 cosine distance to native donor',ylabel='Median nearest-5 cosine distance to host');axes[1,1].legend(fontsize=8)
fig.suptitle('PANDA S2 development: synthetic embedding stress, not clinical grading',fontsize=15)
for ext in ('png','svg'):
    path=a.output_dir/('s2_development.'+ext)
    fig.savefig(path,dpi=180,**({'metadata':{'Date':None}} if ext=='svg' else {}))
    if ext=='svg':path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
plt.close(fig)
provenance=dict(source_kind='real',scope='training/calibration only; no independent held-out test',source_commit=summary['source_commit'],slurm_job_id=summary['slurm_job_id'],primary_pooling=summary['primary_pooling'],input_sha256={name:hashlib.sha256((a.input_dir/name).read_bytes()).hexdigest() for name in ('summary.json','trials.json')},figure_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.output_dir.iterdir()},limitations=['Synthetic right-edge placement is not a natural floater.','Binary low/high changes are not clinical Gleason Grade Group upgrades.','Controls overlap and reuse donor slides.','Repeated doses are not independent patients.','GP4-positive/noGP5 can include GP3; GP5-positive can include GP3/4.','Visual context diagnostic is annotation-informed, not a blinded detector.'])
(a.output_dir/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
