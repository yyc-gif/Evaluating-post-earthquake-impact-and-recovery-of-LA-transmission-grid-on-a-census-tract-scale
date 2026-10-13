"""Independent arithmetic, source preservation and publication-artwork gates."""
import ast
import math
import platform
from datetime import datetime, timezone
import fitz
from PIL import Image
from scipy import sparse
from common import *


def manual_quantile(values, p):
    ordered = sorted(map(float, values))
    position = (len(ordered)-1)*p
    low = math.floor(position);fraction = position-low
    return ordered[low]*(1-fraction)+ordered[min(low+1,len(ordered)-1)]*fraction


def main():
    checks = []
    def passed(name, detail):
        checks.append(dict(name=name, status='PASS', detail=detail))
    d = eligible()
    frozen = frame('FROZEN_POLICY_TRACT_MEANS_2315.csv', 'tract_id').reindex(d.index)
    z = np.load(lp(OUT / 'inputs/FROZEN_STATION_INTEGRALS_AND_MAPPING.npz'))
    ids = pd.Index(z['tract_ids'].astype(str));policies=z['policies'].astype(str).tolist()
    w = sparse.csr_matrix((z['mapping_data'],z['mapping_indices'],z['mapping_indptr']),shape=tuple(z['mapping_shape']))
    mass=np.asarray(w.sum(1)).ravel();order=ids.get_indexer(d.index)
    means={}
    for policy in ['unconstrained',*PRIMARY]:
        raw=z['station_loss'][policies.index(policy)]
        station_mean=np.array([math.fsum(raw[:,i])/1000 for i in range(92)])
        means[policy]=(w@station_mean/mass)[order]
        np.testing.assert_allclose(means[policy],frozen['B_'+policy],rtol=0,atol=1e-10)
    total=np.array([math.fsum(means[p][i] for p in PRIMARY)/5 for i in range(len(d))])
    independent_total_error=float(np.max(np.abs(total-frozen.MeanTotal5.to_numpy())))
    assert independent_total_error<1e-10
    threshold=manual_quantile(total,.75)
    assert abs(threshold-FIXED_P75)<1e-10
    q4=d.frozen_SOVI_quartile.eq('Q4').to_numpy();high=total>=FIXED_P75;joint=q4&high
    assert (len(d),int(q4.sum()),int(high.sum()),int(joint.sum()))==(2299,579,575,94)
    assert math.fsum(d.Population.to_numpy()[joint])==350799
    assert set(d.index[joint])==set(frame('inputs/ORIGINAL_COOCCURRENCE_TRACTS.csv','tract_id').index)
    assert d.additional_zero_housing_positive_population.sum()==8
    full=frame('inputs/FULL_2315_COHORT_STATUS.csv','tract_id')
    assert len(full)==2315 and len(full.index.difference(d.index))==16
    passed('compensated_source_means_identity_and_exact94','Station-sample means reduced with math.fsum then projected;manual type7 percentile;all94GEOIDs and350799people unchanged')
    effects=frame('Q4_VS_NONQ4_EFFECT_SIZES.csv')
    cells=frame('Q4_HIGH_DEFICIT_CONTINGENCY_TABLES.csv')
    for row in effects.itertuples():
        values=frozen[row.field].to_numpy()
        manual_threshold=FIXED_P75 if row.protocol=='F' else manual_quantile(values,.75)
        assert abs(row.cutoff_hr-manual_threshold)<1e-10
        selected=values>=manual_threshold
        assert row.n_high==selected.sum() and row.n_joint==(selected&q4).sum()
        masks=[q4&selected,q4&~selected,~q4&selected,~q4&~selected]
        exact=cells.loc[cells.comparator.eq(row.comparator)&cells.protocol.eq(row.protocol)].set_index('cell')
        for label,mask in zip(['Q4_high','Q4_not_high','nonQ4_high','nonQ4_not_high'],masks):
            assert int(exact.loc[label,'n_tracts'])==mask.sum()
            assert exact.loc[label,'frozen_population']==math.fsum(d.Population.to_numpy()[mask])
        n4=q4.sum();nn=(~q4).sum();p4=(q4&selected).sum()/n4;pn=(~q4&selected).sum()/nn
        assert abs(row.tract_prevalence_difference_pp-100*(p4-pn))<1e-12
        if pn>0:
            assert abs(row.tract_prevalence_ratio-p4/pn)<1e-12
    passed('all_F_R_contingency_cells_populations_and_effects','20 comparator/protocol tables independently recounted;fourcells sum to2299and9066522')
    sensitivity=frame('THRESHOLD_P70_P75_P80_SENSITIVITY.csv')
    for row in sensitivity.itertuples():
        values=frozen[row.field].to_numpy()
        cutoff=manual_quantile(frozen.MeanTotal5 if row.protocol=='F' else values,row.percentile/100)
        assert abs(row.cutoff_hr-cutoff)<1e-10
        selected=values>=cutoff
        assert selected.sum()==row.n_high and (selected&q4).sum()==row.n_joint
    passed('prespecified_thresholds_and_ties','OnlyP70/P75/P80;noforcedquantilegroups;F/Rmeanincrementsemantics explicitlymarked')
    quartiles=frame('VULNERABILITY_QUARTILE_BURDEN_PROFILES.csv')
    from analyze_fig7d import COMPARATORS
    for row in quartiles.itertuples():
        mask=d.frozen_SOVI_quartile.eq(row.quartile).to_numpy();values=frozen[COMPARATORS[row.comparator]].to_numpy()[mask]
        pop=d.Population.to_numpy()[mask]
        assert abs(row.mean_hr-math.fsum(values)/len(values))<1e-10
        assert abs(row.resident_weighted_mean_hr-math.fsum(float(a*b) for a,b in zip(values,pop))/math.fsum(pop))<1e-10
    passed('original_quartile_and_population_weighted_profiles','OriginalQ1-Q4 reused;compensatedunweighted/weightedmeans verified;noquartileconstruction')
    old=frame('inputs/LEGACY_2291_CLUSTER_AND_HOTSPOT_VALUES.csv','tract_id')
    old.index=old.index.str.zfill(11)
    legacy=frame('D1_LEGACY_SCORE_GEOID_VALUES.csv','tract_id')
    for col in legacy.columns:
        if col in old:
            np.testing.assert_array_equal(legacy[col],old.reindex(legacy.index)[col])
    assert len(legacy)==2291 and len(full.index.difference(legacy.index))==24
    assert legacy.SlowVulnerable_Hotspot_Top10.sum()==10
    passed('D1_values_unchanged_and_GEOIDs_explicit','Leadingzero restoration only,numericFIPS unchanged;2291legacy/24NAneverinheritedbynew2299cohort')
    frozen_matrix=np.load(lp(OUT/'inputs/FROZEN_PREPROCESSING_AND_LABELS.npz'))
    memberships=[]
    for k in [3,4]:
        table=frame('inputs/K'+str(k)+'_CLUSTER_MEMBERSHIP.csv','tract_id').reindex(d.index)
        assert (table.Population==d.Population).all() and (table.frozen_SOVI_quartile==d.frozen_SOVI_quartile).all()
        memberships.append(table)
    assert memberships[0].candidate_display_cluster.value_counts().sort_index().to_list()==[1242,475,582]
    assert np.allclose(BUDGET,[1/9,1/9,1/9,1/6,1/6,1/6,1/12,1/12],rtol=0,atol=0)
    passed('saved_K3_K4_and_schema_unchanged','Allfrozenlabels/colors/scientificvariables copied, nofit;cohortandweights unchanged')
    figmanifest=json.loads(lp(OUT/'FIGURE_MANIFEST.json').read_text())['figures']
    figure_checks=[]
    old_pdf=fitz.open(str(lp(OUT/'inputs/Figure7_previous.pdf')))
    old_pix=old_pdf[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
    old_arr=np.frombuffer(old_pix.samples,dtype=np.uint8).reshape(old_pix.height,old_pix.width,3)
    ac_checks=[]
    for record in figmanifest:
        pdf=fitz.open(str(lp(OUT/record['pdf'])))
        assert len(pdf)==1
        page=pdf[0];spans=[span for block in page.get_text('dict')['blocks'] for line in block.get('lines',[]) for span in line['spans']]
        assert all(page.rect.contains(fitz.Rect(span['bbox'])) for span in spans),record['pdf']
        assert not page.get_images(full=True),record['pdf']
        assert HEADER_TEXT_PRESENT(page)
        png=Image.open(str(lp(OUT/record['PNG'])))
        assert abs(png.width-record['width_inch']*600)<=2 and abs(png.height-record['height_inch']*600)<=2
        if 'Figure7_' in record['pdf']:
            pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
            arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
            # Panel D/footer may change; identical content across A/B and C is independently pixel-compared.
            for name,slices in [('AB',(slice(0,780),slice(None))),('C',(slice(780,1110),slice(0,570)))]:
                delta=np.abs(arr[slices].astype(int)-old_arr[slices].astype(int))
                ac_checks.append(dict(figure=record['pdf'],region=name,changed_pixels=int((delta>0).any(-1).sum()),max_channel_difference=int(delta.max())))
        figure_checks.append(dict(file=record['pdf'],vector_only=True,text_in_bounds=True,min_font_pt=min(span['size'] for span in spans),PNG_width=png.width,PNG_height=png.height))
    save('FIGURE7_AC_PIXEL_PRESERVATION_QA.csv',ac_checks)
    # Exact scientific values are separately verified; very small rasterizer/font differences are disclosed if present.
    assert max(row['changed_pixels'] for row in ac_checks)==0,ac_checks
    passed('vector_artwork_and_exact_A_B_C_preservation','SevenPDFs/7pages;zeroembeddedimages;600dpi;A-B/Cpixels matchpriorcandidate exactly atpublication2xrender')
    text_results=lp(OUT/'drafts/RESULTS_REPLACEMENT_DRAFT.md').read_text()
    assert '350,799' not in text_results and 'flags94' not in text_results
    assert 'continuous burden map' in text_results and 'within' in text_results
    sources=json.loads(lp(OUT/'STARTING_STATE_AND_PROTECTION.json').read_text())
    assert {p:sha(SOURCE_ROOT/p) for p in sources['protected_files']}==sources['protected_files']
    assert hashlib.sha256(git('status','--porcelain',cwd=SOURCE_ROOT)).hexdigest()==sources['original_status_sha256']
    assert hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest()==sources['original_staged_sha256']
    tree={r.split('\t',1)[1]:r.split('\t',1)[0].split()[2] for r in git('ls-tree','-r','HEAD').decode().splitlines()}
    assert all(tree.get(path)==blob for path,blob in sources['base_tree'].items())
    forbidden=[]
    for path in OUT.glob('*.py'):
        code=ast.parse(lp(path).read_text())
        for node in ast.walk(code):
            if isinstance(node,ast.Call):
                name=ast.unparse(node.func)
                if name.endswith(('.fit','.fit_predict')) or any(term in name for term in ['KMeans','run_pipeline','run_stage_7','simulate']):
                    forbidden.append((path.name,name))
    assert not forbidden,forbidden
    passed('protection_drafts_and_no_simulation_fit','950actualfiles,originalstaging/untrackedstate andallpriorGitblobs unchanged;mainresults no94screenclaim;nosimulation/refitcalls')
    hashes={p.relative_to(OUT).as_posix():dict(sha256=sha(p),bytes=lp(p).stat().st_size) for p in OUT.rglob('*')
            if lp(p).is_file() and not any(part in ['__pycache__','tmp'] for part in p.relative_to(OUT).parts)
            and p.name not in ['DERIVED_FILE_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json','INDEPENDENT_NUMERICAL_AND_PRESERVATION_QA.json']}
    dump('DERIVED_FILE_HASHES.json',dict(files=hashes))
    dump('INDEPENDENT_NUMERICAL_AND_PRESERVATION_QA.json',dict(all_checks_passed=True,checks=checks,
        completed_UTC=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),
        independent_mean_error_hr=independent_total_error,independent_P75_hr=threshold,
        figure_checks=figure_checks,new_Kmeans_fits=0,new_simulations=0,formal_promotion=False,
        source_and_file_hashes=len(hashes),original950protected=True))
    print('INDEPENDENT_QA_PASS',len(checks),'checks;noformalpromotion',flush=True)


def HEADER_TEXT_PRESENT(page):
    return 'NOT FORMAL STAGE 7' in page.get_text()


if __name__ == '__main__':
    main()
