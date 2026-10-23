#!/usr/bin/env python3
"""Plot measured saved tile footprints, native annotation fractions and counterfactual components."""
import argparse,csv,io,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256


def plot(inputs,examples,trials,genuine_report,foreign_report,output):
    data=json.loads(Path(inputs).read_text());chosen=json.loads(Path(examples).read_text())['examples']
    all_trials=json.loads(Path(trials).read_text());output=Path(output);output.mkdir(parents=True,exist_ok=False)
    trial=next(r for r in all_trials if r['host_id']==chosen['synthetic_foreign']['slide_id'] and r['requested_percent']==chosen['synthetic_foreign']['requested_percent'])
    fig,flat=plt.subplots(1,4,figsize=(12,6.7),layout='constrained');axes=flat.reshape(2,2)
    for i,(kind,path) in enumerate([('genuine_cancer',genuine_report),('synthetic_foreign',foreign_report)]):
        report=json.loads(Path(path).read_text());sid=chosen[kind]['slide_id'];item=data[sid]
        assert report['source_kind']=='real' and report['alerts_evaluated'] is False
        rows=list(csv.DictReader(io.StringIO(item['csv'])))
        coords=np.array([[float(r['x']),float(r['y'])] for r in rows])
        fraction=np.array([sum(float(r[f'gleason{g}_fraction']) for g in (3,4,5)) for r in rows])
        foreign=np.zeros(len(rows),dtype=bool)
        if kind=='synthetic_foreign':
            donors={r['tile_id']:r for r in csv.DictReader(io.StringIO(data[trial['donor_id']]['csv']))}
            selected=[donors[t] for t in trial['donor_tile_ids']]
            extra=np.array([[float(r['x']),float(r['y'])] for r in selected])+np.array(trial['synthetic_injection']['translation_um'])
            coords=np.concatenate([coords,extra]);fraction=np.r_[fraction,[sum(float(r[f'gleason{g}_fraction']) for g in (3,4,5)) for r in selected]]
            foreign=np.r_[foreign,np.ones(len(selected),dtype=bool)]
        assert len(coords)==report['tile_count']
        pieces=[p for p in report['pieces'] if p['decision_changing'] and
                (p['evaluation_only_synthetic_foreign_tiles']==p['tile_count'] if kind=='synthetic_foreign' else
                 (p['evaluation_only_annotated_cancer_area_mm2'] or 0)>0 and p['counterfactual']['result']['prediction']=='benign')]
        piece=min(pieces,key=lambda p:p['area_mm2']);highlight=np.zeros(len(coords),dtype=bool);highlight[piece['tile_indices']]=True
        size=np.array(item['metadata']['tile_size'])/1000;coords=coords/1000
        patches=[Rectangle(xy,*size) for xy in coords]
        for j,ax in enumerate(axes[i]):
            colors=plt.get_cmap('Reds')(fraction) if j==0 else np.where(highlight[:,None],np.array([.10,.48,.62,1]),np.array([.83,.86,.88,1]))
            colors[fraction==0]=[.86,.89,.90,1] if j==0 else colors[fraction==0]
            ax.add_collection(PatchCollection(patches,facecolors=colors,edgecolors='white',linewidths=.15))
            if foreign.any():
                ax.add_collection(PatchCollection([patches[k] for k in np.flatnonzero(foreign)],facecolors='none',edgecolors='#8b1414',linewidths=1.1))
            ax.autoscale_view();ax.set_aspect('equal');ax.invert_yaxis();ax.set(xlabel='Slide x (mm)',ylabel='Slide y (mm)')
        axes[i,0].set_title(('Unmodified GG1\nNative cancer fractions' if kind=='genuine_cancer' else f"Synthetic mixture\n{trial['foreign_tiles']} foreign / {trial['host_tiles']} host tiles\nRed outline = known injection"),fontsize=10)
        axes[i,1].set_title(f"Exclude blue component\n{report['baseline']['prediction']} → {piece['counterfactual']['result']['prediction']}\n{piece['tile_count']} tiles; {piece['area_mm2']:.3f} mm²",fontsize=10)
    bar=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,1),cmap='Reds'),ax=list(flat),orientation='horizontal',fraction=.04,pad=.06,shrink=.65,aspect=45)
    bar.set_label('Native GP3+GP4+GP5 fraction per saved tile')
    fig.suptitle('Real PANDA saved-tile component examples · development only\nTile footprints, not whole-slide tissue images · dependence does not establish foreign tissue',fontsize=12)
    fig.savefig(output/'piece_examples.png',dpi=180);plt.close(fig)
    write_json(output/'provenance.json',dict(source_kind='real',test_slides_scored=False,plot_source_sha256=file_sha256(__file__),
        inputs={str(p):file_sha256(p) for p in (inputs,examples,trials,genuine_report,foreign_report)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','examples','trials','genuine-report','foreign-report','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();plot(a.inputs,a.examples,a.trials,a.genuine_report,a.foreign_report,a.output)
