"""Original-source vector diagnostic figures; no AI assets or cluster models."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import geopandas as gpd
import fitz
from common import *
from audit_cdc import CODES, INDICATORS, safe_assoc

F=OUT/'figures'
LABEL='AUTHOR REVIEW \u2014 NOT FORMAL STAGE 7'
COLORS={'Heat':'#bf513a','Wildfire':'#c79528','Extreme Events':'#287e92'}
SHORT={'NEHD':'Heat days','SMOKE':'Smoke days','BURN':'Burned area','CFLD':'Coastal flood','DRGT':'Drought',
       'RFLD':'Riverine flood','HRCN':'Hurricane','SWND':'Strong wind','TRND':'Tornado'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,
    'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42})


def csv(name):
    return pd.read_csv(lp(OUT/name),dtype={'tract_id':str}).set_index('tract_id')


def finish(fig,name):
    lp(F).mkdir(exist_ok=True)
    fig.text(.5,.99,LABEL,ha='center',va='top',fontsize=8,color='#862c2c')
    fig.savefig(lp(F/(name+'.pdf')))
    fig.savefig(lp(F/(name+'.png')),dpi=600)
    plt.close(fig)
    doc=fitz.open(lp(F/(name+'.pdf')))
    assert len(doc)==1 and not doc[0].get_images()
    doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(str(lp(F/(name+'_publication_review.png'))))


def main():
    full=csv('FROZEN_P2_AND_COHORT.csv')
    d=full.loc[full.Population.gt(0)]
    n=csv('CDC_2024_MATCHED_ORIGINAL_VALUES.csv').reindex(d.index)
    s=sources()
    path=s.source(MH+'sources/TRACT_FULL_3310.gpkg',AUTH)
    g=gpd.read_file(lp(path)).set_index('tract_id').reindex(d.index).to_crs(4326)
    assert len(g)==2299 and g.geometry.notna().all()
    geo=g[['geometry']].join(n)
    fig,axes=plt.subplots(2,2,figsize=(7.2,7.4))
    fig.subplots_adjust(left=.025,right=.905,bottom=.075,top=.935,wspace=.22,hspace=.16)
    for i,(ax,col,title) in enumerate(zip(axes.flat,['RPL_CBM','RPL_CBM_DOM1','RPL_CBM_DOM2','RPL_CBM_DOM3'],
                    ['Standalone climate module','Heat domain','Wildfire domain','Extreme-events domain'])):
        geo.plot(column=col,ax=ax,cmap='YlGnBu',vmin=0,vmax=1,linewidth=0)
        ax.set_axis_off()
        ax.set_title(f'({chr(65+i)}) {title}',pad=4)
        bar=fig.colorbar(plt.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0,1),cmap='YlGnBu'),ax=ax,fraction=.035,pad=.02)
        bar.solids.set_rasterized(False)
        bar.set_label('National percentile (0-1)')
    fig.text(.04,.029,'2,299 frozen-positive-population tracts. Published ranks, not physical intensity or delivered-electricity risk.\nDomains have different indicator counts; these are not equally weighted domain inputs.',fontsize=7)
    finish(fig,'01_CBM_and_domain_maps')

    units=['Days/year','Smoke days/year','Mean annual burned area (%)','Events/year','Source frequency (NRI days/year)',
           'Event-days/year','Events/year','Events/year','Events/year']
    fig,axes=plt.subplots(3,3,figsize=(7.2,7.2))
    fig.subplots_adjust(left=.085,right=.975,bottom=.12,top=.915,wspace=.47,hspace=.72)
    for i,(ax,code,unit) in enumerate(zip(axes.flat,CODES,units)):
        values=n['E_'+code]
        domain=next(v[2] for v in INDICATORS if v[0]==code)
        if code=='HRCN':
            ax.text(.5,.5,'2,299 source-null zeros\nF_HRCN = 1 for all\nNo measured local variation',transform=ax.transAxes,ha='center',va='center',fontsize=8)
            ax.set_xlim(-.5,.5);ax.set_yticks([])
        else:
            ax.hist(values,bins=25,color=COLORS[domain],edgecolor='white',linewidth=.2)
            ax.set_yscale('log');ax.set_ylabel('Tracts (log count)')
            ax.text(.98,.92,f'Zero: {int(values.eq(0).sum()):,}',transform=ax.transAxes,ha='right',va='top',fontsize=7)
        ax.set_title(f'({chr(65+i)}) {SHORT[code]}')
        ax.set_xlabel(unit,fontsize=7)
    fig.text(.05,.037,'Raw official estimates unchanged. Burned-area zeros lack released quality flags.\nDrought values match NRI event-days; CDC text calls them event-weeks. These are not interchangeable.',fontsize=7)
    finish(fig,'02_nine_indicator_original_units')

    v=pd.read_csv(lp(OUT/'CBM_DOMAIN_AND_INDICATOR_CONTRIBUTIONS.csv')).query("type=='indicator'").set_index('component').reindex(CODES)
    loo=pd.read_csv(lp(OUT/'CBM_RESEARCHER_LEAVEOUT_RANK_DIAGNOSTICS.csv')).query("type=='indicator'").set_index('excluded').reindex(CODES)
    fig,axes=plt.subplots(1,2,figsize=(7.2,4.8))
    fig.subplots_adjust(left=.15,right=.97,bottom=.22,top=.84,wspace=.65)
    axes[0].barh(range(9),v.covariance_share_of_local_SPL_variance*100,color=[COLORS[c[2]] for c in INDICATORS])
    axes[0].set_yticks(range(9),[SHORT[c] for c in CODES]);axes[0].invert_yaxis()
    axes[0].set_xlabel('Share of local score variance (%)');axes[0].set_xlim(-3,80)
    axes[0].set_title('(A) Covariance decomposition')
    axes[1].barh(range(9),loo.top230_membership_retention,color='#287e92')
    axes[1].set_yticks(range(9),[SHORT[c] for c in CODES]);axes[1].invert_yaxis()
    axes[1].set_xlim(0,1.04);axes[1].set_xlabel('Top-230 membership retained')
    axes[1].set_title('(B) Leave-one-indicator national rerank')
    fig.text(.045,.05,'(A) Score composition, not causal damage contribution. CDC sums nine indicator ranks, not equal domains.\n(B) Researcher diagnostics only; deleting a local constant can shift national calibration without changing local order.',fontsize=7)
    finish(fig,'03_component_influence_and_leaveout')

    q=pd.read_csv(lp(OUT/'CBM_2299_BY_NINE_INDICATOR_QUALITY.csv'))
    types=[('SOURCE_NULL_OR_EXCLUDED_SET_ZERO','Source-null / excluded zero','#b84a42'),
           ('PROVIDER_CONFIRMED_RECORD_PERIOD_ZERO','Provider-confirmed record zero','#81b4d0'),
           ('ZERO_NO_PUBLISHED_FLAG_UNRESOLVED','Zero, no published flag','#e3ab46'),
           ('POSITIVE_ESTIMATE_WITH_ZERO_RANK','Positive value, rank zero','#9a6b35'),
           ('PROVIDER_OTHER_VALID_ESTIMATE','Other flagged valid value','#318a79'),
           ('POSITIVE_PUBLISHED_ESTIMATE_NO_FLAG','Positive, no published flag','#6b6b78')]
    fig,ax=plt.subplots(figsize=(7.2,4.8));fig.subplots_adjust(left=.16,right=.97,bottom=.28,top=.855)
    left=np.zeros(9)
    for state,label,color in types:
        counts=q.loc[q.quality_state.eq(state)].groupby('indicator').size().reindex(CODES,fill_value=0).to_numpy()
        ax.barh(range(9),counts,left=left,color=color,label=label)
        left+=counts
    assert np.array_equal(left,np.full(9,2299))
    ax.set_yticks(range(9),[SHORT[c] for c in CODES]);ax.invert_yaxis();ax.set_xlim(0,2299)
    ax.set_xlabel('Tracts');ax.set_title('Released flags distinguish values; complete ranks do not prove complete observations')
    fig.legend(handles=[Patch(color=c,label=l) for _,l,c in types],loc='lower center',bbox_to_anchor=(.5,.08),ncol=2,frameon=False,fontsize=7)
    fig.text(.045,.028,'Unresolved burned-area zeros are not asserted missing. F=0 describes the source record, not zero future hazard.',fontsize=7)
    finish(fig,'04_source_flags_and_zero_semantics')

    x=d[P2].join(n[['RPL_CBM']])
    labels=['Initial modeled service','Spectral grid impact','Dependency HHI','Unconstrained deficit (h)',
            'Mean constraint increment (h)','FEMA SOVI (0-100)','log1p(Frozen population)']
    fig,axes=plt.subplots(2,4,figsize=(7.2,4.8));fig.subplots_adjust(left=.07,right=.985,bottom=.18,top=.865,wspace=.52,hspace=.70)
    for i,(ax,col,label) in enumerate(zip(axes.flat,P2,labels)):
        ax.scatter(x[col],x.RPL_CBM,s=2.5,alpha=.25,color='#287e92',rasterized=False)
        a=safe_assoc(x[col],x.RPL_CBM)
        ax.set_title(f'({chr(65+i)}) r={a["Pearson"]:.2f}; rho={a["Spearman"]:.2f}',fontsize=8)
        ax.set_xlabel(label,fontsize=7);ax.set_ylim(0,1)
        if i%4==0:ax.set_ylabel('CDC CBM rank')
    axes.flat[-1].set_axis_off()
    axes.flat[-1].text(.5,.72,'All 2,299 tracts\n\nLinear R2: 0.072\nVIF: 1.078\nSpatial nonlinear R2:\n0.057',transform=axes.flat[-1].transAxes,ha='center',va='top',fontsize=8)
    fig.text(.045,.045,'Same-cohort associations and fixed predictive overlap; not causality or complete statistical independence.\nLow overlap does not resolve omitted quality fields or establish a useful clustering construct.',fontsize=7)
    finish(fig,'05_CBM_relationships_with_P2')

    p=csv('INDEPENDENT_PHYSICAL_MATCHED_VALUES.csv')
    pairs=[('Historical_heat_days_2018_2022','E_NEHD','Prior CDC heat (days/year)','Bulk CDC heat (days/year)'),
           ('Wildfire_high_land_fraction','E_BURN','High-FHSZ land fraction','Burned area (%/year)'),
           ('Wildfire_high_land_fraction','E_SMOKE','High-FHSZ land fraction','Smoke days/year'),
           ('Flood_SFHA_land_fraction_complete','E_RFLD','Known SFHA land fraction','Riverine event-days/year'),
           ('Flood_coastal_V_land_fraction','E_CFLD','Mapped V/VE land fraction','Coastal events/year'),
           ('tract_seismic_PGA','RPL_CBM','Earthquake PGA (g)','CDC CBM rank')]
    fig,axes=plt.subplots(2,3,figsize=(7.2,5.4));fig.subplots_adjust(left=.09,right=.975,bottom=.18,top=.86,wspace=.49,hspace=.7)
    for i,(ax,(a,b,xlabel,ylabel)) in enumerate(zip(axes.flat,pairs)):
        values=pd.concat([p[a],n[b]],axis=1).dropna()
        ax.scatter(values[a],values[b],s=3,alpha=.25,color='#287e92',rasterized=False)
        stat=safe_assoc(values[a],values[b])
        ax.set_title(f'({chr(65+i)}) n={len(values):,}; rho={stat["Spearman"]:.2f}',fontsize=8)
        ax.set_xlabel(xlabel,fontsize=7);ax.set_ylabel(ylabel,fontsize=7)
    fig.text(.045,.045,'Heat agreement uses the SAME source, not independent validation. Fire history and smoke differ from severity.\nNFHL area differs from event frequency; V/VE values include lower-bound partial support. PGA is not a CBM component.',fontsize=7)
    finish(fig,'06_physical_context_correspondence')
    save('SCIENTIFIC_INPUT_HASHES_GEOMETRY.csv',s.records)
    print('Six vector PDFs, 600dpi previews and publication-size renders generated',flush=True)


if __name__=='__main__':
    main()
