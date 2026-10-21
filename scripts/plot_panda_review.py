#!/usr/bin/env python3
"""Reproduce development-only scientific figures from committed measured summaries."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image
from floater_finder.experiments import file_sha256


def plot(selection,diagnostics,qa,output):
    s=json.loads(Path(selection).read_text());d=json.loads(Path(diagnostics).read_text());q=json.loads(Path(qa).read_text())
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','svg.hashsalt':'panda-review-v1'})
    titles=['Combined','Visual only','Decision only','Spatial only'];names=['combined','visual_only','decision_only','spatial_only'];colors=['#147d92','#758697','#c36b36','#7566a4']
    def save(fig,name):
        fig.savefig(out/(name+'.png'),dpi=180);svg=out/(name+'.svg');fig.savefig(svg,metadata={'Date':None});plt.close(fig)
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    fig,axes=plt.subplots(1,3,figsize=(13,4.7),layout='constrained')
    cal=[s['comparison'][n]['calibration'] for n in names];x=np.arange(4)
    values=[[m['fragment_recall'] for m in cal],[m['unmodified_alert_rate'] for m in cal],[m['clean_damage_rate'] for m in cal]]
    labels=['Fragments hit / 40 positive-dose trials','Alerts / 24 unmodified slides','Hypothetical damage / 20 correct slides']
    counts=[[int(round(m['fragment_recall']*40)) for m in cal],[m['unmodified_alerts'] for m in cal],[m['clean_hypothetical_damage'] for m in cal]]
    denoms=[40,24,20]
    for j,ax in enumerate(axes):
        ax.bar(x,values[j],color=colors,width=.7)
        for i,v in enumerate(values[j]):ax.text(i,v+.035,f'{counts[j][i]}/{denoms[j]}',ha='center',bbox=dict(facecolor='white',edgecolor='none',pad=.2))
        ax.set(xticks=x,xticklabels=titles,ylim=(0,1.07),ylabel=labels[j]);ax.tick_params(axis='x',labelrotation=25)
    axes[0].axhline(.2,color='#555',ls='--',lw=1,label='Engineering utility target');axes[0].legend(fontsize=8)
    axes[1].axhline(.1,color='#555',ls='--',lw=1,label='User burden target');axes[1].legend(fontsize=8)
    axes[2].axhline(.05,color='#555',ls='--',lw=1,label='Engineering harm target');axes[2].legend(fontsize=8)
    fig.suptitle('PANDA calibration · review tradeoff fails\n40 mixtures reuse 8 hosts; 8 induced-error instances affect 2 hosts; no held-out test predictions',fontsize=13)
    save(fig,'review_tradeoff')
    fig,axes=plt.subplots(1,2,figsize=(10.5,4.8),layout='constrained')
    for i,(ax,key,title) in enumerate(zip(axes,['mean_components_per_unmodified_slide','genuine_cancer_components_flagged'],['Reviewer burden per unmodified slide','Genuine annotated cancer components flagged'])):
        ax.bar(x,[m[key] for m in cal],color=colors);ax.set(xticks=x,xticklabels=titles,title=title);ax.tick_params(axis='x',labelrotation=25)
        for a,m in enumerate(cal):ax.text(a,m[key]+(.06 if i==0 else .08),f'{m[key]:.2f}' if i==0 else f'{m[key]}/26',ha='center')
        ax.set_ylim(0,max(m[key] for m in cal)*1.2+.15)
    axes[0].axhline(.5,color='#555',ls='--',lw=1,label='User burden target');axes[0].legend(fontsize=8)
    fig.suptitle('PANDA calibration · all tissue retained\nAnnotation is a negative control for foreignness; genuine cancer may be decisive',fontsize=13)
    save(fig,'review_burden_and_genuine_tissue')
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),layout='constrained')
    keys=['positive_trials','mapped_foreign_component','visual_pass','visual_and_influence_pass','combined_pass']
    labels=['Injected\ntrials','Mapped foreign\ncomponent','+ visual\nthreshold','+ influence\nthreshold','+ spatial\nthreshold']
    for ax,split in zip(axes,('train','calibration')):
        counts=[d['splits'][split]['foreign_truth_diagnostic_funnel'][k] for k in keys]
        ax.bar(np.arange(5),counts,color='#147d92');ax.set(xticks=np.arange(5),xticklabels=labels,title=split.capitalize(),ylabel='Positive-dose trial instances');ax.tick_params(axis='x',labelsize=9)
        for i,v in enumerate(counts):ax.text(i,v+max(counts)*.025,str(v),ha='center')
        ax.set_ylim(0,max(counts)*1.17)
    fig.suptitle('Frozen combined-policy failure funnel\nInjection truth used only to describe misses; thresholds and topology unchanged',fontsize=13)
    save(fig,'review_failure_funnel')
    fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained');axes=axes.ravel()
    for ax,choice in zip(axes,q['choices']):
        sid=choice['image_id'];path=Path(qa).parent/sid/'tissue_edges.png'
        if file_sha256(path)!=q['files'][str(path)]['sha256']:raise ValueError('QA image differs')
        with Image.open(path) as image:ax.imshow(image)
        r=choice['record'];ax.set_title(f"{sid[:10]}… · {choice['reason']}\nSampled {r['old_sampled_components']} → observed {r['new_observed_components']} components; mapped {r['mapping_fraction']:.0%}\nPrimary/lenient membership agreement {r['sensitivity_pairwise_membership_agreement']:.1%}",fontsize=9);ax.axis('off')
    fig.suptitle('Training tissue-topology quality checks · actual RGB overviews\nBlue = selected foreground edge proxy; no gap filling or invented tissue bridges',fontsize=13)
    save(fig,'topology_quality_checks')
    fig,ax=plt.subplots(figsize=(12,6.5),layout='constrained');ax.set(xlim=(0,12),ylim=(0,6));ax.axis('off')
    boxes=[(.1,3.6,'PANDA Radboud\n120 real slides\n72 train / 24 cal / 24 test'),(4.1,3.6,'Bounded representative tiles\n112 µm field; physical coordinates\nClean sampling ignores masks'),(8.1,3.6,'Frozen CONCH v1\n50,729 saved 512D embeddings\nNo new GPU inference'),(.1,.8,'Benign / cancer scorer\nFixed prompts + top-5% pooling\n24 test slides remain unscored'),(4.1,.8,'Observed RGB components\nVisual inconsistency + influence\nMeasured area + isolation proxy'),(8.1,.8,'Pathologist review candidate\nPreserve tissue and baseline\nRejected: insufficient utility')]
    for x0,y0,text in boxes:
        ax.add_patch(FancyBboxPatch((x0,y0),3.7,1.5,boxstyle='round,pad=.08',facecolor='#e8f0f2',edgecolor='#147d92'));ax.text(x0+1.85,y0+.75,text,ha='center',va='center',fontsize=10)
    for a,b in [((3.85,4.35),(4,4.35)),((7.85,4.35),(8,4.35)),((9.9,3.45),(1.95,2.4)),((3.85,1.55),(4,1.55)),((7.85,1.55),(8,1.55))]:ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color='#43545b',lw=1.5))
    ax.set_title('Floater Finder · CONCH-only engineering evaluation\nSynthetic foreign tissue and genuine cancer controls; no automatic tissue removal',fontsize=14,pad=16)
    save(fig,'pipeline_and_protocol')
    manifest=dict(source_kind='real',test_predictions_computed=False,script_sha256=file_sha256(__file__),inputs={str(p):file_sha256(p) for p in (selection,diagnostics,qa)},figures={p.name:file_sha256(p) for p in sorted(out.iterdir())},matched_control_limitation='Calibration primary has zero flags, so burden-matched random controls also have zero flags and are uninformative.')
    (out/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('selection','diagnostics','qa','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();plot(a.selection,a.diagnostics,a.qa,a.output)
