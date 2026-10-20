"""Directed travel and source-redundancy display consistency."""
import json
import fitz,numpy as np,pandas as pd
import matplotlib.pyplot as plt
from la_grid.plotting import selected_strategy_artwork as a
from la_grid.plotting.selected_strategy_panels import grouped_key
from la_grid.plotting import apply_coauthor_figure_feedback as c

def s03():
    key='Supplement/FigS03';old,before=c.baseline(key);h=old[0].rect.height/a.MM-110
    q=pd.read_csv(a.ROOT/'data/travel/travel_task_to_task.csv',index_col=0);assert q.shape==(92,92)
    fig=plt.figure(figsize=(185/25.4,h/25.4));ax=fig.add_axes([.15,.16,.67,.75]);im=ax.pcolormesh(np.arange(93),np.arange(93),q.to_numpy(),cmap='YlGnBu',vmin=0,vmax=q.to_numpy().max(),shading='flat',rasterized=False);ax.set_ylim(92,0)
    tick=[0,23,46,69,91];ax.set_xticks(np.array(tick)+.5,q.columns[tick]);ax.set_yticks(np.array(tick)+.5,q.index[tick]);ax.set_xlabel('Destination substation ID');ax.set_ylabel('Origin substation ID');ax.set_title('B. Directed task-to-task travel',pad=7)
    cb=fig.colorbar(im,cax=fig.add_axes([.855,.16,.025,.75]));cb.set_label('Travel time (h)',fontsize=8.5);cb.ax.tick_params(labelsize=7.5)
    f=a.TEMP/'S03_complete_directed.pdf';fig.savefig(f);plt.close(fig)
    with fitz.open(f) as d:out=a.overlay(old,fitz.Rect(0,110*a.MM,185*a.MM,(110+h)*a.MM),d)
    return c.finish(out,key,{'before_sha256':before,'change':'Both directed travel directions shown; no symmetry assumption. Origins map unchanged.','max_direction_difference_hr':float(abs(q.to_numpy()-q.to_numpy().T).max())})

def s07():
    key='Supplement/FigS07';old,before=c.baseline(key)
    d=pd.read_csv(a.ROOT/'results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv')
    fig=plt.figure(figsize=(185/25.4,74/25.4));ax=fig.add_axes([.115,.17,.845,.43])
    for k in a.ORDER:
        q=d[d.strategy.eq(k)].sort_values('time_hr');assert len(q)==9
        ax.plot(q.time_hr,q.population_dependency_weighted_full_minus_fixed_precomputed_best_path,color=c.COLORS[k],lw=1.15,ls='-',alpha=1)
    ax.set_xlim(0,120);ax.set_ylim(-.005,.235);ax.set_xticks([0,24,48,72,96,120]);ax.set_xlabel('Time after earthquake (h)');ax.set_ylabel('Increase in source-\nconnection probability');ax.set_title('B. Additional source connection from alternate routes',pad=5);ax.spines[['top','right']].set_visible(False);ax.grid(color='#e6e6e6',lw=.4)
    grouped_key(fig,74,top=1)
    f=a.TEMP/'S07_selected_routes.pdf';fig.savefig(f);plt.close(fig)
    with fitz.open(f) as d:out=a.overlay(old,fitz.Rect(0,61*a.MM,185*a.MM,135*a.MM),d)
    return c.finish(out,key,{'before_sha256':before,'change':'Six selected scheduled policies plus Unconstrained; solid dynamic alternative-route curves and grouped identity. A/C/D unchanged.'})

def main():
    rows=[s03(),s07()];p=a.TEMP/'artwork_records.json';allrows=json.loads(p.read_text());p.write_text(json.dumps(allrows+rows,indent=2));print([r['file'] for r in rows])
if __name__=='__main__':main()
