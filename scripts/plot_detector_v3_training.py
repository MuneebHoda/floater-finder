#!/usr/bin/env python3
"""Reproduce scientific plots from measured detector-v3 artifacts, without arrays."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from floater_finder.experiments import file_sha256
from floater_finder.artifacts import write_json

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report',type=Path,required=True)
parser.add_argument('--observations',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
a=parser.parse_args();r=json.loads(a.report.read_text());obs=json.loads(a.observations.read_text())
a.output.mkdir(parents=True,exist_ok=False)
methods=list(r['methods']);colors=plt.colormaps['tab10'](np.arange(len(methods)))
labels=[m.replace('_',' ') for m in methods]
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','svg.hashsalt':'floater-finder-detector-v3-training-v1'})

def save(fig,name):
    fig.savefig(a.output/(name+'.png'),dpi=180,bbox_inches='tight')
    svg=a.output/(name+'.svg')
    fig.savefig(svg,bbox_inches='tight',metadata={'Date':None})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(12,4.5))
x=np.arange(len(methods))
for j,(key,ci,title) in enumerate([('fragment_recall','fragment_recall_host_bootstrap95','Synthetic fragment recall (120 cases / 24 hosts)'),
        ('unmodified_alert_rate','unmodified_alert_wilson95','Unmodified slide alert rate (72 slides)')]):
    values=[r['methods'][m]['two_stage'][key] for m in methods]
    axes[j].bar(x,values,color=colors)
    for i,m in enumerate(methods):
        low,high=r['methods'][m]['two_stage'][ci]
        axes[j].plot([i,i],[low,high],color='black',lw=1.2)
    axes[j].set_xticks(x,labels,rotation=55,ha='right');axes[j].set_ylim(0,1);axes[j].set_title(title)
    axes[j].set_ylabel('Rate')
axes[0].axhline(.2,color='black',ls='--',label='20% engineering recall target');axes[0].legend(fontsize=8)
axes[1].axhline(.1,color='black',ls='--',label='10% clean review budget');axes[1].legend(fontsize=8)
fig.suptitle('Detector v3: slide-grouped training cross-fit; no independent validation')
fig.tight_layout();save(fig,'operating_points')

fig,axes=plt.subplots(1,2,figsize=(11,4.5))
for m,color,label in zip(methods,colors,labels):
    points=r['methods'][m]['sensitivity']
    axes[0].plot([p['metrics']['unmodified_alert_rate'] for p in points],[p['metrics']['fragment_recall'] for p in points],'-o',color=color,label=label,ms=3)
    axes[1].plot([p['metrics']['mean_components_per_unmodified_slide'] for p in points],[p['metrics']['fragment_recall'] for p in points],'-o',color=color,ms=3)
axes[0].axvline(.1,color='black',ls='--');axes[1].axvline(.5,color='black',ls='--')
for ax in axes:ax.set_ylim(0,1);ax.set_ylabel('Synthetic fragment recall');ax.grid(alpha=.15)
axes[0].set_xlabel('Unmodified slide alert rate');axes[1].set_xlabel('Mean review components / clean slide')
axes[0].legend(fontsize=8);fig.suptitle('Training sensitivity: nine thresholds fitted within each clean fitting fold')
fig.tight_layout();save(fig,'recall_burden_curves')

fig,ax=plt.subplots(figsize=(7.5,5.5))
for m,color,label in zip(methods,colors,labels):
    pr=r['ranking'][m]['host_equal_weight_pr'];p=pr['points']
    ax.plot([x['recall'] for x in p],[x['precision'] for x in p],color=color,label=f"{label}: AP {pr['average_precision']:.3f}")
ax.set(xlabel='Component recall',ylabel='Component precision',xlim=(0,1),ylim=(0,1),title='Training out-of-fold component ranking')
ax.legend(fontsize=8);ax.grid(alpha=.15)
fig.text(.12,.01,'Ties enter together; each host has equal total weight. Reused doses/donors are dependent.',fontsize=8)
fig.tight_layout(rect=(0,.04,1,1));save(fig,'precision_recall')

fig,axes=plt.subplots(2,4,figsize=(13,7.5))
for ax,m,label in zip(axes.flat,methods,labels):
    for name,key,color in [('Native annotated cancer','native','tab:blue'),('Majority foreign','foreign','tab:orange')]:
        selected=[x for x in obs[m] if x['kind']=='unmodified' and x['genuine_native_cancer']] if key=='native' else [x for x in obs[m] if x['majority_foreign']]
        values=sorted(x['score'] for x in selected)
        if values:ax.step(values,np.arange(1,len(values)+1)/len(values),where='post',color=color,label=f'{name} n={len(values)}')
    ax.set_title(label);ax.set_xlabel('Method-specific anomaly score');ax.set_ylabel('Empirical fraction');ax.legend(fontsize=6);ax.grid(alpha=.15)
axes.flat[-1].axis('off')
fig.suptitle('Native cancer can be morphologically unusual: training-only identifiability check')
fig.text(.06,.01,'Observed component proxies; native controls are unmodified. Foreign components recur across doses; not independent specimens.',fontsize=8)
fig.tight_layout(rect=(0,.04,1,.97));save(fig,'native_foreign_overlap')

fig,axes=plt.subplots(1,2,figsize=(11,4.5));width=.36
for ax,key,title in [(axes[0],'fragment_recall','Fragment recall'),(axes[1],'genuine_cancer_components_flagged','Native cancer components flagged (clean)')]:
    visual=[r['methods'][m]['two_stage'][key] for m in methods]
    veto=[r['methods'][m]['and_influence_comparator'][key] for m in methods]
    ax.bar(x-width/2,visual,width,label='Visual shortlist + influence explanation',color='tab:blue')
    ax.bar(x+width/2,veto,width,label='Same shortlist AND influence ≥0.01',color='tab:orange')
    ax.set_xticks(x,labels,rotation=55,ha='right');ax.set_title(title)
axes[0].set_ylim(0,1);axes[0].legend(fontsize=7)
fig.suptitle('Two-stage review preserves visual shortlists; influence is not proof of foreignness')
fig.tight_layout();save(fig,'two_stage_vs_and')
write_json(a.output/'provenance.json',dict(source_kind='real',scope='training-only cross-fit',slurm_job_id=r['slurm_job_id'],
    source_commit=r['source_commit'],report_sha256=file_sha256(a.report),observations_sha256=file_sha256(a.observations),
    plotter_sha256=file_sha256(__file__),plots={p.name:file_sha256(p) for p in a.output.iterdir()},prediction_action='none',held_out_predictions=False))
