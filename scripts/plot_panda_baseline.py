#!/usr/bin/env python3
"""Plot executed PANDA development confusion matrices; final test slides stay sealed."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from floater_finder.experiments import file_sha256
from floater_finder.artifacts import write_json


def plot(metrics,output):
    report=json.loads(Path(metrics).read_text())
    if report['source_kind']!='real' or report['test_slides_scored'] is not False:
        raise ValueError('Only executed, development-only real PANDA metrics are eligible')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    labels={'benign':'Benign','cancer':'Cancer','low_grade':'GG1','high_grade':'ISUP 4–5'}
    for split in ('train','calibration'):
        fig,axes=plt.subplots(2,3,figsize=(11,6.8),layout='constrained')
        for r,task in enumerate(('benign_cancer','low_high')):
            for c,rule in enumerate(('mean','top1pct','top5pct')):
                row=report['metrics'][f'{split}/{task}/{rule}'];matrix=np.asarray(row['confusion_rows_truth_columns_prediction'])
                assert matrix.shape==(2,2) and matrix.sum()==row['slides'] and matrix.sum()>0
                assert np.isclose(np.trace(matrix)/matrix.sum(),row['accuracy'])
                ax=axes[r,c];ax.imshow(matrix,cmap='Blues',vmin=0,vmax=matrix.max() or 1)
                for (i,j),value in np.ndenumerate(matrix):
                    ax.text(j,i,str(value),ha='center',va='center',fontsize=14,
                            color='white' if value>matrix.max()/2 else '#172a3a')
                names=[labels[name] for name in row['classes']]
                ax.set(xticks=[0,1],yticks=[0,1],xticklabels=names,yticklabels=names,
                       xlabel='Prediction',ylabel='Original slide label',
                       title=f"{rule}: accuracy {row['accuracy']:.1%}\nBalanced {row['balanced_accuracy']:.1%}; n={row['slides']}")
        fig.suptitle(f'PANDA CONCH v1 zero-shot — {split}\nSlide labels only · patient independence unknown · final test unscored',fontsize=12)
        fig.savefig(output/f'{split}_confusion.png',dpi=180);plt.close(fig)
    write_json(output/'provenance.json',dict(metrics_sha256=file_sha256(metrics),
        plot_source_sha256=file_sha256(__file__),source_kind='real',test_slides_scored=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--metrics',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();plot(a.metrics,a.output)
