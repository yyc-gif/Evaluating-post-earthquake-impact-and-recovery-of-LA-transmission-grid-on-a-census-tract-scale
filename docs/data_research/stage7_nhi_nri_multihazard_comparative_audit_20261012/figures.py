"""Data-only Matplotlib author-review graphics; no scientific reruns."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.lines import Line2D
import geopandas as gpd
import fitz
from PIL import Image
from common import *

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'legend.fontsize':7,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
COLORS = ['#007c91','#cc6b36','#4d8c45','#875aa1','#bd4868','#74705a','#4a678c','#6a6a6a']
manifest = []


def finish(fig,name,title,note):
    fig.suptitle(title,fontsize=12,y=.95)
    fig.text(.5,.985,WARN,ha='center',va='top',fontsize=7,color='#943b24')
    for old,new in [('2299','2,299'),('All2343','All 2,343'),('original34','original 34'),('has38','has 38'),('main5','five-policy'),('availability1.73','availability 1.73')]:
        note=note.replace(old,new)
    fig.text(.04,.02,note,ha='left',va='bottom',fontsize=7,wrap=True)
    fig.subplots_adjust(left=.17 if name.startswith('01_') else .10,right=.90,bottom=.13,top=.88,hspace=.47,wspace=.48)
    fig.savefig(dest('figures/'+name+'.pdf'))
    fig.savefig(dest('figures/'+name+'.png'),dpi=600)
    with fitz.open(str(lp(OUT/'figures'/ (name+'.pdf')))) as doc:
        doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(str(dest('tmp/pdfs/'+name+'_publication_review.png')))
    manifest.append(dict(name=name,pdf='figures/'+name+'.pdf',png='figures/'+name+'.png',width_inches=fig.get_figwidth(),height_inches=fig.get_figheight(),PNG_dpi=600,label=WARN,source='Matplotlib from verified numerical/source records; no AI-generated media'))
    plt.close(fig)


def spatial(ax,g,values,title,label,cmap='viridis',norm=None):
    x=np.asarray(values,float)
    g.assign(value=x).plot(column='value',ax=ax,cmap=cmap,norm=norm,edgecolor='none',missing_kwds={'color':'#d9d9d9'})
    ax.set_title(title,pad=16);ax.set_axis_off()
    if norm is None:
        norm=colors.Normalize(vmin=np.nanmin(x),vmax=np.nanmax(x))
    cb=plt.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,fraction=.046,pad=.015,shrink=.85)
    cb.set_label(label,fontsize=7)


def main():
    d=frame('FROZEN_COHORT_AND_COMPARATORS.csv','tract_id')
    size=frame('PER_CLUSTER_SILHOUETTE_AND_POPULATION.csv')
    geo=frame('COLUMBIA_NHI_2010_TO_2020_GEOGRAPHY_QA.csv','tract_id').reindex(d.index)
    tv=frame('COLUMBIA_NHI_TRANSFERRED_VALUES.csv','tract_id').reindex(d.index)
    cover=frame('COLUMBIA_SOURCE_COVERAGE_BY_TARGET.csv','tract_id').reindex(d.index)
    g=gpd.read_file(lp(OUT/'TARGET_2020_GEOMETRY.gpkg')).set_index('tract_id').reindex(d.index)
    v=frame('CANDIDATE_TRACT_VALUES.csv','tract_id').reindex(d.index)
    reg=json.loads(lp(OUT/'FEMA_NCV_ADAPTATION_REGISTRATION.json').read_text())
    qa=frame('COLUMBIA_NHI_14_HAZARD_COMPONENT_QA.csv')
    fig,ax=plt.subplots(2,2,figsize=(7.2,6.6))
    names=qa.name
    ax[0,0].barh(names,qa['class_valid1to5'],color='#397c90',label='Rating1-5')
    ax[0,0].barh(names,qa.class_zero,left=qa.class_valid1to5,color='#a9b8ad',label='Explicit0')
    ax[0,0].barh(names,qa.class_null,left=qa.class_valid1to5+qa.class_zero,color='#dcb59d',label='Unresolved NULL')
    ax[0,0].invert_yaxis();ax[0,0].set_xlabel('Original 2010 LA features (n=2343)');ax[0,0].legend(loc='lower right')
    spatial(ax[0,1],g,cover.hazards_with_no_source_null_area,'Non-null component support','Number of14 layers','cividis')
    spatial(ax[1,0],g,tv.Columbia_published_sum_dominant_source,'Dominant-land-donor\npublished sum','Ordinal category sum','viridis')
    spatial(ax[1,1],g,tv.eq_dominant_source_category,'Earthquake rating: saturated','Ordinal category','YlOrRd',colors.Normalize(1,5))
    finish(fig,'01_Columbia_components_and_support','Columbia NHI: published score is not complete physical support','NULL is not physical zero. Donor sums are transferred2010 screening values, not native2020 measurements.\nNo Columbia14 primary-cohort fit is admitted.')

    fig,ax=plt.subplots(2,2,figsize=(7.2,6.2))
    types=['one_to_one','one_to_many','many_to_one','many_to_many']
    vals=geo.relation_type.value_counts().reindex(types,fill_value=0)
    assert vals.sum()==2299
    ax[0,0].bar(range(4),vals,color=COLORS[:4]);ax[0,0].set_xticks(range(4),[x.replace('_to_','\nto\n') for x in types]);ax[0,0].set_ylabel('Target tract count');ax[0,0].set_title('Official land relationship')
    spatial(ax[0,1],g,geo.dominant_source_fraction,'Dominant donor share','Fraction of official target land','cividis',colors.Normalize(0,1))
    spatial(ax[1,0],g,1-geo.official_land_supported_fraction,'Uncovered donor land','Fraction of target land','OrRd',colors.Normalize(0,.05))
    spatial(ax[1,1],g,geo.geometric_covered_fraction,'Service-geometry coverage','Fraction of total polygon area','Blues',colors.Normalize(0,1))
    finish(fig,'02_Columbia_geographic_uncertainty','2010-to-2020 transfer: IDs do not guarantee matching boundaries','11 targets /46,455 residents have uncovered official donor land; all remain in the cohort.\nLand-relation shares and total geometric overlaps measure different supports, especially along coastlines.')

    raw=frame('FEMA_NCV_HAZARD_COMPONENT_VALUES.csv','tract_id').reindex(d.index)
    fig,ax=plt.subplots(2,3,figsize=(7.2,5.8))
    for row,h in enumerate(['ERQK','RFLD']):
        spatial(ax[row,0],g,raw[h+'_AFREQ'],h+':\nReleased frequency','Released native scale','viridis')
        spatial(ax[row,1],g,raw[h+'_area_fraction'],h+':\nImpacted-area fraction','Fraction of tract AREA','cividis',colors.Normalize(0,1))
        spatial(ax[row,2],g,raw[h+'_NCV_raw'],h+':\nFrequency x fraction','Native factor (not probability)','magma')
    finish(fig,'03_FEMA_frequency_and_area','FEMA factor: frequency and geographic footprint must be separated','ERQK is a modeled probability surrogate, not PGA. Positive RFLD frequency is inherited from one county.\nArea in both numerator/denominator is square miles; no clipping or source-zero imputation.')

    cf=frame('FEMA_NCV_EFFECTIVE_HAZARD_CONTRIBUTIONS.csv')
    fig,ax=plt.subplots(2,2,figsize=(7.2,6.3))
    ax[0,0].barh(cf.hazard,cf.covariance_share*100,color=['#c95e3a' if z=='ERQK' else '#387e8e' for z in cf.hazard]);ax[0,0].invert_yaxis();ax[0,0].set_xlabel('Signed share of local sum variance (%)');ax[0,0].axvline(0,color='black',lw=.5)
    ax[0,1].barh(cf.hazard,cf.mean_normalized,color='#587b42');ax[0,1].invert_yaxis();ax[0,1].set_xlabel('Mean California-normalized component')
    spatial(ax[1,0],g,v.FEMA_NCV14_CA_v119,'Selected14 screening coordinate','California-relative0-1 score','viridis')
    spatial(ax[1,1],g,raw.LNDS_AFREQ.eq(.01).astype(float),'LNDS numerical 0.01 indicator','Coincides with default; not QA flag','Greys',colors.Normalize(0,1))
    finish(fig,'04_FEMA_components_and_defaults','Hazard diversity: background level differs from local variation','Heat, hail and strong wind dominate local variation. Earthquake has high background but weak local leverage.\nFour entirely NULL hazards are excluded; minimum modeled defaults are retained and explicitly flagged.')

    fig,ax=plt.subplots(1,3,figsize=(7.2,4.5))
    spatial(ax[0],g,v.Columbia_published_sum_dominant_source,'Columbia14\nnot admitted','Transferred ordinal sum','viridis')
    spatial(ax[1],g,v.FEMA_NCV14_CA_v119,'FEMA selected14\nqualified extension','California-relative score','cividis')
    spatial(ax[2],g,d.RPL_CBM,'CDC CBM\nClimate-only\ncomparator','National climate percentile','magma',colors.Normalize(0,1))
    finish(fig,'05_Three_way_geographic_comparison','Different constructs: similar maps do not establish equivalence','FEMA extension uses native frozen2020 tract IDs; Columbia is a2010 crosswalk with source NULLs.\nCBM excludes earthquake. All2299 tracts and original frozen population are retained.')

    ev=frame('EIGHT_VARIABLE_K_EVIDENCE.csv');old=frame('FROZEN_COMPARATOR_K_EVIDENCE.csv')
    fig,ax=plt.subplots(2,2,figsize=(7.2,6))
    oldmat=np.load(lp(OUT/'FROZEN_COMPARATOR_WEIGHTED_MATRICES.npz'))
    for j,(name,x) in enumerate([('P2 (seven)',old.query("specification=='P2'")),('H2-CBM',old.query("specification=='H2'")),('H2-NCV14',ev)]):
        if j<2:
            base=oldmat['P2__published' if j==0 else 'H2__published'];k1=np.square(base-base.mean(0)).sum()
            assert abs(k1-2299)<1e-7
            x=pd.concat([pd.DataFrame([dict(k=1,mean_WCSS=k1,mean_silhouette=np.nan)]),x]).sort_values('k')
        ax[0,0].plot(x.k,x.mean_WCSS/x.mean_WCSS.iloc[0],'-o',ms=3,label=name,color=COLORS[j]);ax[0,1].plot(x.k,x.mean_silhouette,'-o',ms=3,label=name,color=COLORS[j])
    ax[0,0].set(xlabel='K',ylabel='WCSS / K1 WCSS',title='Elbow: smooth, endpoint-sensitive');ax[0,0].legend()
    ax[0,1].set(xlabel='K',ylabel='Mean full-cohort silhouette',title='Within-space geometry, not common validation')
    for name,label,c in [('seed_min_ARI','Seed min',COLORS[0]),('geographic_min_ARI','Geographic min',COLORS[1]),('policy_LOO_cohort_min_ARI','Policy LOO min',COLORS[2])]:ax[1,0].plot(ev.k,ev[name],'-o',ms=3,label=label,color=c)
    ax[1,0].set(xlabel='K',ylabel='Minimum ARI',ylim=(0,1.05),title='NCV14 robustness');ax[1,0].legend()
    small=size.query('seed==42 and k>=2').groupby('k').n_tracts.min()
    ax[1,1].bar(small.index,small,color='#82646e');ax[1,1].set(xlabel='K',ylabel='Smallest class (tracts)',title='Rare-state classes persist at K4+')
    finish(fig,'06_K_evidence_and_robustness','K evidence: silhouette favors 4; bend diagnostics favor 3 or 4','Different feature spaces give conditional geometric scores, not absolute physical validation.\nPolicy/geographic sensitivity remains material; no K is promoted to formal Stage 7.')

    fit=np.load(lp(OUT/'REGISTERED_CONDITIONAL_FIT_ARRAYS.npz'));ix={k:i for i,k in enumerate(fit['keys'])}
    fig,ax=plt.subplots(2,3,figsize=(7.2,6.3))
    for j,k in enumerate([3,4,5]):
        lab=fit['labels'][ix[f'NCV14__main__k{k}__s42']]
        cmap=colors.ListedColormap(COLORS[:k]);g.assign(class_id=lab).plot(column='class_id',cmap=cmap,ax=ax[0,j],vmin=-.5,vmax=k-.5,edgecolor='none');ax[0,j].set_axis_off();ax[0,j].set_title('NCV14 K'+str(k)+'; model-specific IDs')
        q=size.query('k==@k and seed==42').sort_values('cluster')
        ax[1,j].bar(q.cluster,q.population_share*100,color=COLORS[:k]);ax[1,j].set(xlabel='Model-specific class',ylabel='Resident population (%)');ax[1,j].set_xticks(q.cluster)
        for row in q.itertuples():ax[1,j].text(row.cluster,row.population_share*100+.8,str(row.n_tracts),ha='center',fontsize=7)
        ax[1,j].set_ylim(0,65)
    finish(fig,'07_Memberships_and_population','K3/4/5: class maps and population represented','Bar labels give tract counts; classes are ordered by mean frozen main5 total deficit within each model.\nK4 has38 tracts including the original34 Q-related tracts; eight zero-housing positive tracts remain elsewhere.')

    p=frame('K4_COMPACT_ORIGINAL_UNIT_PROFILE.csv').sort_values('cluster')
    fig,ax=plt.subplots(2,4,figsize=(7.2,5.6))
    columns=['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','Population','FEMA_NCV14_CA_v119']
    titles=['Initial modeled service (%)','Spectral grid impact','Dependency HHI','Unconstrained deficit (h)','Mean extra deficit (h)','FEMA SOVI (0-100)','Mean tract population','NCV screening (0-1)']
    for a,col,title in zip(ax.flat,columns,titles):
        y=p[col]*100 if col=='Init_Supply' else p[col]
        a.bar(p.cluster,y,color=COLORS[:4]);a.set_title(title,fontsize=8);a.set_xticks(p.cluster);a.set_xlabel('Model-specific class')
        cohort=raw[col].mean() if col in raw else d[col].mean() if col in d else v[col].mean()
        if col=='Init_Supply':cohort*=100
        a.axhline(cohort,color='black',lw=.7,ls='--')
    finish(fig,'08_K4_original_unit_profiles','NCV14 K4: joint patterns in actual units','Dashed lines: full2299-tract means. Initial availability1.73% in the rare class is not strong resilience.\nInput-coordinate contrasts are internal descriptions, not independent validation. No formal class IDs are reused.')
    dump('FIGURE_MANIFEST.json',dict(review_status=WARN,figures=manifest,publication_size_inches='7.2 wide',vector_PDF=True,AI_images_used=False))
    print('Eight review PDFs and600dpi previews created',flush=True)


if __name__=='__main__':
    main()
