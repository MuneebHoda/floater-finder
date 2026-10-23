#!/usr/bin/env python3
"""Plot executed CPU sampling counts and mask context; no model-performance claim."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image


def plot(profile,output):
    profile=Path(profile);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    report=json.loads(profile.read_text());rows=report['slides']
    fig,ax=plt.subplots(figsize=(7,3.8),layout='constrained')
    names=['Benign (ISUP 0)','GG1 (ISUP 1)','High grade (ISUP 4)']
    for index,row in enumerate(rows):
        total=row['representative']['tiles'];positive=row['representative']['gp45_positive_tiles']
        ax.bar(index,total,color='#88aaba');ax.bar(index,positive,color='#b73b37',label='GP4/5-positive' if index==0 else None)
        ax.text(index,total+8,str(total),ha='center')
        if positive:ax.text(index,positive+8,f'{positive} GP4+',ha='center',color='#9e2926')
    ax.set(xticks=range(3),xticklabels=names,ylabel='Extracted tiles',ylim=(0,550),
           title='PANDA CPU profile: all eligible RGB tissue cells (target ≤512)')
    ax.legend(frameon=False)
    fig.savefig(output/'tile_counts.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(10,5),layout='constrained')
    for ax,row,name in zip(axes,rows,names):
        path=profile.parent/(row['image_id']+'-overlay.png')
        width,height=row['reader']['pyramid_dimensions'][0]
        with Image.open(path) as image:
            image=image.resize((max(1,round(700*width/max(width,height))),max(1,round(700*height/max(width,height)))))
            ax.imshow(image)
        ax.set_title(name);ax.axis('off')
    fig.suptitle('Mask context: GP3 yellow · GP4 red · GP5 blue\nAreas measured on native masks, not these thumbnails',fontsize=11)
    fig.savefig(output/'mask_context.png',dpi=170);plt.close(fig)


def plot_gpu(profile,output):
    report=json.loads(Path(profile).read_text());rows=report['slides']
    fig,axes=plt.subplots(1,2,figsize=(9,3.5),layout='constrained')
    labels=[r['image_id'][:8] for r in rows]
    rates=[r['tiles_per_second'] for r in rows]
    axes[0].bar(labels,rates,color='#447c95')
    for i,value in enumerate(rates):axes[0].text(i,value+1,f'{value:.1f}',ha='center')
    axes[0].set(ylabel='Tiles/second',ylim=(0,80),title='Image I/O, preprocessing and inference')
    bottom=[0.]*len(rows)
    for key,label,color in [('model_load_seconds','Model load','#b7cad2'),
                            ('image_encoding_seconds','Image encoding','#447c95')]:
        values=[r[key] for r in rows]
        axes[1].bar(labels,values,bottom=bottom,label=label,color=color)
        bottom=[a+b for a,b in zip(bottom,values)]
    axes[1].set(ylabel='Seconds',title='Recorded phases (other overhead excluded)')
    axes[1].legend(frameon=False)
    fig.suptitle('Executed three-biopsy CONCH v1 profile; no cancer-performance evaluation')
    fig.savefig(Path(output)/'gpu_profile.png',dpi=170);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',required=True);p.add_argument('--output',required=True)
    p.add_argument('--gpu-profile')
    a=p.parse_args();plot(a.profile,a.output)
    if a.gpu_profile:plot_gpu(a.gpu_profile,a.output)
