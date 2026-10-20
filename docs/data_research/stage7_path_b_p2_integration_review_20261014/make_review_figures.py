"""Two vector Figure 7 Path B candidates using frozen labels and observations."""
import os
from pathlib import Path
import sys

import fitz
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0,str(Path(__file__).parent))
import analyze_path_b as a

OUT=a.HERE/'figures'
plt.rcParams.update({'font.family':'Arial','font.size':7,'axes.titlesize':8,'axes.labelsize':7,
                     'xtick.labelsize':6.5,'ytick.labelsize':6.5,'pdf.fonttype':42,'ps.fonttype':42,
                     'hatch.linewidth':.25,'axes.spines.top':False,'axes.spines.right':False})
FEATURE_LABELS=['Initial service','Spectral grid impact','Dependency HHI','Unconstrained deficit',
                'Constraint increment','SOVI score','log1p(Population)']
HATCHES=['','///','\\\\\\','xx']
MACHADO={
    'protanopia':[[.152286,1.052583,-.204868],[.114503,.786281,.099216],[-.003882,-.048116,1.051998]],
    'deuteranopia':[[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]],
    'tritanopia':[[1.255528,-.076749,-.178779],[-.078411,.930809,.147602],[.004733,.691367,.303900]]}


def srgb(linear):
    v=np.asarray(linear)
    return np.where(v<=.0031308,12.92*v,1.055*np.maximum(v,0)**(1/2.4)-.055)


def linear_rgb(rgb):
    v=np.asarray(rgb)
    return np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)


def lab_linear(L,C,hue):
    aa=C*np.cos(np.deg2rad(hue));bb=C*np.sin(np.deg2rad(hue))
    fy=(L+16)/116;f=np.array([fy+aa/500,fy,fy-bb/200])
    xyz=np.where(f>6/29,f**3,3*(6/29)**2*(f-4/29))*[.95047,1,1.08883]
    return np.array([[3.2404542,-1.5371385,-.4985314],[-.969266,1.8760108,.041556],
                     [.0556434,-.2040259,1.0572252]])@xyz


def color_lut(lo,hi):
    rows=[];table=[]
    hues=[255,155,75,325]
    for j,t in enumerate(np.linspace(0,1,257)):
        L=91-49*t;C=25
        while True:
            rgb=np.array([lab_linear(L,C,h) for h in hues])
            if np.all((rgb>=0)&(rgb<=1)):break
            C-=.25
            assert C>0
        rgb=srgb(rgb);table.append(rgb)
        for q,c in enumerate(rgb):
            rows.append(dict(position=j,quartile=f'Q{q+1}',deficit_hours=lo+t*(hi-lo),L_star=L,
                common_chroma=C,hue_degrees=hues[q],R=c[0],G=c[1],B=c[2],
                relative_luminance=float(linear_rgb(c)@[.2126729,.7151522,.0721750])))
    a.save('BIVARIATE_EXACT_COLOR_LEGEND.csv',pd.DataFrame(rows))
    return np.array(table)


def save(fig,name):
    a.u.write(OUT/(name+'.pdf'),b'')
    fig.savefig(a.u.lp(OUT/(name+'.pdf')),metadata={'CreationDate':None,'ModDate':None})
    fig.savefig(a.u.lp(OUT/(name+'.png')),dpi=600)
    plt.close(fig)


def base_map(ax,g):
    bounds=g.total_bounds
    ax.set_xlim(bounds[0]-2200,bounds[2]+2200);ax.set_ylim(bounds[1]-1800,bounds[3]+1800)
    ax.set_aspect('equal');ax.set_axis_off()


def na_and_joint(ax,g):
    na=g.Population.eq(0)
    g.loc[na].plot(ax=ax,facecolor='white',edgecolor='#333333',linewidth=.45,zorder=6)
    g.loc[g.Q4_and_high_mean_total5].boundary.plot(ax=ax,color='#111111',linewidth=.62,zorder=7)


def common_top(fig,d):
    q=d.loc[d.Population>0];colors=a.COLORS
    fig.text(.025,.986,'PATH B AUTHOR REVIEW - NOT FORMAL STAGE 7',fontsize=7,color='#555555',va='top')
    fig.text(.025,.96,'A. Feature distributions across the saved P2/K3 classes',weight='bold',fontsize=9)
    fig.legend([Line2D([],[],color=c,ls=ls,lw=1.2) for c,ls in zip(colors,['-','--',':'])],
        [f'C{i+1} (n={int(q.P2_K3_class.eq(i+1).sum()):,})' for i in range(3)],
        loc='upper left',bbox_to_anchor=(.025,.95),ncol=3,frameon=False,columnspacing=2,fontsize=7)
    choices=[('Grid_Impact','RQ1: Spectral grid impact','Unitless'),
             ('Redundancy_HHI','RQ1: Dependency concentration','HHI (unitless)'),
             ('B_Unconstrained','RQ2: Baseline restoration deficit','Equivalent deficit hours'),
             ('MeanDelta','RQ2: Added constraint deficit','Five-policy mean increment (h)'),
             ('SOVI_SCORE','RQ3: Social vulnerability','SOVI score (0-100)'),
             ('Population','RQ3: Population exposure','Persons')]
    for i,(v,title,label) in enumerate(choices):
        col=i%3;row=i//3
        ax=fig.add_axes([.075+col*.322,.785-row*.15,.225,.089])
        for c,ls in zip(range(1,4),['-','--',':']):
            vals=np.sort(q.loc[q.P2_K3_class.eq(c),v].to_numpy())
            y=np.arange(1,len(vals)+1)/len(vals)
            ax.step(vals,y,where='post',color=colors[c-1],ls=ls,lw=.9)
            ax.plot(np.median(vals),.5,'o',ms=2.6,color=colors[c-1])
        ax.axhline(.5,color='#aaaaaa',lw=.4,zorder=0)
        ax.set_ylim(0,1.02);ax.set_yticks([0,.5,1]);ax.set_xlabel(label,labelpad=1)
        ax.set_title(title,pad=3,fontsize=7.2)
        if v=='Population':ax.ticklabel_format(axis='x',style='sci',scilimits=(4,4));ax.xaxis.get_offset_text().set_fontsize(6)
        if col==0:ax.set_ylabel('Cumulative fraction',fontsize=6.5)
        ax.spines[['left','bottom']].set_color('#aaaaaa');ax.tick_params(length=2,pad=2)
    fig.text(.025,.594,'Exact empirical CDFs; markers locate class medians on the 50% guide. Population is fitted as log1p.',fontsize=6.4)
    fig.text(.025,.572,'B. Seven-coordinate cohort-standardized class profiles',weight='bold',fontsize=9)
    fig.text(.025,.552,'Ordinary feature z means, not weighted-distance contributions; zero = 2,299-tract cohort mean.',fontsize=6.6)
    z=pd.read_csv(a.u.lp(a.HERE/'P2_ORDINARY_COHORT_Z_CLASS_MEANS.csv')).set_index('class_id')[a.FEATURES].to_numpy().T
    ax=fig.add_axes([.40,.414,.35,.126]);norm=TwoSlopeNorm(vmin=-1.5,vcenter=0,vmax=1.5)
    grid=ax.pcolormesh(np.arange(4),np.arange(8),z,cmap='RdBu_r',norm=norm,edgecolors='white',linewidth=.2)
    ax.set_ylim(7,0);ax.set_yticks(np.arange(7)+.5,FEATURE_LABELS);ax.set_xticks(np.arange(3)+.5,['C1','C2','C3'])
    ax.xaxis.tick_top();ax.tick_params(length=0,pad=3)
    for t,c in zip(ax.get_xticklabels(),colors):t.set_color(c);t.set_fontweight('bold')
    for i in range(7):
        for j in range(3):ax.text(j+.5,i+.5,f'{z[i,j]:+.2f}',ha='center',va='center',fontsize=6.4,
                                  color='white' if abs(z[i,j])>1 else '#222222')
    for y in [3,5]:ax.axhline(y,color='#333333',lw=.7)
    for y,rq in [(1.5,'RQ1'),(4,'RQ2'),(6,'RQ3')]:
        ax.text(-2.5,y,rq,ha='right',va='center',weight='bold',fontsize=7,clip_on=False)
    cb=fig.colorbar(grid,cax=fig.add_axes([.81,.414,.017,.126]));cb.set_label('Class mean z-score',fontsize=6.5)
    cb.solids.set_rasterized(False)
    return q


def make_candidate(kind,d,g,lut):
    fig=plt.figure(figsize=(7.2,10.4));q=common_top(fig,d)
    fig.text(.045,.386,'C. Saved seven-variable P2/K3 typology',weight='bold',fontsize=8.7)
    fig.text(.535,.386,'D. Recovery burden and frozen vulnerability',weight='bold',fontsize=8.7)
    cax=fig.add_axes([.035,.136,.445,.239]);dax=fig.add_axes([.525,.136,.445,.239])
    base_map(cax,g);base_map(dax,g)
    for c,color in enumerate(a.COLORS,1):
        g.loc[g.P2_K3_class.eq(c).fillna(False)].plot(ax=cax,facecolor=color,edgecolor='white',linewidth=.12)
    g.loc[g.Population.eq(0)].plot(ax=cax,facecolor='white',edgecolor='#333333',linewidth=.45)
    positive=g.Population>0;values=g.loc[positive,'MeanTotal5'].to_numpy();lo=values.min();hi=values.max()
    norm=Normalize(lo,hi)
    if kind=='A':
        g.loc[positive].plot(ax=dax,column='MeanTotal5',cmap='cividis_r',norm=norm,edgecolor='#dddddd',linewidth=.10)
        for qid,hatch in zip(['Q1','Q2','Q3','Q4'],HATCHES):
            if hatch:g.loc[positive & g.frozen_SOVI_quartile.eq(qid)].plot(ax=dax,facecolor='none',
                edgecolor='#444444',linewidth=.13,hatch=hatch)
        cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap='cividis_r'),
            cax=fig.add_axes([.56,.122,.37,.011]),orientation='horizontal')
        cb.set_label('Five-policy mean total deficit (equivalent h)',fontsize=6.5,labelpad=2)
        cb.solids.set_rasterized(False)
        handles=[Patch(facecolor='white',edgecolor='#444444',hatch=h,label=f'Q{i+1}') for i,h in enumerate(HATCHES)]
        fig.legend(handles=handles,loc='upper left',bbox_to_anchor=(.525,.084),ncol=4,frameon=False,
                   handlelength=1.6,columnspacing=1,fontsize=6.5)
    else:
        t=np.clip(np.rint(norm(values)*256).astype(int),0,256)
        qi=g.loc[positive,'frozen_SOVI_quartile'].str[1].astype(int).to_numpy()-1
        rgba=lut[t,qi]
        g.loc[positive].plot(ax=dax,color=rgba,edgecolor='white',linewidth=.10)
        ax=fig.add_axes([.61,.069,.32,.057])
        # Vector cells, same L* and luminance for the same burden in every row.
        for qid in range(4):
            ax.pcolormesh(np.linspace(lo,hi,258),[qid,qid+1],np.zeros((1,257)),
                          color=lut[:,qid].reshape(-1,3),edgecolors='none',cmap=None)
            ax.collections[-1].set_array(None);ax.collections[-1].set_facecolors(lut[:,qid])
        ax.set_ylim(4,0);ax.set_yticks(np.arange(4)+.5,['Q1','Q2','Q3','Q4']);ax.tick_params(length=2,pad=1,labelsize=6)
        ax.set_xticks([25,35,45,50]);ax.set_xlim(lo,hi)
        ax.set_xlabel('Five-policy mean total deficit (equivalent h)',fontsize=6.2,labelpad=1)
        ax.set_ylabel('Frozen SOVI',fontsize=6.5,labelpad=2)
    na_and_joint(dax,g)
    fig.legend(handles=[Patch(facecolor=c,label=f'C{i+1}') for i,c in enumerate(a.COLORS)]+
               [Patch(facecolor='white',edgecolor='#333333',label='N/A (16)')],
               loc='upper left',bbox_to_anchor=(.035,.12),ncol=4,frameon=False,fontsize=6.5,
               columnspacing=1,handlelength=1.2)
    fig.text(.045,.071,'2,299 tracts; 9,066,522 frozen residents.\nP2 model IDs; no NCV14 clustering coordinate.',fontsize=6.4,va='top')
    fig.legend(handles=[Patch(facecolor='none',edgecolor='#111111',linewidth=.8,label='Q4 and deficit >= frozen P75'),
                        Patch(facecolor='white',edgecolor='#333333',label='N/A (16)')],
               loc='lower left',bbox_to_anchor=(.525,.014),frameon=False,ncol=1,fontsize=6.2)
    fig.text(.045,.022,'Finite five-policy comparison.\nDescriptive co-occurrence; no new score.',fontsize=6.1)
    save(fig,f'FIGURE7_PATH_B_CANDIDATE_{kind}')


def previews(name):
    with fitz.open(a.u.lp(OUT/(name+'.pdf'))) as doc:
        pix=doc[0].get_pixmap(dpi=150,alpha=False)
        im=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)/255
        lin=linear_rgb(im);Y=lin@np.array([.2126729,.7151522,.0721750])
        gray=srgb(Y)
        Image.fromarray(np.rint(np.repeat(gray[:,:,None],3,axis=2)*255).astype('uint8')).save(a.u.lp(OUT/(name+'_GRAYSCALE.png')))
        for label,matrix in MACHADO.items():
            rgb=np.clip(srgb(lin@np.asarray(matrix).T),0,1)
            Image.fromarray(np.rint(rgb*255).astype('uint8')).save(a.u.lp(OUT/(name+'_'+label.upper()+'.png')))
        a.u.write(OUT/(name+'_NATIVE.png'),pix.tobytes('png'))


def evidence(d,g):
    fits=pd.read_csv(a.u.lp(a.HERE/'P2_REGISTERED_K_EVIDENCE.csv'))
    f=fig=plt.figure(figsize=(7.2,4.2));axs=fig.subplots(1,2)
    for seed in range(42,47):
        q=fits.query('seed == @seed').sort_values('k')
        axs[0].plot(q.k,q.WCSS,color='#7b7b7b',alpha=.5,lw=.8)
        axs[1].plot(q.k,q.mean_silhouette,color='#7b7b7b',alpha=.5,lw=.8)
    for ax in axs:ax.axvline(3,color=a.COLORS[0],ls='--',lw=1);ax.set_xlabel('K');ax.set_xticks(range(1,9))
    axs[0].set_ylabel('Weighted within-class sum of squares');axs[1].set_ylabel('Full-cohort mean silhouette')
    axs[0].set_title('A. Frozen P2 inertia');axs[1].set_title('B. Frozen P2 silhouette')
    fig.subplots_adjust(left=.10,right=.97,bottom=.22,top=.82,wspace=.35)
    fig.text(.02,.96,'PATH B AUTHOR REVIEW - NOT FORMAL STAGE 7',fontsize=8)
    fig.text(.10,.06,'K3 is the parsimonious main-text candidate; K4 remains sensitivity. K5 has the highest mean silhouette.\nSaved seeds 42-46 only; no new fitting. Smooth elbow is not proof of a unique optimum.',fontsize=7)
    save(fig,'P2_K_SELECTION_SAVED_EVIDENCE')
    fig=plt.figure(figsize=(7.2,4.1));ax=fig.add_axes([.025,.12,.49,.72]);base_map(ax,g)
    q=g.Population>0
    g.loc[q].plot(ax=ax,column='FEMA_NCV14_CA_v119',cmap='viridis',vmin=0,vmax=1,linewidth=.12,edgecolor='white')
    g.loc[~q].plot(ax=ax,facecolor='white',edgecolor='#333333',linewidth=.45)
    ax.set_title('A. Supplementary NCV14 geography',fontsize=9)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,1),cmap='viridis'),
                   cax=fig.add_axes([.07,.10,.40,.020]),orientation='horizontal')
    cb.set_label('NCV14 screening index (California reference, 0-1)',fontsize=6.4,labelpad=2)
    cb.solids.set_rasterized(False)
    bx=fig.add_axes([.64,.24,.30,.52])
    for c in range(1,4):
        v=np.sort(d.loc[d.P2_K3_class.eq(c).fillna(False),'FEMA_NCV14_CA_v119'])
        bx.step(v,np.arange(1,len(v)+1)/len(v),where='post',color=a.COLORS[c-1],label=f'C{c}')
    bx.set_xlabel('Researcher-derived NCV14 (0-1)');bx.set_ylabel('Cumulative tract fraction');bx.legend(frameon=False)
    bx.set_title('B. Context within P2 classes',fontsize=9)
    fig.text(.02,.97,'PATH B AUTHOR REVIEW - SUPPLEMENTARY CONTEXT ONLY',fontsize=8)
    fig.text(.56,.09,'Not a fitted coordinate, official FEMA risk score,\noutage prediction or independent validation.',fontsize=7)
    fig.text(.56,.035,'White outlined tracts: N/A (16).',fontsize=6.5)
    save(fig,'NCV14_OPTIONAL_CONTEXT_NOT_CLUSTER_VALIDATION')


def main():
    Path(a.u.lp(OUT)).mkdir(parents=True,exist_ok=True)
    d=a.load_frozen()
    geo=gpd.read_file(a.u.lp(a.HERE/'inputs/FULL_2315_GEOMETRY.gpkg')).set_index('tract_id')
    assert geo.index.is_unique and set(geo.index)==set(d.index) and geo.geometry.notna().all()
    g=geo.join(d);q=d.Population>0
    lut=color_lut(d.loc[q,'MeanTotal5'].min(),d.loc[q,'MeanTotal5'].max())
    lo=d.loc[q,'MeanTotal5'].min();hi=d.loc[q,'MeanTotal5'].max()
    a.save('CONTINUOUS_HATCH_EXACT_COLOR_LEGEND.csv',pd.DataFrame([
        dict(quartile=f'Q{k+1}',hatch=HATCHES[k],deficit_hours=float(v),
             R=float(plt.cm.cividis_r((v-lo)/(hi-lo))[0]),G=float(plt.cm.cividis_r((v-lo)/(hi-lo))[1]),
             B=float(plt.cm.cividis_r((v-lo)/(hi-lo))[2]))
        for k in range(4) for v in np.linspace(lo,hi,257)]))
    for kind in ['A','B']:
        make_candidate(kind,d,g,lut);previews(f'FIGURE7_PATH_B_CANDIDATE_{kind}')
    evidence(d,g)
    qa=[]
    for name in ['FIGURE7_PATH_B_CANDIDATE_A','FIGURE7_PATH_B_CANDIDATE_B']:
        with fitz.open(a.u.lp(OUT/(name+'.pdf'))) as doc:
            qa.append(dict(file=name+'.pdf',width_inches=doc[0].rect.width/72,height_inches=doc[0].rect.height/72,
                raster_images=len(doc[0].get_images()),vector_paths=len(doc[0].get_drawings()),
                png_dimensions=Image.open(a.u.lp(OUT/(name+'.png'))).size,PNG_dpi=600,
                crs=str(g.crs),geometry_records=len(g),eligible_polygons=int(q.sum())))
    a.dump('FIGURE_RENDER_TECHNICAL_QA.json',qa)
    a.dump('CVD_PREVIEW_METHOD.json',dict(method='Machado et al. 2009 severity100 matrices on linear sRGB',
        source='https://raw.githubusercontent.com/njsmith/colorspacious/master/colorspacious/cvd.py',
        doi='10.1109/TVCG.2009.113',matrices=MACHADO,
        limitation='Simulated screens are visual stress tests, not clinical accessibility validation; clipping after simulation is recorded.'))
    panels=[]
    for kind in ['A','B']:
        for suffix in ['NATIVE','GRAYSCALE','PROTANOPIA','DEUTERANOPIA','TRITANOPIA']:
            im=Image.open(a.u.lp(OUT/f'FIGURE7_PATH_B_CANDIDATE_{kind}_{suffix}.png')).convert('RGB')
            crop=im.crop((int(im.width*.50),int(im.height*.59),im.width,im.height))
            crop.thumbnail((430,660));panels.append((kind,suffix,crop))
    from PIL import ImageDraw
    sheet=Image.new('RGB',(5*430,2*685),'white');draw=ImageDraw.Draw(sheet)
    for i,(kind,label,im) in enumerate(panels):
        xx=(i%5)*430;yy=(i//5)*685
        sheet.paste(im,(xx,yy+25));draw.text((xx+10,yy+8),f'{kind}: {label}',fill='black')
    sheet.save(a.u.lp(OUT/'D_MAP_ACCESSIBILITY_COMPARISON.png'))
    print(qa)


if __name__=='__main__':main()
