"""Publication-friendly static evidence plots from exported experiment files."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    groups=json.loads((ROOT/'results'/'summary.json').read_text())['groups']
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),constrained_layout=True)
    for ax,radio in zip(axes,['NR','LTE']):
        for profile,color in [('bursty','#008e85'),('steady','#6656cc'),('overload','#ca7b27')]:
            g=[r for r in groups if r['radio']==radio and r['profile']==profile]
            x=np.array([r['load'] for r in g])*100;y=np.array([r['saving_mean_pct'] for r in g])
            ax.plot(x,y,'o-',label=profile,color=color)
            ax.fill_between(x,[r['saving_min_pct'] for r in g],[r['saving_max_pct'] for r in g],alpha=.13,color=color)
        ax.set_title(radio+' · compact vs always-on');ax.set_xlabel('Nominal offered load (%)');ax.set_ylabel('Modelled energy reduction (%)');ax.grid(alpha=.15);ax.legend(frameon=False)
    fig.suptitle('Energy savings shrink under congestion',fontsize=15,fontweight='bold')
    fig.savefig(ROOT/'results'/'benchmark.png',dpi=180);plt.close(fig)
    with (ROOT/'results'/'forecast-predictions.csv').open() as f:rows=list(csv.DictReader(f))
    fig,ax=plt.subplots(figsize=(12,4),constrained_layout=True)
    ax.plot([float(r['observed_activity']) for r in rows],label='Observed normalized profile',color='#243746',lw=1)
    ax.plot([float(r['ridge_prediction']) for r in rows],label='Ridge AR(6), one-step forecast',color='#008e85',lw=.9,alpha=.85)
    ax.set(xlabel='Held-out week 3 · ten-minute sample index',ylabel='Normalized activity (unitless)',title='Measurement-derived Milan profiles: held-out traffic forecast')
    ax.legend(frameon=False);ax.grid(alpha=.15);fig.savefig(ROOT/'results'/'forecast.png',dpi=180);plt.close(fig)
    print('Saved benchmark.png and forecast.png from exported numerical results')

if __name__=='__main__':main()
