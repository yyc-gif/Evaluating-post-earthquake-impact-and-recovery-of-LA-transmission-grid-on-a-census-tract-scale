"""Replay the adopted seven-variable P2 authority and approved figure suite.

Reads hash-bound saved results only. No K-means, simulation, or scheduling.
"""
from pathlib import Path
import io
import json
import re
import sys

import fitz
import numpy as np
import pandas as pd
from reportlab import rl_config

import consolidate_current_figure_suite as u
from short_current_captions_20261013 import brief_caption_page
import figure_presentation
import figure7_map_readability_20261015 as figure7_maps
import figure7_final_presentation_20261016 as figure7_final
from restoration_strategy_display import STRATEGY_DISPLAY_NAMES

ROOT = u.ROOT
BASE = '937fa2b1ab9953d8411a08fbbd0400cf3b52bd8f'
CURRENT_SUITE_BASE = '0f67aa1f2758fcf1d35c112c36eb04e6d8a5dd68'
MAP_REVIEW_BASE = '0134bfc5b27a8c518078873e21c6151675523b68'
FIGURE_BASELINE_COMMIT = '2779c0b0f2694af2818debeb69241edbe8762260'
FIGURE_BASELINE_SHA256 = '7a85c1d46e9d28309b955f986fb61b12b33064744aceb573ac3c598ed5f93b21'
PB = 'docs/data_research/stage7_path_b_p2_integration_review_20261014/'
AUTH = ROOT / 'results/stage7/2026-10-14'
DEST = ROOT / 'results/figure_review'
GEN = 'src/la_grid/plotting/build_current_suite_p2.py'
PRESENTATION = 'src/la_grid/plotting/figure_presentation.py'
FEATURES = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained',
            'MeanDelta', 'SOVI_SCORE', 'log1p_Population']
BUDGETS = np.array([1/9, 1/9, 1/9, 1/6, 1/6, 1/6, 1/6])
COLORS = ['#3C9198', '#52699E', '#C69EBA']
ACTIVE = [f'Main/Fig{i:02d}' for i in range(1, 8)] + [f'Supplement/FigS{i:02d}' for i in range(1, 10)]
STRATEGY_LABEL_FIGURES = ['Main/Fig04','Main/Fig05','Main/Fig06',
                          'Supplement/FigS03','Supplement/FigS08']
SOURCES = {}


def source(rel, commit=BASE):
    raw = u.payload(commit, rel)
    SOURCES[rel] = dict(commit=commit, sha256=u.digest(raw), bytes=len(raw))
    return raw


def frame(rel):
    return pd.read_csv(io.BytesIO(source(rel)), dtype={'tract_id': str}, float_precision='round_trip')


def csv(path, data):
    u.write(path, data.to_csv(index=False, float_format='%.17g', lineterminator='\n'))


def adopt_authority():
    """Revalidate the saved P2 authority without writing scientific products."""
    full = frame(PB + 'FROZEN_P2_TRACT_TABLE_2315.csv').sort_values('tract_id').reset_index(drop=True)
    f = full.loc[full.Population.gt(0)].copy()
    assert len(full) == 2315 and len(f) == 2299 and f.Population.sum() == 9066522
    assert full.tract_id.str.fullmatch(r'\d{11}').all() and full.tract_id.is_unique
    assert f.additional_zero_housing_positive_population.sum() == 8
    assert f.P2_K3_class.value_counts().sort_index().tolist() == [1235, 428, 636]
    assert f.frozen_SOVI_quartile.eq('Q4').sum() == 579
    weights = frame(PB + 'P2_STANDARDIZER_AND_WEIGHTS.csv')
    assert weights.variable.tolist() == FEATURES
    np.testing.assert_allclose(weights.squared_distance_budget, BUDGETS, atol=1e-16, rtol=0)
    np.testing.assert_allclose(weights.coordinate_multiplier, np.sqrt(BUDGETS), atol=1e-16, rtol=0)
    raw = f[FEATURES].to_numpy()
    assert np.isfinite(raw).all()
    np.testing.assert_allclose(raw.mean(0), weights.cohort_mean, atol=1e-12, rtol=1e-13)
    np.testing.assert_allclose(raw.std(0), weights.population_SD, atol=1e-12, rtol=1e-13)
    arrays = np.load(io.BytesIO(source(PB + 'inputs/REGISTERED_FIT_ARRAYS.npz')))
    matrices = np.load(io.BytesIO(source(PB + 'inputs/VERIFIED_WEIGHTED_MATRICES.npz')))
    ids = f.tract_id.to_numpy().astype('U11')
    np.testing.assert_array_equal(ids, arrays['tract_ids'])
    np.testing.assert_array_equal(ids, matrices['tract_ids'])
    weighted = matrices['P2__main5__cohort']
    np.testing.assert_allclose((raw-weights.cohort_mean.to_numpy())/weights.population_SD.to_numpy()
                              *np.sqrt(BUDGETS), weighted, atol=2e-12, rtol=0)
    saved = {}
    for k in [3, 4]:
        index = list(arrays['keys']).index(f'P2__main5__cohort__k{k}__s42')
        saved[k] = arrays['labels'][index]
        field = 'P2_K3_class' if k == 3 else 'P2_K4_sensitivity_class'
        np.testing.assert_array_equal(saved[k]+1, f[field])
    policy = frame(PB + 'inputs/FROZEN_POLICY_TRACT_MEANS_2315.csv').set_index('tract_id').loc[f.tract_id]
    policies = ['impact-first', 'hospital-first', 'degree-first', 'betweenness-first', 'vulnerability-first']
    np.testing.assert_allclose(f.MeanTotal5, policy[['B_'+p for p in policies]].mean(axis=1), atol=1e-12, rtol=0)
    np.testing.assert_allclose(f.MeanTotal5, f.B_Unconstrained+f.MeanDelta, atol=1e-12, rtol=0)
    np.testing.assert_array_equal(f.Population, policy.Population)
    np.testing.assert_array_equal(f.frozen_SOVI_quartile, policy.frozen_SOVI_quartile)
    keep = ['tract_id', *FEATURES, 'Population', 'frozen_SOVI_quartile',
            'additional_zero_housing_positive_population', 'MeanTotal5']
    saved_features = pd.read_csv(io.BytesIO(source('results/stage7/2026-10-14/tract_features.csv', CURRENT_SUITE_BASE)),
                                 dtype={'tract_id': str}, float_precision='round_trip')
    np.testing.assert_array_equal(saved_features.tract_id, f.tract_id)
    np.testing.assert_array_equal(saved_features.K3_class, f.P2_K3_class)
    np.testing.assert_array_equal(saved_features.Population, f.Population)
    np.testing.assert_array_equal(saved_features.SOVI_SCORE, f.SOVI_SCORE)
    np.testing.assert_array_equal(saved_features.MeanTotal5, f.MeanTotal5)
    schema = json.loads(source('results/stage7/2026-10-14/feature_schema_and_identity.json', CURRENT_SUITE_BASE))
    assert schema['feature_names'] == FEATURES and schema['primary_K'] == 3
    assert schema['eligible_tracts'] == 2299 and schema['full_domain_tracts'] == 2315
    assert schema['squared_distance_budgets'] == BUDGETS.tolist()
    artifact_hashes = json.loads(source('results/stage7/2026-10-14/ARTIFACT_HASHES.json', CURRENT_SUITE_BASE))
    for name, expected in artifact_hashes.items():
        actual = u.digest(source('results/stage7/2026-10-14/' + name, CURRENT_SUITE_BASE))
        assert actual == expected, name
    current = json.loads(source('config/current_stage7.json', CURRENT_SUITE_BASE))
    assert current['primary_K'] == 3 and current['fitted_feature_count'] == 7
    return schema


def captions():
    text = source('results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md', CURRENT_SUITE_BASE).decode('utf-8')
    items = [(title.strip(), body.strip()) for title, body in
             re.findall(r'^## (.+?)\n\n(.*?)(?=^## |\Z)', text, re.M | re.S)]
    assert len(items) == 16
    short_bodies = [
        'Study workflow from tract-substation mapping and earthquake damage to modeled service recovery, restoration strategies, and community outcomes. T80 is time to 80% modeled tract-service availability; availability is a network proxy, not delivered electricity.',
        'Transmission network, tract-substation mapping, and comparison of candidate tract assignments with public SCE assignments. Assignment agreement does not validate feeder boundaries or recovery outcomes.',
        'Earthquake damage and initial modeled service are followed by Unconstrained recovery outcomes. Service loss is integrated over 0-480 h; applicable whiskers show the 5th-95th realization range.',
        'Modeled recovery trajectories and service-loss comparisons across restoration strategies, vulnerability groups, and hospital-linked tracts. All applicable whiskers show 5th-95th realization ranges (not confidence intervals); service-loss bars show means. Hospital-linked service is a tract proxy, not power delivered to hospitals.',
        'Vulnerability-first outcomes across SOVI groups and relative to the named reference strategies. Whiskers show the 5th-95th realization range; negative tract-level differences favor Vulnerability-first.',
        'Vulnerability-first effects across crew-availability and repair-duration scenarios. Whiskers are 95% bootstrap confidence intervals for mean effects (not realization ranges); some comparisons show means only.',
        'Empirical distributions for six selected variables (A), standardized means for all seven fitted variables (B), K3 community geography (C), and tract-level recovery burden with SOVI context (D). Panel D shows five-strategy mean service-deficit hours and continuous SOVI; outlines mark the Q4/P75 descriptive screen, not a composite score or significance test.',
        'Station damage severity and corresponding initial modeled tract-service availability. Availability is a network proxy, not physical MW or observed customer outages.',
        'Crew bases, station tasks, and task-to-task travel times used in restoration scheduling. These are pre-event scheduling inputs, not post-earthquake traffic forecasts.',
        'Recovery of the largest connected-component fraction and mean degree within that component among functional substations. The curves describe network topology, not power flow or delivered electricity.',
        'Search and validation diagnostics for genetic-algorithm restoration sequences. Each run\'s best initial order is compared with its best final order; a global optimum is not established.',
        'Sensitivity of modeled service loss to dependency cutoff and source/threshold assumptions. Panel B isolates source-connectivity removal at fixed 0.50 functionality; (C) Functionality thresholds 0.05 and 0.75 retain source connectivity.',
        'Dynamic and static source-connectivity measures and alternate-path contributions under their stated conditioning. These are connectivity probabilities, not delivered power.',
        'Provider planning loads, reported limits, and modeled service-loss changes under capacity ceilings. Post-earthquake load flow and complete electrical-capacity adequacy are not assessed.',
        'Repair-priority geography for Hospital-first, Vulnerability-first, and Impact-first strategies. The blue-green scale shows population; outcome comparisons appear in Figures 4-6 and Supplementary Figure S9.',
        'Absolute modeled service losses under crew-availability and repair-duration variations, reported separately for overall, Q4, Q4-Q1, and hospital-linked outcomes. Whiskers show the 5th-95th realization range.'
    ]
    assert len(short_bodies) == len(items)
    items = [(title, body) for (title, _), body in zip(items, short_bodies)]
    s3_title, _ = items[9]
    items[9]=(s3_title.replace('Structural criticality and functional-network recovery',
                               'Functional-network recovery'), items[9][1])
    assert len(items) == 16
    assert [int(x) for x in re.findall(r'^Supplementary Figure S(\d+)\.', '\n'.join(t for t,b in items), re.M)] == list(range(1,10))
    return items


def update_explorer_display_labels(path):
    """Keep the offline evidence viewer's visible policy names in sync."""
    text=path.read_text(encoding='utf-8')
    labels=json.dumps(STRATEGY_DISPLAY_NAMES,separators=(',',':'),ensure_ascii=False)
    old='const cname=p=>D.policies[p]||p;'
    new=f'const strategyDisplayNames={labels};const cname=p=>strategyDisplayNames[p]||D.policies[p]||p;'
    if old in text:
        text=text.replace(old,new)
    else:
        pattern=r'const strategyDisplayNames=\{[^}]*\};const cname=p=>strategyDisplayNames\[p\]\|\|D\.policies\[p\]\|\|p;'
        text,count=re.subn(pattern,lambda _:new,text,count=1)
        assert count==1,'The offline viewer no longer exposes its strategy label hook.'
    u.write(path,text)
    return u.sha(path)


def packets(caps, registry_path):
    u.pdfmetrics.registerFont(u.TTFont('SuiteArial', 'C:/Windows/Fonts/arial.ttf'))
    u.pdfmetrics.registerFont(u.TTFont('SuiteBold', 'C:/Windows/Fonts/arialbd.ttf'))
    rl_config.invariant = 1
    book, main, supp = fitz.open(), fitz.open(), fitz.open()
    registry = []
    for i, (stem, (title, body)) in enumerate(zip(ACTIVE, caps)):
        with fitz.open(u.lp(DEST/(stem+'.pdf'))) as art:
            (main if i < 7 else supp).insert_pdf(art)
            w, h = art[0].rect.width, art[0].rect.height
            with brief_caption_page(title, body, w) as cap:
                page = book.new_page(width=w, height=h+cap[0].rect.height)
                page.show_pdf_page(fitz.Rect(0,0,w,h), art, 0)
                page.show_pdf_page(fitz.Rect(0,h,w,page.rect.height), cap, 0)
                registry.append(dict(figure=stem, packet_page=i+1, figure_height_pt=h,
                    caption_height_pt=cap[0].rect.height, caption_stream_sha256=u.digest(cap[0].read_contents()),
                    caption_min_font_pt=10, caption_bounds_valid=True, title=title, caption=body))
            if stem in {'Main/Fig01','Main/Fig07'}:
                preview = 'results/figure_review/Page_Previews/'+Path(stem).name+'.png'
                u.write(ROOT/preview, art[0].get_pixmap(dpi=150).tobytes('png'))
            else:
                preview = 'results/figure_review/Page_Previews/'+Path(stem).name+'.png'
                u.write(ROOT/preview, source(preview,CURRENT_SUITE_BASE))
    for name, doc in [('ALL_FIGURES_WITH_CAPTIONS.pdf', book), ('ALL_MAIN_FIGURES.pdf', main),
                      ('ALL_SUPPLEMENT_FIGURES.pdf', supp)]:
        u.write(DEST/name, doc.tobytes(garbage=4, deflate=True, no_new_id=True))
        doc.close()
    u.write_csv(registry_path, registry)


def main():
    spec = adopt_authority()
    print('[build] frozen P2 inputs verified',flush=True)
    original_manifest = u.csv_rows(source('results/figure_review/FIGURE_MANIFEST.csv',CURRENT_SUITE_BASE))
    original_index = u.csv_rows(source('results/figures/FIGURE_INDEX.csv',CURRENT_SUITE_BASE))
    review_dir=ROOT/'results/diagnostics/1021/restoration_methods_s03_revision_20261019'
    review_dir.mkdir(parents=True,exist_ok=True)
    previous=review_dir/'BUILD_CHECKPOINT.json'
    preservation_before_path=review_dir/'PRESERVATION_BEFORE.json'
    default_preserve_artwork=sorted({r[k] for r in original_manifest for k in ['current_source_file','mirror_file']}
        | {f'results/figure_review/Page_Previews/{Path(stem).name}.png' for stem in ACTIVE})
    default_preserve_science=[
        'config/current_stage7.json','results/stage7/2026-10-14/tract_features.csv',
        'results/stage7/2026-10-14/feature_schema_and_identity.json',
        'results/stage7/2026-10-14/ARTIFACT_HASHES.json',
        'FINAL_REVISION_RUN_SEQUENCE/03_GA_AND_STRATEGY_FREEZE/FINAL_STRATEGY_SET.json',
        'src/la_grid/core/C257H_Project_Main.py',
        'src/la_grid/revision/r1_realization_scheduling.py',
        'src/la_grid/revision/r1_source_gate.py',
        'src/la_grid/revision/r1_vulnerability_first.py']
    tracked_stage7=u.git('ls-files','-z','results/stage7/2026-10-14').decode().split('\0')
    default_preserve_science=list(dict.fromkeys(default_preserve_science+[p for p in tracked_stage7 if p]))
    if preservation_before_path.exists():
        prior_preservation=json.loads(preservation_before_path.read_text(encoding='utf-8'))
        preserve_artwork=list(prior_preservation['active_artwork_hashes'])
        preserve_science=list(prior_preservation['protected_source_hashes'])
        preservation_before={**prior_preservation['active_artwork_hashes'],
                             **prior_preservation['protected_source_hashes']}
    else:
        preserve_artwork=default_preserve_artwork
        preserve_science=default_preserve_science
        preservation_before={rel:u.sha(ROOT/rel) for rel in preserve_artwork+preserve_science}
        u.dump(preservation_before_path,dict(starting_commit=u.git('rev-parse','HEAD').decode().strip(),
            active_artwork_hashes={rel:preservation_before[rel] for rel in preserve_artwork},
            protected_source_hashes={rel:preservation_before[rel] for rel in preserve_science}))
    legacy_display_occurrences_before={}
    for stem in STRATEGY_LABEL_FIGURES:
        with fitz.open(stream=source('results/figure_review/'+stem+'.pdf',CURRENT_SUITE_BASE),filetype='pdf') as art:
            visible=' '.join(art[0].get_text().split())
        legacy_display_occurrences_before[stem]=visible.count('Centrality-first')
    manifest=[];index=[]
    changed={};style_checks={}
    original_f1_path='results/figure_review/Main/Fig01.pdf'
    original_f1=source(original_f1_path,CURRENT_SUITE_BASE)
    revised_f1,f1_layout=figure_presentation.restoration_workflow(original_f1)
    changed['Main/Fig01']=revised_f1
    f1_source_hash=u.digest(original_f1)
    style_checks['Main/Fig01']={
        'source_commit':CURRENT_SUITE_BASE,'source_path':original_f1_path,
        'source_sha256':f1_source_hash,'output_sha256':u.digest(revised_f1),
        'presentation':f1_layout,'scientific_data_changed':False,
        'community_outcomes_panel_unchanged':True}
    print('[build] Figure 1 restoration panel reconstructed',flush=True)
    original_s3_path='results/figure_review/Supplement/FigS03.pdf'
    original_s3=source(original_s3_path,CURRENT_SUITE_BASE)
    original_s3_png=source('results/figure_review/Supplement/FigS03.png',CURRENT_SUITE_BASE)
    revised_s3,s3_layout=figure_presentation.functional_network_recovery(original_s3)
    changed['Supplement/FigS03']=revised_s3
    with fitz.open(stream=original_s3,filetype='pdf') as before_doc, fitz.open(stream=revised_s3,filetype='pdf') as after_doc:
        comparison=fitz.open()
        comparison.insert_pdf(before_doc)
        comparison.insert_pdf(after_doc)
        comparison.set_toc([[1,'Original S3: static percolation and recovery',1],
                            [1,'Revised S3: functional-network recovery',2]])
        u.write(review_dir/'S03_ORIGINAL_VS_REVISED.pdf',comparison.tobytes(garbage=4,deflate=True,no_new_id=True))
        comparison.close()
        u.write(review_dir/'S03_REVISED.pdf',revised_s3)
        u.write(review_dir/'S03_REVISED.png',after_doc[0].get_pixmap(dpi=600,alpha=False).tobytes('png'))
    s3_source_hash=u.digest(original_s3)
    s3_output_hash=u.digest(revised_s3)
    style_checks['Supplement/FigS03']={
        'source_commit':CURRENT_SUITE_BASE,'source_path':original_s3_path,
        'source_sha256':s3_source_hash,'source_png_sha256':u.digest(original_s3_png),
        'output_sha256':s3_output_hash,'layout':s3_layout,
        'policy_sequence_manifest_sha256':u.sha(ROOT/'FINAL_REVISION_RUN_SEQUENCE/03_GA_AND_STRATEGY_FREEZE/FINAL_STRATEGY_SET.json'),
        'centrality_first_sequence_sha256':'435904b411b7c96a533548418ae9a0d8fa1cc46946d92799d2cc0eddc61d5b79',
        'strategy_id_unchanged':'centrality-first','static_analysis_code_or_results_modified':False}
    print('[build] S3 recovery panels reconstructed',flush=True)
    original_s8_path='results/figure_review/Supplement/FigS08.pdf'
    original_s8=source(original_s8_path,CURRENT_SUITE_BASE)
    revised_s8,s8_layout=figure_presentation.apply('Supplement/FigS08',original_s8)
    changed['Supplement/FigS08']=revised_s8
    s8_source_hash=u.digest(original_s8)
    s8_source_png_hash=u.digest(source('results/figure_review/Supplement/FigS08.png',CURRENT_SUITE_BASE))
    style_checks['Supplement/FigS08']={
        'source_commit':CURRENT_SUITE_BASE,'source_path':original_s8_path,
        'source_pdf_sha256':s8_source_hash,'source_png_sha256':s8_source_png_hash,
        'output_sha256':u.digest(revised_s8),'presentation':s8_layout,
        'data_and_geometry_changed':False,'color_only_population_context_change':True}
    full = frame(PB + 'FROZEN_P2_TRACT_TABLE_2315.csv').sort_values('tract_id').reset_index(drop=True)
    table = full.loc[full.Population.gt(0)].copy().reset_index(drop=True)
    display = pd.read_csv(io.BytesIO(source(
        'results/diagnostics/fig7d_continuous_bivariate_20261015/TRACT_DISPLAY_COLORS.csv', MAP_REVIEW_BASE)),
        dtype={'tract_id':str}, float_precision='round_trip')
    specification = json.loads(source(
        'results/diagnostics/fig7d_continuous_bivariate_20261015/COLOR_MAPPING_SPECIFICATION.json', MAP_REVIEW_BASE))
    with np.load(io.BytesIO(source(
            'results/diagnostics/fig7d_continuous_bivariate_20261015/inputs/SOURCE_D_VECTOR_PATHS.npz', MAP_REVIEW_BASE))) as archive:
        paths = json.loads(archive['payload'].tobytes())
    source_screen = pd.read_csv(io.BytesIO(source(
        'results/diagnostics/fig7d_continuous_bivariate_20261015/inputs/ORIGINAL_94_GEOIDS.csv', MAP_REVIEW_BASE)),
        dtype={'tract_id':str}, float_precision='round_trip')
    expected_geoids = {'NA':set(full.loc[full.Population.eq(0),'tract_id']),
                       'high_high':set(source_screen.tract_id)}
    table, display = figure7_maps.verify_inputs(table, display, paths, specification, expected_geoids)
    weights = frame(PB + 'P2_STANDARDIZER_AND_WEIGHTS.csv')
    source_profile = frame(PB + 'P2_ORDINARY_COHORT_Z_CLASS_MEANS.csv').set_index('class_id')
    profile = figure7_final.profile_means(table, weights)
    np.testing.assert_allclose(profile[figure7_final.FEATURES].to_numpy(),
        source_profile.loc[['C1','C2','C3'],figure7_final.FEATURES].to_numpy(), atol=1e-12, rtol=0)
    source_pdf = source('results/figure_review/Main/Fig07.pdf', FIGURE_BASELINE_COMMIT)
    source_pdf_sha = u.digest(source_pdf)
    assert source_pdf_sha == FIGURE_BASELINE_SHA256
    source_png = source('results/figure_review/Main/Fig07.png', FIGURE_BASELINE_COMMIT)
    diagnostic_dir = ROOT/'results/diagnostics/1021/figure7_final_presentation_20261016'
    diagnostic_dir.mkdir(parents=True, exist_ok=True)
    u.write(diagnostic_dir/'FIG07_CURRENT_REFERENCE.pdf', source_pdf)
    u.write(diagnostic_dir/'FIG07_CURRENT_REFERENCE.png', source_png)
    top_b = figure7_final.build_top_panel(table, profile, figure7_final.PROPOSED, layout='B')
    top_c = figure7_final.build_top_panel(table, profile, figure7_final.PROPOSED, layout='C')
    candidate_b = figure7_final.compose_figure(top_b, table, display, paths, specification,
                                                figure7_final.PROPOSED, layout='B')
    candidate_c = figure7_final.compose_figure(top_c, table, display, paths, specification,
                                                figure7_final.PROPOSED, layout='C')
    top_alt = figure7_final.build_top_panel(table, profile, figure7_final.DARKER_MAUVE, layout='B')
    candidate_alt = figure7_final.compose_figure(top_alt, table, display, paths, specification,
                                                   figure7_final.DARKER_MAUVE, layout='B')
    for name, doc in [('FIG07_LAYOUT_B_REVISED', candidate_b),
                      ('FIG07_LAYOUT_C_COMPACT', candidate_c)]:
        figure7_maps.write_pdf(diagnostic_dir/(name+'.pdf'), doc)
        figure7_maps.export_png(diagnostic_dir/(name+'.pdf'), diagnostic_dir/(name+'.png'), dpi=600)
    palette_comparison = fitz.open()
    palette_comparison.insert_pdf(candidate_b)
    palette_comparison.insert_pdf(candidate_alt)
    palette_comparison.set_toc([[1,'Proposed mauve palette',1],[1,'Alternative darker mauve',2]])
    figure7_maps.write_pdf(diagnostic_dir/'FIG07_PALETTE_COMPARISON.pdf', palette_comparison)
    layout_comparison = fitz.open()
    with fitz.open(stream=source_pdf,filetype='pdf') as original:
        layout_comparison.insert_pdf(original)
    layout_comparison.insert_pdf(candidate_b)
    layout_comparison.insert_pdf(candidate_c)
    layout_comparison.set_toc([[1,'Current Figure 7 reference',1],
        [1,'Layout B: 7.2 x 10.0 in, revised palette and labels',2],
        [1,'Layout C: 7.2 x 9.03 in, compact',3]])
    figure7_maps.write_pdf(diagnostic_dir/'FIG07_LAYOUT_COMPARISON.pdf',layout_comparison)
    figure7_maps.COLORS = dict(figure7_final.PROPOSED)
    details = figure7_maps.build_details(table, paths, display, specification, diagnostic_dir,
                                         outline_width=0.25)
    figure7_maps.write_pdf(diagnostic_dir/'FIG07_MAP_DETAILS_C_D.pdf', details)
    for n, page in enumerate(details, start=1):
        page.get_pixmap(dpi=600, alpha=False).save(str(diagnostic_dir/f'FIG07_MAP_DETAILS_PAGE_{n}.png'))
    figure7_final.write_palette_metrics(diagnostic_dir)
    figure7_final.write_accessibility_previews(candidate_b, candidate_c, candidate_alt, diagnostic_dir)
    figure7_final.write_narrow_width_previews(candidate_c, diagnostic_dir)
    figure7_final.write_layout_contact_sheet(source_pdf,candidate_b,candidate_c,diagnostic_dir)
    changed['Main/Fig07']=candidate_c.tobytes(garbage=4,deflate=True,no_new_id=True)
    style_checks['Main/Fig07']={
        'source_commit':FIGURE_BASELINE_COMMIT,'source_pdf_sha256':source_pdf_sha,
        'approved_map_source_commit':MAP_REVIEW_BASE,
        'positive_polygon_parts':len(paths['positive']),'positive_GEOIDs':len(table),
        'NA_polygon_count':len(paths['NA']),'high_high_outline_count':len(paths['high_high']),
        'high_high_population':int(table.set_index('tract_id').Population.loc[
            list(expected_geoids['high_high'])].sum()),
        'high_high_threshold_hr':38.38135467381475,'chosen_outline_width_pt':0.25,
        'contrasting_internal_tract_boundaries':False,
        'same_fill_edge_overprint_pt':figure7_maps.SEAM_OVERLAP_PT,
        'A_ECDF_variable_count':6,'A_ECDF_class_variable_curves':18,
        'B_standardized_profile_cells':21,'B_feature_count':7,
        'profile_reconstruction_max_abs_error':float(np.max(np.abs(
            profile[figure7_final.FEATURES].to_numpy()-source_profile.loc[['C1','C2','C3'],figure7_final.FEATURES].to_numpy()))),
        'palette':{str(k):v for k,v in figure7_final.PROPOSED.items()},
        'layout_B_size_in':[7.2,10.0],'layout_C_size_in':[7.2,figure7_final.LAYOUT_C_H/72],
        'layout_B_map_scale':1.25,'layout_C_map_scale':1.25,'all_map_geometry_vector':True,
        'D_continuous_color_function_unchanged':True,'Figure7_render_isolated_from_other_artwork':True}
    ecdf_rows=figure7_final.ecdf_qa(table)
    u.write_csv(diagnostic_dir/'ECDF_DISTRIBUTION_QA.csv',ecdf_rows)
    profile_rows=[]
    for class_id in ['C1','C2','C3']:
        for variable in figure7_final.FEATURES:
            profile_rows.append(dict(class_id=class_id,variable=variable,
                standardized_mean=float(profile.loc[class_id,variable]),
                saved_reference_mean=float(source_profile.loc[class_id,variable]),
                absolute_difference=abs(float(profile.loc[class_id,variable])-float(source_profile.loc[class_id,variable])),
                display_label=figure7_final.LABELS[variable]))
    u.write_csv(diagnostic_dir/'STANDARDIZED_PROFILE_QA.csv',profile_rows)
    u.dump(diagnostic_dir/'FEATURE_LABELS_AND_PALETTES.json',dict(
        labels=figure7_final.LABELS,panel_A_variables=figure7_final.PANEL_A,
        proposed_palette={str(k):v for k,v in figure7_final.PROPOSED.items()},
        alternative_darker_C3={str(k):v for k,v in figure7_final.DARKER_MAUVE.items()},
        Figure7D_color_function='unchanged pinned CIELAB blue-amber hue and burden lightness'))
    u.dump(diagnostic_dir/'LAYOUT_SPECIFICATIONS.json',dict(
        layout_B={'width_in':7.2,'height_in':10.0,'page_points':[518.4,720],
                  'map_scale':1.25,'text_floor_pt':7.5},
        layout_C={'width_in':7.2,'height_in':figure7_final.LAYOUT_C_H/72,
                  'height_mm':figure7_final.LAYOUT_C_H*25.4/72,
                  'page_points':[518.4,figure7_final.LAYOUT_C_H],
                  'map_scale':1.25,'text_floor_pt':7.5}))
    retired_s3_mirrors=[]
    for stem in ACTIVE:
        original_path='results/figure_review/'+stem+'.pdf'
        original=source(original_path,CURRENT_SUITE_BASE)
        raw=changed.get(stem,original)
        for ext in ['pdf','png']:
            row=next(r.copy() for r in original_manifest if r['final_name']==stem+'.'+ext)
            ix=next(r.copy() for r in original_index if r['source_path']==row['current_source_file'])
            old_mirror=row['mirror_file']
            if stem=='Supplement/FigS03':
                new_name='FigS03_Functional_Network_Recovery.'+ext
                row['mirror_file']='results/figures/'+new_name
                ix['file']=new_name
                ix['scientific_question']='How does functional-network topology recover over time?'
                ix['main_message']='Largest-component fraction and within-component mean degree recover over time.'
                ix['scientific_content']=ix['main_message']
                ix['notes']='Two saved time-dependent network-recovery panels; static percolation is not shown.'
                retired_s3_mirrors.append((old_mirror,preservation_before[old_mirror]))
            if ext=='png':
                if stem in changed:
                    with fitz.open(stream=changed[stem],filetype='pdf') as art:
                        raw=art[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
                else:
                    raw=source('results/figure_review/'+stem+'.png',CURRENT_SUITE_BASE)
            else:
                raw=changed.get(stem,original)
            u.write(ROOT/row['current_source_file'],raw)
            u.write(ROOT/row['mirror_file'],raw)
            before=preservation_before[row['current_source_file']]
            current_hash=u.digest(raw)
            starting_commit=json.loads(preservation_before_path.read_text(encoding='utf-8'))['starting_commit']
            row.update(sha256=current_hash,change_in_this_update='UPDATED' if before!=current_hash else 'RETAINED',
                parent_sha256=before,parent_source_commit=starting_commit,
                parent_source_file=row['current_source_file'],parent_current_source_file=row['current_source_file'])
            if stem in changed:
                with fitz.open(stream=raw,filetype='pdf') as art:
                    size=f'{art[0].rect.width*25.4/72:.3f} x {art[0].rect.height*25.4/72:.3f}'
                if stem=='Main/Fig01':
                    row.update(source_commit=CURRENT_SUITE_BASE,source_file=original_path,
                        presentation_generator=PRESENTATION,presentation_generator_sha256=u.sha(ROOT/PRESENTATION),
                        status='CURRENT_1021_RESTORATION_MODES_CLARIFIED',size_mm=size,
                        parent_sha256=before,parent_source_commit=CURRENT_SUITE_BASE,parent_source_file=original_path)
                    ix.update(source_authority=CURRENT_SUITE_BASE,source_data_path=original_path,
                        source_data_sha256=f1_source_hash,generator=PRESENTATION,
                        notes='Part 4 distinguishes Unconstrained reference restoration from constrained strategy execution; no scientific outputs changed.')
                elif stem=='Main/Fig07':
                    row.update(source_commit=FIGURE_BASELINE_COMMIT,source_file=original_path,
                        presentation_generator=GEN,presentation_generator_sha256=u.sha(ROOT/GEN),
                        status='CURRENT_1021_FIGURE7_PRESENTATION_20261016',min_font_pt='7.500',size_mm=size,
                        parent_sha256=before,parent_source_commit=FIGURE_BASELINE_COMMIT,parent_source_file=original_path)
                    ix.update(source_authority=FIGURE_BASELINE_COMMIT,source_data_path=original_path,
                        source_data_sha256=source_pdf_sha,generator=GEN,
                        notes='Figure 7 palette, labels and layout only; tract values and K3 assignments are unchanged.')
                elif stem=='Supplement/FigS03':
                    row.update(source_commit=CURRENT_SUITE_BASE,source_file=original_path,
                        presentation_generator=PRESENTATION,presentation_generator_sha256=u.sha(ROOT/PRESENTATION),
                        status='CURRENT_1021_FUNCTIONAL_NETWORK_RECOVERY',size_mm=size,
                        parent_sha256=before,parent_source_commit=CURRENT_SUITE_BASE,parent_source_file=original_path)
                    ix.update(source_authority=CURRENT_SUITE_BASE,source_data_path=original_path,
                        source_data_sha256=s3_source_hash,generator=PRESENTATION,
                        notes='Only the two original time-dependent network-recovery panels and their shared legend are shown.')
                else:
                    row.update(source_commit=CURRENT_SUITE_BASE,source_file=original_path,
                        presentation_generator=PRESENTATION,presentation_generator_sha256=u.sha(ROOT/PRESENTATION),
                        status='CURRENT_1021_PRIORITY_MAP_POPULATION_PALETTE',size_mm=size,
                        parent_sha256=before,parent_source_commit=CURRENT_SUITE_BASE,parent_source_file=original_path)
                    ix.update(source_authority=CURRENT_SUITE_BASE,source_data_path=original_path,
                        source_data_sha256=s8_source_hash,generator=PRESENTATION,
                        notes='Population-context colors only; station priorities and tract geography are unchanged.')
            ix['sha256_or_lfs_oid']=current_hash
            ix['current_status']='CURRENT_1021_P2_K3_SUITE'
            manifest.append(row);index.append(ix)
    print('[build] numbered artwork synchronized',flush=True)
    for old_mirror,expected_hash in retired_s3_mirrors:
        old_path=ROOT/old_mirror
        if old_path.exists():
            assert u.sha(old_path)==expected_hash, f'Unexpected pre-existing mirror content: {old_mirror}'
            old_path.unlink()
    display_audit=[]
    for strategy_id,label in STRATEGY_DISPLAY_NAMES.items():
        display_audit.append(dict(strategy_id=strategy_id,display_name=label,
            id_changed=False,sequence_changed=False,
            frozen_sequence_sha256=('435904b411b7c96a533548418ae9a0d8fa1cc46946d92799d2cc0eddc61d5b79'
                if strategy_id=='centrality-first' else ''),
            display_only_mapping=True))
    u.write_csv(review_dir/'STRATEGY_DISPLAY_NAME_AUDIT.csv',display_audit)
    legacy_display_occurrences_after={}
    for stem in STRATEGY_LABEL_FIGURES:
        with fitz.open(u.lp(DEST/(stem+'.pdf'))) as art:
            visible=' '.join(art[0].get_text().split())
        legacy_display_occurrences_after[stem]=visible.count('Centrality-first')
    assert not any(legacy_display_occurrences_after.values()),legacy_display_occurrences_after
    changes = []
    for row in manifest:
        name=row['final_name'];current_hash=row['sha256']
        baseline_sha=preservation_before[row['current_source_file']]
        changes.append(dict(figure=name,baseline_sha256=baseline_sha,current_sha256=current_hash,
                            unchanged=baseline_sha==current_hash))
    u.write_csv(DEST/'FIGURE_MANIFEST.csv', manifest)
    u.write_csv(ROOT/'results/figures/FIGURE_INDEX.csv', index)
    u.write_csv(review_dir/'FIGURE_CHANGE_MANIFEST.csv', changes)
    caps = captions()
    u.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md', '# Manuscript-facing figure captions\n\n'+
            '\n\n'.join('## '+title+'\n\n'+body for title,body in caps)+'\n')
    packets(caps,review_dir/'COMPACT_PACKET_PAGE_REGISTRY.csv')
    print('[build] captions and figure packets rebuilt',flush=True)
    font_names={}
    for stem in ACTIVE:
        with fitz.open(u.lp(DEST/(stem+'.pdf'))) as artwork:
            font_names[stem]=sorted({font[3] for font in artwork[0].get_fonts()})
    normalized_fonts={name.split('+')[-1].strip() for names in font_names.values() for name in names}
    assert normalized_fonts and all(name.lower().startswith('arial') for name in normalized_fonts),normalized_fonts
    with fitz.open(DEST/'ALL_FIGURES_WITH_CAPTIONS.pdf') as packet:
        assert len(packet)==16
        packet_fonts={font[3] for page in packet for font in page.get_fonts()}
    normalized_packet_fonts={name.split('+')[-1].strip() for name in packet_fonts}
    assert normalized_packet_fonts and all(name.lower().startswith('arial') for name in normalized_packet_fonts),normalized_packet_fonts
    style_checks['Typography']={'font_families':['Arial'],'embedded_font_names':font_names,
        'packet_embedded_font_names':sorted(packet_fonts),
        'all_active_artwork_uses_Arial':True,'all_packet_pages_use_Arial':True,
        'regular_and_bold_styles_allowed':True}
    u.dump(review_dir/'FIGURE_PRESENTATION_QA.json',dict(source_commit=CURRENT_SUITE_BASE,figures=style_checks,
        generator_sha256=u.sha(ROOT/GEN),no_simulation_or_new_statistical_estimates=True,
        no_stage7_data_or_config_writes=True))
    palette=json.loads(source('results/figure_review/CURRENT_CLUSTER_PALETTE.json',CURRENT_SUITE_BASE))
    palette.update(colors={str(k):v for k,v in figure7_final.PROPOSED.items()},
        cluster_palette_version='2026-10-16',map_version='2026-10-15',
        map_encoding='continuous SOVI blue-to-amber hue; five-policy service deficit lightness',
        map_regular_tract_outlines=False,NA_fill='#FFFFFF',NA_outline='#333333',NA_outline_width_pt=.45,
        screening_outline_width_pt=.25,map_same_fill_edge_overprint_pt=figure7_maps.SEAM_OVERLAP_PT,
        screening_rule='Frozen SOVI Q4 and five-policy deficit >= cohort P75',
        screening_tracts=94,screening_population=350799,formal_Stage7_pipeline_migrated=False,
        Figure7_layout='7.2 x 9.03 in; compact map-forward layout',Figure7_NA_fill='#FFFFFF')
    u.dump(DEST/'CURRENT_CLUSTER_PALETTE.json',palette)
    u.dump(DEST/'STRATEGY_DISPLAY_NAMES.json',dict(
        strategy_id_to_display_name=STRATEGY_DISPLAY_NAMES,
        strategy_ids_unchanged=True,
        centrality_first_sequence_sha256='435904b411b7c96a533548418ae9a0d8fa1cc46946d92799d2cc0eddc61d5b79'))
    gallery = ['<!doctype html><meta charset="utf-8"><title>Figures - 2026-10-19</title>',
        '<style>body{font:16px Arial;max-width:1000px;margin:24px auto}img{width:100%;height:auto}section{margin:32px 0}</style>',
        '<h1>Figures - 2026-10-19</h1><p>Seven-variable P2/K3 community types; Figure 7D maps continuous SOVI and five-policy recovery burden.</p>']
    for stem,(title,body) in zip(ACTIVE,caps):
        row=next(r for r in manifest if r['final_name']==stem+'.png')
        gallery += [f'<section><h2>{u.escape(title)}</h2><img src="{Path(row["mirror_file"]).name}" alt="{u.escape(title)}">',
                    f'<p>{u.escape(body)}</p></section>']
    u.write(ROOT/'results/figures/FIGURE_REVIEW_GALLERY.html', '\n'.join(gallery))
    explorer_hash=update_explorer_display_labels(ROOT/'results/figure_review/Additional_Evidence/METRIC_EXPLORER.html')
    info = ('# Figures - 2026-10-19\n\nSeven-variable P2 model, three primary classes, 2,299 positive-population tracts '
        '(1,235 / 428 / 636), 9,066,522 residents. NCV14 is supplementary environmental context, not a fitted coordinate. '
        'K4 remains a saved sensitivity result, not a second primary model.\n\n16 numbered figures: Main 1-7 and Supplement 1-9. '
        'The combined publication packet has 16 pages, one per numbered figure with its concise caption. '
        'Two unnumbered evidence candidates remain separate under results/figure_review/Additional_Evidence and are not in the publication packet. '
        'Figure S8 uses a muted blue-green population scale. Figure 7 uses a muted teal, slate and mauve K3 palette, cohort-standardized profiles, '
        'borderless tract fills, continuous blue-to-amber SOVI hue and five-policy burden lightness. Thin outlines show the Q4/cohort-P75 screen. '
        'Unnumbered map details and accessibility views are in results/diagnostics/1021/figure7_final_presentation_20261016/.\n\nReproduce: '
        '`python src/la_grid/plotting/build_current_figures.py --portable`. This replays the current figures.\n')
    for rel in ['results/figure_review/README.md','results/figures/README.md']:
        u.write(ROOT/rel, info)
    log = source('results/figure_review/UPDATE_LOG.md',CURRENT_SUITE_BASE).decode()
    u.write(DEST/'UPDATE_LOG.md', log+'\n\n## 2026-10-16 - Figure 7 palette, terminology and publication layout\n\n'
        'Figure 7A/B labels now use the seven registered publication-facing variable names; all six ECDFs and 21 standardized profile values are reconstructed from the verified P2/K3 tract table. '
        'The K3 palette is muted lake teal, slate blue and mauve. Figure 7C/D retain the same vector geography and map scale in a 7.2 x 9.03 in page; the D continuous blue-amber/luminance mapping is unchanged. '
        'Only Figure 7 changed among the 16 numbered artwork pairs. No feature values, memberships, SOVI groups, recovery results or simulations changed.\n'
        '\n## 2026-10-19 - Restoration strategy terminology and S3 recovery panels\n\n'
        'Spectral-connectivity-first is the display name for the unchanged centrality-first ID and station sequence. Supplementary Figure S3 shows the two time-dependent functional-network recovery analyses; static percolation remains in historical calculations but is omitted from the active figure. No scientific model or result changed.\n'
        '\n## 2026-10-21 - Figure S8 palette and publication packet\n\n'
        'Figure S8 population shading and its colorbar use a muted blue-green sequential palette; map geometry, station priorities and data are unchanged. The caption identifies the scale and points to active Supplementary Figure S9. Two unnumbered evidence candidates remain archived separately and are excluded from the 16-page numbered publication packet. Current figure text uses the Arial font family.\n')
    for rel in ['results/figure_review/README.md','results/figures/README.md']:
        existing=Path(ROOT/rel).read_text(encoding='utf-8')
        addition=('\nSupplementary Figure S3 shows only time-dependent functional-network recovery. '
                  'Spectral-connectivity-first is the publication display name for the unchanged centrality-first strategy ID.\n')
        if addition.strip() not in existing:
            u.write(ROOT/rel,existing.rstrip()+addition)
    u.dump(review_dir/'SOURCE_AUTHORITY_AND_HASHES.json', dict(source_commit=BASE,current_suite_source_commit=CURRENT_SUITE_BASE,
        actual_current_figure_baseline_commit=FIGURE_BASELINE_COMMIT,actual_current_figure_baseline_sha256=source_pdf_sha,
        map_experiment_source_commit=MAP_REVIEW_BASE,sources=SOURCES,adopted_specification=spec,
        no_stage7_or_simulation_changes=True,figure7_map_qa=style_checks['Main/Fig07']))
    outputs = ['results/figure_review/FIGURE_MANIFEST.csv',
        'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md', 'results/figure_review/CURRENT_CLUSTER_PALETTE.json',
        'results/figure_review/STRATEGY_DISPLAY_NAMES.json',
        'results/figure_review/ALL_MAIN_FIGURES.pdf', 'results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf',
        'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf', 'results/figures/FIGURE_INDEX.csv',
        'results/figures/FIGURE_REVIEW_GALLERY.html', 'results/figure_review/README.md',
        'results/figures/README.md', 'results/figure_review/UPDATE_LOG.md',
        'results/figure_review/Additional_Evidence/METRIC_EXPLORER.html']
    outputs += [r[field] for r in manifest for field in ['current_source_file','mirror_file']]
    outputs += ['results/figure_review/Page_Previews/'+Path(s).name+'.png' for s in ACTIVE]
    outputs += [str(p.relative_to(ROOT)) for p in diagnostic_dir.iterdir() if p.is_file()]
    preservation_after={rel:(u.sha(ROOT/rel) if (ROOT/rel).is_file() else None) for rel in preservation_before}
    preservation_rows=[]
    for rel,before_hash in preservation_before.items():
        after_hash=preservation_after[rel]
        expected_retired=rel.endswith(('FigS03_Network_Criticality_and_Percolation.pdf',
                                        'FigS03_Network_Criticality_and_Percolation.png'))
        preservation_rows.append(dict(path=rel,before_sha256=before_hash,after_sha256=after_hash,
            unchanged=before_hash==after_hash,
            authorized_S3_mirror_rename=expected_retired and after_hash is None))
    u.write_csv(review_dir/'FIGURE_ARTWORK_AND_SCIENCE_PRESERVATION.csv',preservation_rows)
    current_s3_sha=u.sha(DEST/'Supplement/FigS03.pdf')
    s3_manifest_rows=[r for r in manifest if r['final_name'].startswith('Supplement/FigS03.')]
    s3_mirror_rows=[r for r in index if r['figure_number']=='FigS03']
    with fitz.open(DEST/'ALL_FIGURES_WITH_CAPTIONS.pdf') as full_packet, \
         fitz.open(DEST/'ALL_MAIN_FIGURES.pdf') as main_packet, \
         fitz.open(DEST/'ALL_SUPPLEMENT_FIGURES.pdf') as supp_packet, \
         fitz.open(DEST/'Main/Fig07.pdf') as fig7:
        packet_info=dict(complete_packet_pages=len(full_packet),main_figure_pages=len(main_packet),
            supplementary_figure_pages=len(supp_packet),figure7_sha256=u.sha(DEST/'Main/Fig07.pdf'),
            figure7_matches_starting_hash=preservation_before['results/figure_review/Main/Fig07.pdf']==u.sha(DEST/'Main/Fig07.pdf'))
    qa_s3=dict(source_commit=CURRENT_SUITE_BASE,source_pdf_sha256=s3_source_hash,
        source_png_sha256=u.digest(original_s3_png),revised_pdf_sha256=current_s3_sha,
        revised_png_sha256=u.sha(DEST/'Supplement/FigS03.png'),comparison_pdf_sha256=u.sha(review_dir/'S03_ORIGINAL_VS_REVISED.pdf'),
        layout=s3_layout,active_caption=caps[9],manifest_rows=s3_manifest_rows,index_rows=s3_mirror_rows,
        explorer_sha256=explorer_hash,legacy_strategy_display_occurrences_before=legacy_display_occurrences_before,
        legacy_strategy_display_occurrences_after=legacy_display_occurrences_after,
        packet=packet_info,static_analysis_code_or_results_modified=False,
        strategy_id='centrality-first',strategy_display_name='Spectral-connectivity-first',
        frozen_sequence_sha256='435904b411b7c96a533548418ae9a0d8fa1cc46946d92799d2cc0eddc61d5b79',
        frozen_strategy_registry_sha256=u.sha(ROOT/'FINAL_REVISION_RUN_SEQUENCE/03_GA_AND_STRATEGY_FREEZE/FINAL_STRATEGY_SET.json'),
        strategy_id_and_registered_sequence_digest_unchanged=True,
        raw_sequence_payload_available=(ROOT/'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').is_file(),
        raw_sequence_payload_independently_replayed=False)
    u.dump(review_dir/'S03_SOURCE_AND_REBUILD_QA.json',qa_s3)
    science_rows=[r for r in preservation_rows if r['path'] in preserve_science]
    unrelated_artwork_rows=[r for r in preservation_rows if r['path'] in preserve_artwork and
        'Main/Fig01' not in r['path'] and 'Fig01_Methodology_Workflow' not in r['path'] and
        'Page_Previews/Fig01' not in r['path'] and
        'Supplement/FigS03' not in r['path'] and 'Supplement/FigS08' not in r['path'] and
        'FigS03_Network_Criticality_and_Percolation' not in r['path'] and
        'FigS08_Priority_Construction' not in r['path']]
    assert all(r['unchanged'] for r in science_rows)
    assert all(r['unchanged'] for r in unrelated_artwork_rows)
    u.dump(review_dir/'PRESERVATION_AFTER.json',dict(preservation=preservation_rows,
        all_registered_science_sources_unchanged=all(r['unchanged'] for r in science_rows),
        all_unrelated_numbered_artwork_unchanged=all(r['unchanged'] for r in unrelated_artwork_rows),
        figure1_restoration_panel_updated=True,
        figure1_other_panels_unchanged=True,
        figure7_unchanged=packet_info['figure7_matches_starting_hash'],
        S08_population_art_and_caption_updated=True,
        unnumbered_evidence_candidates_retained_as_separate_files=True))
    outputs += [str(p.relative_to(ROOT)) for p in review_dir.iterdir()
                if p.is_file() and p.name not in {
                    'BUILD_CHECKPOINT.json','DETERMINISTIC_REBUILD.json','TEST_RESULTS.json',
                    'FIGURE_PUBLICATION_SIZE_VISUAL_QA.md','FINAL_DELIVERY_REPORT.md'}]
    outputs += [str(review_dir/'METHODS_REFERENCE.md')]
    hashes = {rel:u.sha(ROOT/rel) for rel in dict.fromkeys(outputs)}
    prior = previous
    idempotence_verified=False
    if prior.exists():
        old=json.loads(prior.read_text(encoding='utf-8'))
        if (old['generator_sha256']==u.sha(ROOT/GEN)
                and old.get('presentation_sha256')==u.sha(ROOT/PRESENTATION)
                and old.get('figure7_presentation_sha256')==u.sha(ROOT/'src/la_grid/plotting/figure7_final_presentation_20261016.py')):
            if old['output_hashes']!=hashes:
                keys=set(old['output_hashes'])|set(hashes)
                differences={key:(old['output_hashes'].get(key),hashes.get(key))
                             for key in sorted(keys)
                             if old['output_hashes'].get(key)!=hashes.get(key)}
                raise AssertionError(f'Non-idempotent current-suite replay: {differences}')
            idempotence_verified=True
    u.dump(prior, dict(generator_sha256=u.sha(ROOT/GEN), presentation_sha256=u.sha(ROOT/PRESENTATION),
        figure7_presentation_sha256=u.sha(ROOT/'src/la_grid/plotting/figure7_final_presentation_20261016.py'),
        routing_sha256=u.sha(ROOT/'src/la_grid/plotting/build_current_figures.py'), output_hashes=hashes, model='P2',
        numbered_figures=16, packet_pages=16, primary_K=3, fitted_feature_count=7,
        figure7_layout='C',current_source_commit=CURRENT_SUITE_BASE,figure_baseline_commit=FIGURE_BASELINE_COMMIT))
    u.dump(review_dir/'DETERMINISTIC_REBUILD.json',dict(
        canonical_command='python src/la_grid/plotting/build_current_figures.py --portable',
        build_checkpoint_sha256=u.sha(prior),output_hashes=hashes,
        second_run_hashes_match=idempotence_verified,second_run_pending=not idempotence_verified,
        figure7_sha256=packet_info['figure7_sha256'],
        figure_s3_sha256=current_s3_sha,packet_pages=packet_info['complete_packet_pages']))
    print('Current suite synchronized: 16 numbered figures, 16 packet pages; S3 and S8 presentation updates; no fits or simulations.')


if __name__ == '__main__':
    main()
