#!/usr/bin/env python3
"""Plot executed development S1 stress metrics, retaining their host denominators."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256


def plot(summary,output):
    report=json.loads(Path(summary).read_text())
    assert report['source_kind']=='real' and report['test_slides_scored'] is False
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    fig,axes=plt.subplots(2,2,figsize=(10.5,7.2),layout='constrained')
    for i,split in enumerate(('train','calibration')):
        for rule,color in [('mean','#62717c'),('top1pct','#c17c24'),('top5pct','#23789d')]:
            rows=sorted([r for r in report['metrics'] if r['split']==split and r['pooling']==rule],key=lambda r:r['requested_percent'])
            assert len(rows)==6 and all(r['hosts']>0 and 0<=r['prediction_changes']<=r['hosts'] for r in rows)
            x=[r['requested_percent'] for r in rows]
            axes[i,0].plot(x,[r['prediction_changes']/r['hosts'] for r in rows],'-o',color=color,label=rule)
            axes[i,1].plot(x,[r['contaminated_host_accuracy'] for r in rows],'-o',color=color,label=rule)
        n=rows[0]['hosts']
        for j,title in enumerate(('Prediction changes from clean','Original benign-host label retained')):
            axes[i,j].set(title=f'{split}: {title}\n{n} host slides; one donor per host',xlabel='Requested foreign tiles / original host tiles (%)',ylabel='Fraction of host slides',ylim=(-.03,1.03),xticks=[0,1,2,5,10])
            axes[i,j].grid(alpha=.2);axes[i,j].legend(frameon=False,fontsize=8)
    fig.suptitle('PANDA S1 development stress · 192 exact oracle recoveries / 192 trials\nGenuine saved donor features; synthetic placement · final test unscored · no detector',fontsize=12)
    fig.savefig(output/'stress_curves.png',dpi=180);plt.close(fig)
    write_json(output/'provenance.json',dict(summary_sha256=file_sha256(summary),plot_source_sha256=file_sha256(__file__),source_kind='real',test_slides_scored=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--summary',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();plot(a.summary,a.output)
