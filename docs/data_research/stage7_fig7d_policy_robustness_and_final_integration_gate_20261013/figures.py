"""Vector scientific review figures; no model fitting, no formal output writes."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import geopandas as gpd
import fitz
from common import *

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':8,'axes.labelsize':8,
    'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'axes.spines.top':False,'axes.spines.right':False,
    'pdf.fonttype':42,'ps.fonttype':42})
PALETTE = ['#147f98', '#d07734', '#7a5899']
K4_COLORS = ['#608543', PALETTE[0], PALETTE[1], PALETTE[2]]
HEADER = 'AUTHOR REVIEW CANDIDATE - NOT FORMAL STAGE 7'
CATEGORY_COLORS = ['#ececec', '#e6b260', '#779aae', '#765080']
manifest = []


def emit(fig, name, title, note):
    fig.text(.5, .985, HEADER, ha='center', va='top', fontsize=7, color='#963d29')
    if title:
        fig.suptitle(title, y=.951, fontsize=11)
    fig.text(.035, .015, note, fontsize=7, ha='left', va='bottom')
    fig.savefig(dest('figures/' + name + '.pdf'))
    fig.savefig(dest('figures/' + name + '.png'), dpi=600)
    manifest.append(dict(pdf='figures/' + name + '.pdf', PNG='figures/' + name + '.png',
                         width_inch=fig.get_figwidth(), height_inch=fig.get_figheight(), PNG_dpi=600,
                         vector=True, AI_generated_images=False, formal_paths_written=False))
    plt.close(fig)


def continuous_map(ax, g, values, title, label, cmap='cividis', norm=None, horizontal=False):
    values = pd.Series(values, index=g.index, dtype=float)
    norm = norm or colors.Normalize(values.min(), values.max())
    g.plot(ax=ax, color='#d4d4d4', edgecolor='none')
    g.assign(value=values).plot(column='value', ax=ax, cmap=cmap, norm=norm, edgecolor='none', missing_kwds={'color':'#d4d4d4'})
    ax.set_axis_off()
    ax.set_title(title, pad=6)
    if horizontal:
        cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, orientation='horizontal', shrink=.78, fraction=.045, pad=.025)
    else:
        cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=.85, fraction=.043, pad=.014)
    cb.set_label(label, fontsize=7)
    cb.ax.tick_params(labelsize=6.5)
    cb.solids.set_rasterized(False)
    return cb


def category_map(ax, g, categories, title, legend=True):
    categories = pd.Series(categories, index=g.index)
    g.plot(ax=ax, color='#d4d4d4', edgecolor='none')
    eligible_g = g.loc[categories.notna()].assign(category=categories.dropna().astype(int))
    eligible_g.plot(column='category', ax=ax, cmap=colors.ListedColormap(CATEGORY_COLORS), vmin=-.5, vmax=3.5, edgecolor='none')
    ax.set_axis_off()
    ax.set_title(title, pad=6)
    if legend:
        ax.legend(handles=[Patch(facecolor=CATEGORY_COLORS[i], label=n) for i, n in enumerate(['Neither', 'Frozen Q4 only', 'High deficit only', 'Both'])] +
                  [Patch(facecolor='#d4d4d4', label='Zero population')], loc='upper right', fontsize=6, frameon=True)


def original_AC(d, g):
    # Same frozen data, positions, titles, scales and class colors as the prior candidate.
    profiles = frame('inputs/ORIGINAL_UNIT_PROFILES.csv')
    sizes = frame('inputs/QUARTILE_POPULATION_HOSPITAL.csv')
    fig = plt.figure(figsize=(7.2, 8.2))
    gs = fig.add_gridspec(4, 4, height_ratios=[.7, .82, .82, 1.25], left=.08, right=.97, bottom=.11, top=.93, hspace=.75, wspace=.78)
    a1 = fig.add_subplot(gs[0, :2]); a2 = fig.add_subplot(gs[0, 2:])
    q = sizes.loc[sizes.condition.eq('main') & sizes.k.eq(3)].sort_values('model_class')
    a1.bar([1,2,3], q.n_tracts, color=PALETTE); a1.set_xticks([1,2,3], ['C1','C2','C3']); a1.set(ylabel='Tracts', title='(A) Primary K3 class coverage')
    a2.bar([1,2,3], q.population_share*100, color=PALETTE); a2.set_xticks([1,2,3], ['C1','C2','C3']); a2.set(ylabel='Residents (%)', title='Frozen population represented')
    for r in q.itertuples():
        a1.text(r.model_class+1, r.n_tracts+20, str(r.n_tracts), ha='center', fontsize=7)
        a2.text(r.model_class+1, r.population_share*100+.7, f'{r.population_share*100:.2f}', ha='center', fontsize=7)
    a1.set_ylim(0,1400); a2.set_ylim(0,64)
    display = FEATURES.copy(); display[6] = 'Population'
    titles = ['Initial service\n(%)','Spectral grid\nimpact','Dependency\nHHI','Unconstrained\ndeficit (h)',
              'Mean extra\ndeficit (h)','FEMA SOVI\n(0-100)','Mean population\n(persons)','Natural-hazard\nscreen (0-1)']
    for j, (field, title) in enumerate(zip(display, titles)):
        a = fig.add_subplot(gs[1+j//4, j%4])
        vals = profiles.loc[profiles.condition.eq('main') & profiles.k.eq(3) & profiles.variable.eq(field)].sort_values('model_class')
        scale = 100 if field == 'Init_Supply' else 1
        a.bar([1,2,3], vals['mean']*scale, color=PALETTE)
        a.axhline(d[field].mean()*scale, color='black', ls='--', lw=.7)
        a.set_title(('(B) ' if j == 0 else '') + title, fontsize=7)
        a.set_xticks([1,2,3], ['C1','C2','C3']); a.tick_params(labelsize=6)
    membership = frame('inputs/K3_CLUSTER_MEMBERSHIP.csv', 'tract_id').saved_model_class.reindex(g.index)
    a = fig.add_subplot(gs[3, :2])
    g.plot(ax=a, color='#d4d4d4', edgecolor='none')
    gg = g.loc[membership.notna()].assign(class_id=membership.dropna().astype(int))
    gg.plot(column='class_id', ax=a, cmap=colors.ListedColormap(PALETTE), vmin=-.5, vmax=2.5, edgecolor='none')
    a.set_axis_off(); a.set_title('(C) Primary candidate memberships', pad=6)
    a.legend(handles=[Patch(facecolor=PALETTE[c], label='C'+str(c+1)) for c in range(3)] +
             [Patch(facecolor='#d4d4d4', label='Zero population')], loc='upper right', fontsize=6, frameon=True)
    return fig, fig.add_subplot(gs[3, 2:])


def review_figure7(d, g, option):
    fig, ax = original_AC(d, g)
    if option == 'D1':
        old = frame('D1_LEGACY_SCORE_GEOID_VALUES.csv', 'tract_id')
        continuous_map(ax, g, old.SlowVulnerable_Hotspot_Score.reindex(g.index), '(D) Unchanged legacy score', 'Legacy percentile sum (0-4)', 'YlOrRd', colors.Normalize(0,4), horizontal=True)
        top = old.index[old.SlowVulnerable_Hotspot_Top10.astype(bool)]
        g.loc[top].boundary.plot(ax=ax, color='black', linewidth=.65)
        ax.legend(handles=[Patch(facecolor='none', edgecolor='black', label='Original Top10'),
                           Patch(facecolor='#d4d4d4', label='Legacy score N/A (24)')], loc='upper right', fontsize=6)
        note = 'A-C: 2,299 positive-population tracts; 16 unassigned. Dashed lines: cohort means.\nD1: unchanged 2,291-tract legacy score; 24 score-N/A, including 8 residents-bearing zero-housing tracts.'
    elif option == 'D2':
        q4 = d.frozen_SOVI_quartile.eq('Q4')
        high = d.MeanTotal5.ge(FIXED_P75)
        cats = (q4.astype(int) + 2*high.astype(int)).reindex(g.index)
        category_map(ax, g, cats, '(D) Policy-conditioned Q4 / P75 screen', legend=False)
        ax.legend(handles=[Patch(facecolor=CATEGORY_COLORS[i], label=n) for i,n in enumerate(['Neither (1,239)', 'Q4 only (485)', 'High deficit only (481)', 'Both (94)'])] +
                  [Patch(facecolor='#d4d4d4', label='Zero population (16)')], loc='upper right', fontsize=6)
        note = 'All 2,299 positive-population tracts; 16 unassigned. Dashed lines: cohort means.\nD2: frozen Q4 and five-policy total deficit >= 38.38135467381475 h; descriptive, not significant hotspots.'
    else:
        continuous_map(ax, g, d.MeanTotal5.reindex(g.index), '(D) Mean total deficit and frozen Q4', 'Mean total service deficit (h)', horizontal=True)
        q4geom = g.loc[d.index[d.frozen_SOVI_quartile.eq('Q4')]]
        boundary = gpd.GeoSeries([q4geom.geometry.union_all()], crs=g.crs)
        boundary.boundary.plot(ax=ax, color='#161616', linewidth=.35)
        ax.legend(handles=[Patch(facecolor='none', edgecolor='#161616', label='Frozen Q4 extent (579)'),
                           Patch(facecolor='#d4d4d4', label='Zero population (16)')], loc='upper right', fontsize=6)
        note = 'All 2,299 positive-population tracts; 16 unassigned. Dashed lines: cohort means.\nD3: equal descriptive mean of five frozen policy outcomes; Q4 outlines, no extra cutoff or priority score.'
    ax.title.set_fontsize(7)
    emit(fig, 'Figure7_' + option + '_Review', None, note)


def supplementary9():
    ev = frame('inputs/EXISTING_K_EVIDENCE.csv')
    st = frame('inputs/EXISTING_STABILITY.csv')
    fig, ax = plt.subplots(2,2,figsize=(7.2,6.0))
    fig.subplots_adjust(left=.10,right=.94,bottom=.14,top=.88,hspace=.48,wspace=.45)
    ax[0,0].plot(ev.k, ev.mean_WCSS, 'o-', ms=3, color=PALETTE[0]); ax[0,0].axvspan(2.8,4.2,color='#e3eae7',alpha=.6)
    ax[0,0].set(xlabel='K',ylabel='Weighted WCSS',title='(A) Saved-fit elbow evidence')
    ax[0,1].plot(ev.k,ev.mean_silhouette,'o-',ms=3,color=PALETTE[1]);ax[0,1].axvspan(2.8,4.2,color='#e3eae7',alpha=.6)
    ax[0,1].set(xlabel='K',ylabel='Full-cohort mean silhouette',title='(B) Maximum at 4, not selected by score alone')
    for j, (k, color) in enumerate([(3,PALETTE[0]),(4,K4_COLORS[0])]):
        for i, test in enumerate(['seed','geographic','policy','Init_ablation']):
            sub=st.loc[st.k.eq(k)&st.test.eq(test)]
            if test=='policy': sub=sub.loc[sub.condition.str.contains('without_')&sub.condition.str.endswith('__cohort')]
            x0=i+(j-.5)*.18
            ax[1,0].plot([x0,x0],[sub.ARI.min(),sub.ARI.max()],color=color,lw=2)
            ax[1,0].scatter(x0,sub.ARI.mean(),s=20,color=color)
    ax[1,0].set_xticks(range(4),['Seed','Geographic','Policy\nleaveout','Minus\nInit'])
    ax[1,0].set(ylim=(0,1.07),ylabel='ARI',title='(C) Conditional membership sensitivity')
    ax[1,0].legend(handles=[Line2D([],[],marker='o',color=PALETTE[0],label='K3'),Line2D([],[],marker='o',color=K4_COLORS[0],label='K4')])
    a=frame('inputs/K3_CLUSTER_MEMBERSHIP.csv','tract_id').saved_model_class
    b=frame('inputs/K4_CLUSTER_MEMBERSHIP.csv','tract_id').saved_model_class.reindex(a.index)
    trans=pd.crosstab(a,b)
    ax[1,1].pcolormesh(np.arange(5)-.5,np.arange(4)-.5,trans.to_numpy(),cmap='Blues',shading='flat')
    ax[1,1].set(ylim=(2.5,-.5),xticks=range(4),xticklabels=['C1\nInitial\nexception','C2','C3','C4'],yticks=range(3),yticklabels=['C1','C2','C3'],
                xlabel='K4 within-model class',ylabel='K3 within-model class',title='(D) Refinement, not four new mechanisms')
    for i in range(3):
        for j in range(4):
            ax[1,1].text(j,i,str(trans.iloc[i,j]),ha='center',va='center',color='white' if trans.iloc[i,j]>800 else 'black')
    emit(fig,'FigureS9_Consistency_Review','K3 primary interpretation; K4 explicit sensitivity',
         'Existing K2-8 curves reused; no new search or fitted PCA. Ranges are not confidence intervals.\nInit deletion redistributes RQ1 weights. Initial exception: 34 Q-linked plus 4 HAYNES / ALAMITOS-linked.')


def main():
    d=frame('VERIFIED_COOCCURRENCE_TRACT_VALUES.csv','tract_id')
    g=gpd.read_file(lp(OUT/'inputs/FULL_2315_GEOMETRY.gpkg')).set_index('tract_id')
    assert len(g)==2315 and set(d.index).issubset(g.index) and g.geometry.is_valid.all()
    e=frame('Q4_VS_NONQ4_EFFECT_SIZES.csv')
    q=frame('VULNERABILITY_QUARTILE_BURDEN_PROFILES.csv')
    names=['Five_policy_mean','Four_policy_no_Vulnerability','Impact_first','Hospital_first','Degree_first','Betweenness_first','Vulnerability_first','Unconstrained']
    labels=['Five-policy','Four (no V)','Impact','Hospital','Degree','Betweenness','Vulnerability','Unconstrained']
    fig, ax=plt.subplots(2,2,figsize=(7.2,6.5));fig.subplots_adjust(left=.14,right=.96,bottom=.17,top=.84,hspace=.57,wspace=.55)
    for group,color,offset in [('Q4',PALETTE[2],-.16),('nonQ4',PALETTE[0],.16)]:
        means=[]; medians=[]
        for name in names:
            field={'Five_policy_mean':'MeanTotal5','Four_policy_no_Vulnerability':'MeanTotal4_no_Vulnerability',
                   'Unconstrained':'B_unconstrained'}.get(name,'B_'+name.replace('_','-').lower())
            subset=d.loc[d.frozen_SOVI_quartile.eq('Q4') if group=='Q4' else ~d.frozen_SOVI_quartile.eq('Q4')]
            means.append(subset[field].mean());medians.append(subset[field].median())
        ax[0,0].barh(np.arange(8)+offset,means,height=.30,color=color,label=group)
        ax[0,0].scatter(medians,np.arange(8)+offset,s=12,facecolor='white',edgecolor='black',linewidth=.4,zorder=5)
    ax[0,0].set_yticks(range(8),labels);ax[0,0].invert_yaxis();ax[0,0].set(xlabel='Mean deficit (h); circles = median',title='(A) Total burden by vulnerability')
    fig.legend(handles=[Patch(facecolor=PALETTE[2],label='Q4'),Patch(facecolor=PALETTE[0],label='non-Q4')],loc='upper center',bbox_to_anchor=(.5,.91),ncol=2,fontsize=7)
    selected=e.loc[e.protocol.eq('R') & e.comparator.isin(names)].set_index('comparator').reindex(names)
    ax[0,1].barh(np.arange(8)-.16,100*selected.tract_Q4_prevalence,height=.30,color=PALETTE[2],label='Q4')
    ax[0,1].barh(np.arange(8)+.16,100*selected.tract_nonQ4_prevalence,height=.30,color=PALETTE[0],label='non-Q4')
    ax[0,1].set_yticks(range(8),labels);ax[0,1].invert_yaxis();ax[0,1].set(xlabel='Tracts above own P75 (%)',title='(B) R-protocol high-burden prevalence')
    for field,color,label in [('tract_prevalence_difference_pp',PALETTE[0],'Equal tract'),('resident_prevalence_difference_pp',PALETTE[1],'Resident weighted')]:
        ax[1,0].plot(np.arange(8),selected[field],'-o',color=color,ms=3,label=label)
    ax[1,0].axhline(0,color='black',lw=.7);ax[1,0].set_xticks(range(8),['5','4','Imp','Hos','Deg','Bet','Vul','U'])
    ax[1,0].set(ylabel='Q4 minus non-Q4 (pp)',xlabel='Policy definition',title='(C) Descriptive prevalence differences');ax[1,0].legend(fontsize=6.5)
    quart=q.loc[q.comparator.eq('Unconstrained')].set_index('quartile').reindex(['Q1','Q2','Q3','Q4'])
    additional=q.loc[q.comparator.eq('MeanDelta_five')].set_index('quartile').reindex(quart.index)
    ax[1,1].bar(range(4),quart.mean_hr,color='#859caa',label='Unconstrained')
    ax[1,1].bar(range(4),additional.mean_hr,bottom=quart.mean_hr,color='#d29057',label='MeanDelta')
    ax[1,1].set_xticks(range(4),quart.index);ax[1,1].set(ylabel='Mean deficit (h)',title='(D) Baseline + constraint increment');ax[1,1].legend(fontsize=6.5,loc='upper center',bbox_to_anchor=(.5,-.15),ncol=2)
    emit(fig,'01_Q4_vs_NonQ4_Policy_Burden','Frozen vulnerability and burden: global contrasts are descriptive',
         'Same 2,299 positive-population tracts and original quartiles. Policy means use 1,000 matched samples.\nResident weighting counts people represented by tracts, not actual customer outages; no IID significance test.')
    fig, ax=plt.subplots(2,2,figsize=(7.2,6.3));fig.subplots_adjust(left=.10,right=.94,bottom=.14,top=.84,hspace=.35,wspace=.43)
    ax[0,0].scatter(d.MeanTotal5,d.MeanTotal4_no_Vulnerability,s=3,color='#417c8c',alpha=.4)
    bounds=[min(d.MeanTotal5.min(),d.MeanTotal4_no_Vulnerability.min()),max(d.MeanTotal5.max(),d.MeanTotal4_no_Vulnerability.max())]
    ax[0,0].plot(bounds,bounds,color='black',ls='--',lw=.7);ax[0,0].set(xlabel='Five-policy mean deficit (h)',ylabel='Four-policy mean deficit (h)',title='(A) Same tracts, no new trajectories')
    change=d.MeanTotal4_no_Vulnerability-d.MeanTotal5;lim=max(abs(change.min()),abs(change.max()))
    continuous_map(ax[0,1],g,change.reindex(g.index),'(B) Four minus five','Deficit change (h)','RdBu_r',colors.TwoSlopeNorm(0,-lim,lim))
    for a,protocol,title in [(ax[1,0],'F','(C) Four-policy: fixed original cutoff'),(ax[1,1],'R','(D) Four-policy: own P75')]:
        cutoff=FIXED_P75 if protocol=='F' else d.MeanTotal4_no_Vulnerability.quantile(.75)
        category_map(a,g,(d.frozen_SOVI_quartile.eq('Q4').astype(int)+2*d.MeanTotal4_no_Vulnerability.ge(cutoff).astype(int)).reindex(g.index),title,legend=False)
        row=e.loc[e.comparator.eq('Four_policy_no_Vulnerability')&e.protocol.eq(protocol)].iloc[0]
        a.text(.02,.01,f'Joint = {int(row.n_joint)} tracts\n{int(row.population_joint):,} frozen residents',transform=a.transAxes,fontsize=7)
    fig.legend(handles=[Patch(facecolor=CATEGORY_COLORS[i],label=n) for i,n in enumerate(['Neither','Q4 only','High only','Both'])],loc='lower center',bbox_to_anchor=(.5,.085),ncol=4,fontsize=7)
    emit(fig,'02_Five_vs_Four_Policy_Cooccurrence','Policy definition changes membership, not the aggregate direction',
         'F: same 38.38135467381475 h cutoff. R: four-policy cohort P75. No group sizes forced.\nRemoving Vulnerability-first does not remove other geographic or procedural policy dependencies.')
    fig,ax=plt.subplots(2,2,figsize=(7.2,6.4));fig.subplots_adjust(left=.11,right=.94,bottom=.14,top=.84,hspace=.52,wspace=.55)
    thresholds=frame('THRESHOLD_P70_P75_P80_SENSITIVITY.csv')
    for name,color,label in [('Five_policy_mean',PALETTE[0],'Five'),('Four_policy_no_Vulnerability',PALETTE[1],'Four no V'),('Impact_first',PALETTE[2],'Impact')]:
        part=thresholds.loc[thresholds.comparator.eq(name)&thresholds.protocol.eq('R')].sort_values('percentile')
        ax[0,0].plot(part.percentile,part.tract_prevalence_difference_pp,'-o',color=color,label=label,ms=3)
    ax[0,0].axhline(0,color='black',lw=.7);ax[0,0].set(xticks=[70,75,80],xlabel='Within-comparator percentile',ylabel='Q4 minus non-Q4 (pp)',title='(A) Limited R-threshold sensitivity');ax[0,0].legend(fontsize=6.5)
    block=frame('SPATIAL_COMMON_SUPPORT_STANDARDIZATION.csv').query("comparator == 'Five_policy_mean'")
    values=[selected.loc['Five_policy_mean','tract_prevalence_difference_pp'],
            block.loc[block.grouping.eq('block_5000')&block.weighting.eq('tract'),'standardized_difference_pp'].iloc[0],
            block.loc[block.grouping.eq('block_10000')&block.weighting.eq('tract'),'standardized_difference_pp'].iloc[0]]
    ax[0,1].bar([0,1,2],values,color=['#576a80','#558c77','#a99256']);ax[0,1].axhline(0,color='black',lw=.7)
    ax[0,1].set_xticks([0,1,2],['Global\n2,299','5 km\n1,075','10 km\n1,723']);ax[0,1].set(ylabel='Q4 minus non-Q4 (pp)',title='(B) Different geographic common supports')
    spatial=frame('SPATIAL_AND_K3_STRATIFIED_CHECKS.csv').query("comparator == 'Five_policy_mean' and grouping == 'K3_class'").sort_values('group')
    ax[1,0].bar(np.arange(3)-.16,100*spatial.tract_Q4_prevalence,width=.30,color=PALETTE[2],label='Q4')
    ax[1,0].bar(np.arange(3)+.16,100*spatial.tract_nonQ4_prevalence,width=.30,color=PALETTE[0],label='non-Q4')
    ax[1,0].set_xticks(range(3),['C1','C2','C3']);ax[1,0].set(ylabel='Above global five-policy P75 (%)',title='(C) K3 strata share fitted inputs');ax[1,0].legend(fontsize=6.5)
    blocks=frame('SPATIAL_LEAVEOUT_SUMMARY.csv').query("test == 'leave_group_out_R_full_comparator_cutoff'").set_index('grouping').reindex(['block_5000','block_10000','broad_region']).reset_index()
    for i,row in enumerate(blocks.itertuples()):
        ax[1,1].plot([row.min_difference_pp,row.max_difference_pp],[i,i],color='#417c8c',lw=2)
        ax[1,1].scatter([row.min_difference_pp,row.max_difference_pp],[i,i],color='#417c8c',s=12)
    ax[1,1].axvline(0,color='black',lw=.7);ax[1,1].set_yticks(range(len(blocks)),['5 km cells','10 km cells','Broad regions']);ax[1,1].set(xlabel='Q4 minus non-Q4 range (pp)',title='(D) Leave-region-out descriptions')
    emit(fig,'03_Threshold_and_Spatial_Sensitivity','Global overlap is not a spatially universal relationship',
         'Common-support block standardization is descriptive and partial; it is not causal adjustment.\nStrong spatial dependence; no spatial p-value or significant-hotspot claim. K3 is not independent validation.')
    for option in ['D1','D2','D3']:
        review_figure7(d,g,option)
    supplementary9()
    dump('FIGURE_MANIFEST.json',dict(figures=manifest,numbered_formal_figures_unchanged=True,all_data_frozen=True,AI_generated_images=False))
    for record in manifest:
        with fitz.open(str(lp(OUT/record['pdf']))) as pdf:
            for index,page in enumerate(pdf):
                page.get_pixmap(matrix=fitz.Matrix(2,2)).save(str(dest('tmp/pdfs/'+Path(record['pdf']).stem+'_page'+str(index+1)+'_review.png')))
    print('Seven review vector PDFs and600dpi previews;noformalwrites',flush=True)


if __name__ == '__main__':
    main()
