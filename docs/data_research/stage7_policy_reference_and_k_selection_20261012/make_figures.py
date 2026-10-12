"""Native Matplotlib diagnostics; no model or manuscript outputs."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import fitz

from common import *

FIG=OUT/'figures'
PREVIEW=OUT/'pdf_review'
NOTICE='AUTHOR REVIEW \u2014 NOT FORMAL STAGE 7'
COLORS=['#176fa4','#b45616','#397950','#9564a8','#ad3345','#585858']
NAMES=['Impact','Hospital','Degree','Betweenness','Vulnerability','Random']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,
    'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,
    'axes.spines.top':False,'axes.spines.right':False})


def head(fig,title,note):
    fig.suptitle(title,fontsize=11,y=.975)
    fig.text(.5,.935,NOTICE,ha='center',color='#a52c2c',fontsize=8)
    fig.text(.5,.018,note,ha='center',fontsize=7,va='bottom')


def finish(fig,stem,pdf=None,page=None):
    if pdf is None: fig.savefig(lp(FIG/(stem+'.pdf')))
    else: pdf.savefig(fig)
    fig.savefig(lp(FIG/(stem+(f'_k{page}' if page else '')+'.png')),dpi=600)
    plt.close(fig)


def curves(elbow,sil):
    for kind in ['elbow','silhouette']:
        fig,axs=plt.subplots(2,2,figsize=(7.2,6.8))
        head(fig,'Weighted-space inertia' if kind=='elbow' else 'Full-cohort silhouette by K',
            'Five registered seeds; colors identify policy. No single statistic selects a scientific typology.\n'
            'Fixed scaling uses the Impact-first full-cohort scaler; minus-Init reallocates RQ1 weights.')
        fig.subplots_adjust(top=.81,bottom=.13,left=.09,right=.97,hspace=.43,wspace=.3)
        for row,spec in enumerate(['A','A-minus-Init']):
            for col,scale in enumerate(['policy_cohort','fixed_impact']):
                ax=axs[row,col]
                for policy,color,label in zip(POLICIES,COLORS,NAMES):
                    if kind=='elbow':
                        d=elbow.loc[elbow.policy.eq(policy)&elbow.specification.eq(spec)&elbow.scaling.eq(scale)]
                        ax.plot(d.k,d.mean_WCSS,color=color,marker='o',ms=3,lw=1.1,label=label)
                        knee=d.endpoint_chord_elbow_candidate.iloc[0]
                        r=d.loc[d.k.eq(knee)].iloc[0]
                        ax.scatter([knee],[r.mean_WCSS],s=35,facecolors='none',edgecolors=color,lw=1)
                    else:
                        d=sil.loc[sil.policy.eq(policy)&sil.specification.eq(spec)&sil.scaling.eq(scale)&sil.k.gt(1)]
                        g=d.groupby('k').mean_silhouette.agg(['mean','min','max'])
                        ax.plot(g.index,g['mean'],color=color,marker='o',ms=3,lw=1.1,label=label)
                        ax.fill_between(g.index,g['min'],g['max'],color=color,alpha=.12)
                ax.set_title(f'{spec}; '+('policy-specific scaling' if col==0 else 'fixed Impact scaling'))
                ax.set_xlabel('Number of clusters, K')
                ax.set_ylabel('WCSS' if kind=='elbow' else 'Mean silhouette')
                ax.set_xticks(range(1 if kind=='elbow' else 2,9));ax.grid(alpha=.2)
        fig.legend(handles=axs[0,0].get_legend_handles_labels()[0],labels=NAMES,loc='upper center',bbox_to_anchor=(.5,.89),ncol=3,frameon=False)
        finish(fig,'ELBOW_CURVES' if kind=='elbow' else 'SILHOUETTE_VERSUS_K')


def sizes(cluster):
    fig,axs=plt.subplots(2,3,figsize=(7.2,6.0))
    head(fig,'Class representation and rare initial-state groups',
        'A, policy-specific scaling, seed 42. Each dot is a model-specific class; size indicates resident share.\n'
        'Orange: >=80% precision and capture of the original 34-tract Q-proxy group; not electrical resilience.')
    fig.subplots_adjust(top=.825,bottom=.15,left=.09,right=.97,wspace=.4,hspace=.42)
    for ax,policy,name in zip(axs.ravel(),POLICIES,NAMES):
        d=cluster.loc[cluster.policy.eq(policy)&cluster.specification.eq('A')&cluster.scaling.eq('policy_cohort')&cluster.seed.eq(42)&cluster.k.gt(1)]
        for k,part in d.groupby('k'):
            offsets=np.linspace(-.13,.13,len(part))
            rare=part.rare_34_capture.ge(.8)&part.rare_34_precision.ge(.8)
            ax.scatter(k+offsets,part.n_tracts,s=12+180*part.population_share,c=np.where(rare,'#b45616','#176fa4'),alpha=.85,edgecolors='white',lw=.3)
        ax.axhline(34,color='#b45616',lw=.8,ls=':')
        ax.set_title(name+'-first' if name!='Random' else name)
        ax.set_yscale('log');ax.set_ylim(10,2600);ax.set_yticks([34,100,500,2000],['34','100','500','2000'])
        ax.set_xticks(KS);ax.set_xlabel('K');ax.set_ylabel('Tracts per class');ax.grid(alpha=.2)
    finish(fig,'CLUSTER_SIZE_AND_RARE_GROUPS')


def maps(changes):
    fig,axs=plt.subplots(2,3,figsize=(7.2,6.6))
    head(fig,'Policy-specific tract service-deficit differences',
        'Frozen 2pc50 / C57_D1 / M1_UTILITY_003 / G1_BASELINE_050; same 1,000 samples.\n'
        'Positive values mean more deficit than Impact-first. Official tract internal points, not polygon extents.')
    fig.subplots_adjust(top=.82,bottom=.21,left=.09,right=.96,wspace=.43,hspace=.42)
    for ax,policy,name in zip(axs.ravel()[:5],POLICIES[1:],NAMES[1:]):
        d=changes.loc[changes.alternative_policy.eq(policy)&changes.variable.eq('B_480_hr')]
        im=ax.scatter(d.INTPTLON,d.INTPTLAT,c=d.alternative_minus_impact_hr,s=2,cmap='RdBu_r',vmin=-25,vmax=25,rasterized=False)
        ax.set_title(name+' minus Impact')
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.set_aspect(1/np.cos(np.deg2rad(34)))
        ax.xaxis.set_major_locator(MaxNLocator(3));ax.yaxis.set_major_locator(MaxNLocator(3))
    ax=axs.ravel()[5];ax.axis('off')
    text=['P90 absolute tract difference']
    for policy,name in zip(POLICIES[1:],NAMES[1:]):
        d=changes.loc[changes.alternative_policy.eq(policy)&changes.variable.eq('B_480_hr')]
        text.append(f'{name}: {d.alternative_minus_impact_hr.abs().quantile(.9):.2f} h')
    ax.text(0,.85,'\n\n'.join(text),fontsize=8,va='top',transform=ax.transAxes)
    cax=fig.add_axes([.22,.12,.56,.018]);cb=fig.colorbar(im,cax=cax,orientation='horizontal')
    cb.set_label('Alternative minus Impact-first cumulative deficit (h)')
    finish(fig,'TRACT_POLICY_DEFICIT_DIFFERENCES')


def agreement(compare):
    fig,axs=plt.subplots(2,3,figsize=(7.2,6.4))
    head(fig,'Membership agreement across restoration references',
        'A; median ARI across matched registered seeds. ARI is label-invariant; no formal Stage 7 IDs are used.\n'
        'All policies use the same cohort, RQ1/RQ3 values and squared-distance budgets.')
    fig.subplots_adjust(top=.83,bottom=.21,left=.13,right=.96,wspace=.26,hspace=.43)
    for row,scale in enumerate(['policy_cohort','fixed_impact']):
        for col,k in enumerate([3,4,5]):
            ax=axs[row,col];m=np.eye(6)
            d=compare.loc[compare.comparison.eq('policy')&compare.specification.eq('A')&compare.scaling.eq(scale)&compare.k.eq(k)]
            for (a,b),part in d.groupby(['policy_a','policy_b']):
                i,j=POLICIES.index(a),POLICIES.index(b);m[i,j]=m[j,i]=part.ARI.median()
            im=ax.imshow(m,vmin=0,vmax=1,cmap='YlGnBu')
            ax.set_xticks(range(6),[n[:3] for n in NAMES],rotation=45,ha='right')
            ax.set_yticks(range(6),NAMES if col==0 else [])
            ax.set_title(f'K={k}; '+('policy scaler' if row==0 else 'fixed scaler'))
            for i in range(6):
                for j in range(6):ax.text(j,i,f'{m[i,j]:.2f}',ha='center',va='center',fontsize=6.2,color='white' if m[i,j]>.55 else 'black')
    cax=fig.add_axes([.27,.12,.52,.018]);fig.colorbar(im,cax=cax,orientation='horizontal',label='Adjusted Rand index (ARI)')
    finish(fig,'POLICY_MEMBERSHIP_AGREEMENT')


def profiles(profile,cluster):
    variables=FEATURES+['Population']
    titles=['Initial modeled service (%)','Spectral Grid_Impact','Dependency HHI','Cumulative deficit (h)',
        'Extra logistics deficit (h)','SOVI (0-100)','ln(1 + population)','Population (persons)']
    stem='K3_K4_K5_ORIGINAL_UNIT_PROFILES'
    with PdfPages(lp(FIG/(stem+'.pdf'))) as pdf:
        for k in [3,4,5]:
            fig,axs=plt.subplots(3,3,figsize=(7.2,7.8))
            head(fig,f'Impact-first original-unit profiles, K={k}',
                'Seven-variable A, policy-specific scaling, seed 42; class IDs are model-specific.\n'
                'Dots: mean; diamonds: median; lines: P10-P90, not confidence intervals; dashed: cohort median.')
            fig.subplots_adjust(top=.84,bottom=.11,left=.10,right=.97,wspace=.50,hspace=.48)
            p=profile.loc[profile.policy.eq('impact-first')&profile.specification.eq('A')&profile.scaling.eq('policy_cohort')&profile.k.eq(k)]
            for ax,v,title in zip(axs.ravel()[:8],variables,titles):
                part=p.loc[p.variable.eq(v)].sort_values('diagnostic_cluster')
                scale=100 if v=='Init_Supply' else 1
                x=part.diagnostic_cluster+1
                for row in part.itertuples():
                    color=COLORS[row.diagnostic_cluster]
                    ax.plot([row.diagnostic_cluster+1]*2,[row.p10*scale,row.p90*scale],color=color,lw=2)
                    ax.scatter(row.diagnostic_cluster+1,row.mean*scale,color=color,s=20)
                    ax.scatter(row.diagnostic_cluster+1,row.median*scale,color=color,s=16,marker='D',edgecolor='white',lw=.5)
                ax.axhline(part.cohort_median.iloc[0]*scale,ls='--',lw=.7,color='#777')
                ax.set_title(title);ax.set_xticks(x,[f'D{j}' for j in x]);ax.grid(axis='y',alpha=.2)
                if v=='Population':ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
            ax=axs.ravel()[8];ax.axis('off')
            c=cluster.loc[cluster.policy.eq('impact-first')&cluster.specification.eq('A')&cluster.scaling.eq('policy_cohort')&cluster.k.eq(k)&cluster.seed.eq(42)]
            lines=['Class   n    Pop. share']
            for r in c.itertuples(): lines.append(f'D{r.diagnostic_cluster+1:<3} {r.n_tracts:>5}   {100*r.population_share:>5.1f}%')
            ax.text(0,.88,'\n\n'.join(lines),transform=ax.transAxes,fontsize=8,va='top',fontfamily='DejaVu Sans Mono')
            finish(fig,stem,pdf,k)


def main():
    lp(FIG).mkdir(exist_ok=True);lp(PREVIEW).mkdir(exist_ok=True)
    curves(frame('ELBOW_INERTIA_BY_K.csv'),frame('SILHOUETTE_BY_K_AND_SEED.csv'))
    sizes(frame('PER_CLUSTER_SILHOUETTE_AND_SIZE.csv'))
    maps(frame('IMPACT_FIRST_TRACT_POLICY_DIFFERENCES.csv'))
    agreement(frame('POLICY_CONDITIONAL_MEMBERSHIP_COMPARISONS.csv'))
    profiles(frame('CLUSTER_ORIGINAL_UNIT_PROFILES.csv'),frame('PER_CLUSTER_SILHOUETTE_AND_SIZE.csv'))
    review=[]
    for path in sorted(FIG.glob('*.pdf')):
        with fitz.open(lp(path)) as pdf:
            for i,page in enumerate(pdf):
                assert 'AUTHOR REVIEW' in page.get_text()
                bad=[]
                for block in page.get_text('dict')['blocks']:
                    for line in block.get('lines',[]):
                        for span in line['spans']:
                            box=fitz.Rect(span['bbox'])
                            if box.x0<-.2 or box.y0<-.2 or box.x1>page.rect.width+.2 or box.y1>page.rect.height+.2:bad.append(span['text'])
                assert not bad,(path.name,i,bad)
                image_path=PREVIEW/(path.stem+f'_p{i+1}.png')
                page.get_pixmap(matrix=fitz.Matrix(150/72,150/72),alpha=False).save(lp(image_path))
                review.append(dict(pdf=path.name,page=i+1,width_inches=page.rect.width/72,height_inches=page.rect.height/72,
                    pdf_sha256=sha(path),preview_relative_path=image_path.relative_to(OUT).as_posix(),text_bounds_pass=True))
    dump('PDF_RENDER_AND_BOUNDS_QA.json',review)
    print('Six vector PDFs / eight pages rendered at publication size.',flush=True)


if __name__=='__main__': main()
