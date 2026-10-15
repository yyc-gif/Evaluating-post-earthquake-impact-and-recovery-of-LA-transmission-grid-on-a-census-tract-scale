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

ROOT = u.ROOT
BASE = '937fa2b1ab9953d8411a08fbbd0400cf3b52bd8f'
PB = 'docs/data_research/stage7_path_b_p2_integration_review_20261014/'
REVIEW = 'local_elsevier_review_outputs/'
CAPTION_COMMIT = 'aecc9adadd04edc4c5f64de64f79ed4c34c1f69c'
AUTH = ROOT / 'results/stage7/2026-10-14'
DEST = ROOT / 'results/figure_review'
QA = ROOT / 'docs/reproducibility/p2_final_adoption_20261014'
GEN = 'src/la_grid/plotting/build_current_suite_p2.py'
PRESENTATION = 'src/la_grid/plotting/figure_presentation.py'
STYLE_QA = ROOT/'docs/reproducibility/figure_presentation_20261014'
FEATURES = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained',
            'MeanDelta', 'SOVI_SCORE', 'log1p_Population']
BUDGETS = np.array([1/9, 1/9, 1/9, 1/6, 1/6, 1/6, 1/6])
COLORS = ['#147f98', '#d07734', '#7a5899']
ACTIVE = [f'Main/Fig{i:02d}' for i in range(1, 8)] + [f'Supplement/FigS{i:02d}' for i in range(1, 11)]
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
    selected = f[keep].copy()
    selected['K3_class'] = saved[3]+1
    csv(AUTH/'tract_features.csv', selected)
    csv(AUTH/'clusters_labels_final.csv', selected[['tract_id', 'K3_class', 'Population', 'frozen_SOVI_quartile']])
    csv(AUTH/'standardizer_and_weights.csv', weights)
    csv(AUTH/'K4_sensitivity_membership.csv', pd.DataFrame(dict(tract_id=ids, K4_sensitivity_class=saved[4]+1)))
    status = full[['tract_id', 'Population', 'frozen_SOVI_quartile',
                   'additional_zero_housing_positive_population']].copy()
    status['clustering_eligible'] = status.Population.gt(0)
    status['K3_class'] = full.P2_K3_class
    csv(AUTH/'stage7_full_domain_tract_status.csv', status)
    registry = pd.DataFrame(dict(class_id=['C1', 'C2', 'C3'], K3_class=[1, 2, 3], color=COLORS,
        tract_count=f.groupby('P2_K3_class').size().tolist(),
        frozen_population=f.groupby('P2_K3_class').Population.sum().astype(int).tolist()))
    csv(AUTH/'class_id_registry.csv', registry)
    for src, dst in [('CLUSTER_ORIGINAL_UNIT_PROFILES.csv', 'cluster_profiles_original_units.csv'),
        ('P2_ORDINARY_COHORT_Z_CLASS_MEANS.csv', 'ordinary_cohort_z_class_means.csv'),
        ('P2_REGISTERED_K_EVIDENCE.csv', 'saved_K_evidence.csv'),
        ('P2_SEED_STABILITY.csv', 'seed_stability.csv'),
        ('P2_SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv', 'geographic_stability.csv'),
        ('P2_POLICY_SET_CLUSTER_STABILITY.csv', 'policy_set_stability.csv')]:
        u.write(AUTH/dst, source(PB+src))
    csv(AUTH/'five_policy_total_deficit.csv', selected[['tract_id', 'B_Unconstrained', 'MeanDelta', 'MeanTotal5',
                                                       'frozen_SOVI_quartile', 'Population']])
    u.write(AUTH/'study_domain_geometry.gpkg', source(PB+'inputs/FULL_2315_GEOMETRY.gpkg'))
    buffer = io.BytesIO()
    np.savez_compressed(buffer, tract_ids=ids, feature_names=np.array(FEATURES), raw=raw, weighted_matrix=weighted,
                        budgets=BUDGETS, K3_labels=saved[3], K4_sensitivity_labels=saved[4])
    u.write(AUTH/'preprocessing_and_labels.npz', buffer.getvalue())
    spec = dict(schema_version=1, status='AUTHOR_ADOPTED_P2_SEVEN_VARIABLE', primary_K=3,
        sensitivity_K=4, feature_names=FEATURES, squared_distance_budgets=BUDGETS.tolist(),
        standardization='Frozen eligible-cohort mean and population SD (ddof=0); sqrt budgets applied for distance',
        cohort_rule='Frozen formal Population > 0', eligible_tracts=2299, full_domain_tracts=2315,
        represented_population=9066522, excluded_zero_population=16, included_zero_housing=8,
        class_counts=[1235, 428, 636], class_populations=[5184036, 1695501, 2186985],
        hazard='2pc50', resources='C57_D1', mapping='M1_UTILITY_003', gate='G1_BASELINE_050',
        horizon_hr=480, realizations=1000, policies=policies,
        MeanDelta='Equal descriptive mean of matched constrained-minus-Unconstrained deficit over five policies',
        environmental_hazard_context='NCV14 supplementary only; not a fitted feature or comprehensive risk index',
        source_commit=BASE, original_saved_fit_commit='81c3452e29abc109f50564d39035c06225e3ea84',
        no_refitting_or_scientific_generation=True)
    u.dump(AUTH/'feature_schema_and_identity.json', spec)
    files = {p.name: u.sha(p)
             for p in Path(u.lp(AUTH)).iterdir() if p.is_file() and p.name != 'ARTIFACT_HASHES.json'}
    u.dump(AUTH/'ARTIFACT_HASHES.json', files)
    u.dump(ROOT/'config/current_stage7.json', dict(version='2026-10-14',
        authority='results/stage7/2026-10-14', primary_K=3, fitted_feature_count=7,
        schema_sha256=u.sha(AUTH/'feature_schema_and_identity.json'), source_commit=BASE))
    return spec


def captions():
    text = source('results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md', CAPTION_COMMIT).decode('utf-8')
    items = [(title.strip(), body.strip()) for title, body in
             re.findall(r'^## (.+?)\n\n(.*?)(?=^## |\Z)', text, re.M | re.S)]
    items=[(title,body.replace('frozen SOVI quartiles','SOVI quartiles')
            .replace('frozen scheduling inputs','pre-event scheduling inputs')
            .replace('Saved damage-,','Damage-,')) for title,body in items]
    items[6]=('Figure 7. Community recovery types and social vulnerability',
        '(A) Six empirical feature distributions; markers locate class medians on the 50% guide. '
        '(B) Cohort-standardized means of all seven clustering variables; zero is the cohort mean. '
        '(C) Community types. (D) Five-policy mean total equivalent service-deficit hours and SOVI quartiles, '
        'using common burden-to-lightness scaling. Outlines mark Q4 tracts at or above the cohort P75 deficit. '
        'This is descriptive co-occurrence, not a composite risk score, statistically significant hotspot, '
        'or repair-priority ranking. White outlined tracts are N/A (16 zero-population tracts).')
    items=[(title,body.replace('frozen ','').replace('Saved ','').replace('saved ','')) for title,body in items]
    items=[(title,re.sub(r'\bfrozen\s+','',body,flags=re.I).replace('for P2.','for the community typology.'))
           for title,body in items]
    assert len(items) == 17
    assert [int(x) for x in re.findall(r'^Supplementary Figure S(\d+)\.', '\n'.join(t for t,b in items), re.M)] == list(range(1,11))
    return items


def packets(caps):
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
            preview = 'results/figure_review/Page_Previews/'+Path(stem).name+'.png'
            u.write(ROOT/preview, art[0].get_pixmap(dpi=150).tobytes('png')
                    if stem in ['Main/Fig05','Main/Fig07','Supplement/FigS08'] else source(preview))
    with fitz.open(stream=source('results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'), filetype='pdf') as baseline:
        assert len(baseline)==21
        book.insert_pdf(baseline, from_page=17, to_page=20)
    for name, doc in [('ALL_FIGURES_WITH_CAPTIONS.pdf', book), ('ALL_MAIN_FIGURES.pdf', main),
                      ('ALL_SUPPLEMENT_FIGURES.pdf', supp)]:
        u.write(DEST/name, doc.tobytes(garbage=4, deflate=True, no_new_id=True))
        doc.close()
    u.write_csv(QA/'COMPACT_PACKET_PAGE_REGISTRY.csv', registry)


def main():
    spec = adopt_authority()
    previous=QA/'BUILD_CHECKPOINT.json'
    old_outputs=json.loads(previous.read_text(encoding='utf-8'))['output_hashes'] if previous.exists() else {}
    manifest = u.csv_rows(source('results/figure_review/FIGURE_MANIFEST.csv'))
    index = u.csv_rows(source('results/figures/FIGURE_INDEX.csv'))
    replacements = {'Main/Fig07': 'FIG07_P2_K3_B_COLOR_NO_REVIEW_BANNER',
                    'Supplement/FigS08': 'FigS08_P2_K3_K4_Saved_Diagnostics'}
    style={};style_checks={}
    for stem in ['Main/Fig05','Main/Fig07','Supplement/FigS08']:
        rel=REVIEW+replacements[stem]+'.pdf' if stem in replacements else 'results/figure_review/'+stem+'.pdf'
        style[stem],style_checks[stem]=figure_presentation.apply(stem,source(rel))
    u.dump(STYLE_QA/'PRESENTATION_QA.json',dict(source_commit=BASE,figures=style_checks,
        generator_sha256=u.sha(ROOT/PRESENTATION),no_scientific_calculations=True))
    changes = []
    for row in manifest:
        stem, ext = row['final_name'].rsplit('.', 1)
        path = REVIEW+replacements[stem]+'.'+ext if stem in replacements else row['current_source_file']
        raw = source(path)
        source_hash=u.digest(raw)
        if stem in style:
            if ext=='pdf':raw=style[stem]
            else:
                png=row['current_source_file'];pdf=png.removesuffix('.png')+'.pdf'
                if (ROOT/png).is_file() and old_outputs.get(pdf)==u.digest(style[stem]) and old_outputs.get(png)==u.sha(ROOT/png):
                    raw=(ROOT/png).read_bytes()
                else:
                    with fitz.open(stream=style[stem],filetype='pdf') as art:
                        raw=art[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
        u.write(ROOT/row['current_source_file'], raw)
        u.write(ROOT/row['mirror_file'], raw)
        before = row['sha256']
        row.update(sha256=u.digest(raw), change_in_this_update='UPDATED' if stem in style else 'RETAINED')
        if stem in style:
            with fitz.open(stream=style[stem],filetype='pdf') as art:
                size=f'{art[0].rect.width*25.4/72:.3f} x {art[0].rect.height*25.4/72:.3f}'
            row.update(source_commit=BASE, source_file=path, presentation_generator=GEN,
                       presentation_generator_sha256=u.sha(ROOT/GEN), status='AUTHOR_ADOPTED_P2_CURRENT',
                       min_font_pt='7.500', size_mm=size,
                       parent_sha256=before, parent_source_commit=BASE, parent_source_file=row['current_source_file'])
        else:
            assert u.digest(raw)==before
        ix=next(r for r in index if r['source_path']==row['current_source_file'])
        ix['sha256_or_lfs_oid']=u.digest(raw)
        ix['current_status']='CURRENT_ADOPTED_P2_SUITE'
        ix['submission_status']='Current author-approved seven-variable suite'
        if stem in style:
            ix.update(source_authority=BASE, source_data_path=path, source_data_sha256=source_hash, generator=GEN,
                notes='Presentation-only spacing and wording corrections; scientific vectors and values retained.')
        changes.append(dict(figure=row['final_name'], baseline_sha256=before, current_sha256=u.digest(raw),
                            unchanged=before==u.digest(raw)))
    assert sum(not r['unchanged'] for r in changes)==6
    u.write_csv(DEST/'FIGURE_MANIFEST.csv', manifest)
    u.write_csv(ROOT/'results/figures/FIGURE_INDEX.csv', index)
    u.write_csv(QA/'FIGURE_CHANGE_MANIFEST.csv', changes)
    caps = captions()
    u.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md', '# Manuscript-facing figure captions\n\n'+
            '\n\n'.join('## '+title+'\n\n'+body for title,body in caps)+'\n')
    packets(caps)
    u.dump(DEST/'CURRENT_CLUSTER_PALETTE.json', dict(figure_cluster_count=3, adopted_K=3,
        model_version='2026-10-14', colors={str(i+1):c for i,c in enumerate(COLORS)}, class_labels=['C1','C2','C3'],
        NA_fill='#FFFFFF', NA_outline='#777777', NA_outline_width_pt=.45, NA_count=16,
        membership_commit=BASE, membership_source=PB+'P2_FROZEN_MEMBERSHIPS.csv',
        formal_Stage7_pipeline_migrated=True, primary_authority='results/stage7/2026-10-14'))
    gallery = ['<!doctype html><meta charset="utf-8"><title>Figures - 2026-10-14</title>',
        '<style>body{font:16px Arial;max-width:1000px;margin:24px auto}img{width:100%;height:auto}section{margin:32px 0}</style>',
        '<h1>Figures - 2026-10-14</h1><p>Three-class community typology; environmental-hazard analysis is supplementary context only.</p>']
    for stem,(title,body) in zip(ACTIVE,caps):
        row=next(r for r in manifest if r['final_name']==stem+'.png')
        gallery += [f'<section><h2>{u.escape(title)}</h2><img src="{Path(row["mirror_file"]).name}" alt="{u.escape(title)}">',
                    f'<p>{u.escape(body)}</p></section>']
    u.write(ROOT/'results/figures/FIGURE_REVIEW_GALLERY.html', '\n'.join(gallery))
    info = ('# Figures - 2026-10-14\n\nSeven-variable model, three primary classes, 2,299 positive-population tracts '
        '(1,235 / 428 / 636), 9,066,522 residents. NCV14 is supplementary environmental context, not a fitted coordinate. '
        'K4 remains a sensitivity result, not a second primary model.\n\n17 numbered figures: Main 1-7 and Supplement 1-10. '
        'The compact combined packet has 21 pages: 17 native artwork-plus-concise-caption pages and four retained '
        'complementary-evidence pages. Figure 7 uses the approved color-family/continuous-burden map and direct Q4/P75 '
        'co-occurrence outlines; no composite hotspot score. The separate grayscale accessibility maps remain available '
        'under docs/figure_sources/2026-10-14/.\n\nReproduce: '
        '`python src/la_grid/plotting/build_current_figures.py --portable`. This replays the current figures. '
        'Historical implementations are recoverable from Git history, not competing current builders. '
        'No physical simulation or K-means is run. Current identity: results/stage7/2026-10-14/.\n')
    for rel in ['results/figure_review/README.md','results/figures/README.md']:
        u.write(ROOT/rel, info)
    log = source('results/figure_review/UPDATE_LOG.md').decode()
    u.write(DEST/'UPDATE_LOG.md', log+'\n\n## 2026-10-14 - current version\n\n'
        'Replaced Fig07 and FigS08 from the frozen P2 source; all other 15 numbered PDF/PNG pairs remain byte-identical. '
        'Updated concise captions, palettes, indexes, gallery, mirrors, previews and native packets. '
        'Saved K3 is primary; K4 is sensitivity and its stronger geographic agreement is disclosed. '
        'Full service domain remains 2,315; no physical outputs or manuscript documents changed. '
        'The branch and current data directory use the date 2026-10-14; superseded presentation drafts '
        'and per-run search archives are retained in Git history rather than the current tree.\n\n'
        'Figure 5 now uses balanced row-title spacing. Figure 7 uses concise titles and no embedded explanatory '
        'footnotes; its original graphs and maps are translated without scaling. Supplement S8 removes '
        'process-only labels. All other 14 artwork pairs retain their approved bytes.\n')
    u.dump(QA/'SOURCE_AUTHORITY_AND_HASHES.json', dict(source_commit=BASE, sources=SOURCES,
        adopted_specification=spec, author_authorization_date='2026-10-14'))
    outputs = [str(p.relative_to(ROOT)).replace('\\','/') for p in AUTH.iterdir() if p.is_file()]
    outputs += ['config/current_stage7.json', 'results/figure_review/FIGURE_MANIFEST.csv',
        'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md', 'results/figure_review/CURRENT_CLUSTER_PALETTE.json',
        'results/figure_review/ALL_MAIN_FIGURES.pdf', 'results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf',
        'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf', 'results/figures/FIGURE_INDEX.csv',
        'results/figures/FIGURE_REVIEW_GALLERY.html', 'results/figure_review/README.md',
        'results/figures/README.md', 'results/figure_review/UPDATE_LOG.md']
    outputs += [r[field] for r in manifest for field in ['current_source_file','mirror_file']]
    outputs += ['results/figure_review/Page_Previews/'+Path(s).name+'.png' for s in ACTIVE]
    hashes = {rel:u.sha(ROOT/rel) for rel in outputs}
    prior = QA/'BUILD_CHECKPOINT.json'
    if prior.exists():
        old=json.load(open(u.lp(prior),encoding='utf-8'))
        if old['generator_sha256']==u.sha(ROOT/GEN) and old.get('presentation_sha256')==u.sha(ROOT/PRESENTATION):
            assert old['output_hashes']==hashes, 'Non-idempotent current-suite replay'
    u.dump(prior, dict(generator_sha256=u.sha(ROOT/GEN), presentation_sha256=u.sha(ROOT/PRESENTATION), routing_sha256=u.sha(ROOT/'src/la_grid/plotting/build_current_figures.py'), output_hashes=hashes, model='P2',
        numbered_figures=17, packet_pages=21, primary_K=3, fitted_feature_count=7))
    print('Adopted P2 authority and complete figure suite synchronized: 17 figures, 21 pages; no fits.')


if __name__ == '__main__':
    main()
