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

ROOT = u.ROOT
BASE = '937fa2b1ab9953d8411a08fbbd0400cf3b52bd8f'
CURRENT_SUITE_BASE = '0f67aa1f2758fcf1d35c112c36eb04e6d8a5dd68'
MAP_REVIEW_BASE = '0134bfc5b27a8c518078873e21c6151675523b68'
PB = 'docs/data_research/stage7_path_b_p2_integration_review_20261014/'
AUTH = ROOT / 'results/stage7/2026-10-14'
DEST = ROOT / 'results/figure_review'
QA = ROOT / 'docs/reproducibility/figure7_map_readability_20261015'
GEN = 'src/la_grid/plotting/build_current_suite_p2.py'
PRESENTATION = 'src/la_grid/plotting/figure_presentation.py'
FEATURES = ['Init_Supply', 'Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained',
            'MeanDelta', 'SOVI_SCORE', 'log1p_Population']
BUDGETS = np.array([1/9, 1/9, 1/9, 1/6, 1/6, 1/6, 1/6])
COLORS = ['#147f98', '#d07734', '#7a5899']
ACTIVE = [f'Main/Fig{i:02d}' for i in range(1, 8)] + [f'Supplement/FigS{i:02d}' for i in range(1, 10)]
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
    title, _ = items[6]
    items[6]=(title,
        '(A) Six empirical feature distributions by class; dots mark medians. '
        '(B) Profiles show standardized means for all seven fitted variables. '
        '(C) Tract classes. (D) Five-policy recovery burden (lightness) and continuous SOVI score '
        '(blue-to-amber hue). Outlines identify Q4 tracts at or above the 75th-percentile burden; this is a descriptive screen, '
        'not a composite score or inferential hotspot test. White outlined tracts are N/A.')
    assert len(items) == 16
    assert [int(x) for x in re.findall(r'^Supplementary Figure S(\d+)\.', '\n'.join(t for t,b in items), re.M)] == list(range(1,10))
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
            if stem == 'Main/Fig07':
                preview = 'results/figure_review/Page_Previews/Fig07.png'
                u.write(ROOT/preview, art[0].get_pixmap(dpi=150).tobytes('png'))
            else:
                preview = 'results/figure_review/Page_Previews/'+Path(stem).name+'.png'
                u.write(ROOT/preview, source(preview,CURRENT_SUITE_BASE))
    with fitz.open(stream=source('results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf', CURRENT_SUITE_BASE), filetype='pdf') as baseline:
        assert len(baseline)==20
        book.insert_pdf(baseline, from_page=16, to_page=19)
    for name, doc in [('ALL_FIGURES_WITH_CAPTIONS.pdf', book), ('ALL_MAIN_FIGURES.pdf', main),
                      ('ALL_SUPPLEMENT_FIGURES.pdf', supp)]:
        u.write(DEST/name, doc.tobytes(garbage=4, deflate=True, no_new_id=True))
        doc.close()
    u.write_csv(QA/'COMPACT_PACKET_PAGE_REGISTRY.csv', registry)


def main():
    spec = adopt_authority()
    previous=QA/'BUILD_CHECKPOINT.json'
    original_manifest = u.csv_rows(source('results/figure_review/FIGURE_MANIFEST.csv',CURRENT_SUITE_BASE))
    original_index = u.csv_rows(source('results/figures/FIGURE_INDEX.csv',CURRENT_SUITE_BASE))
    manifest=[];index=[]
    changed={};style_checks={}
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
    source_pdf = source('results/figure_review/Main/Fig07.pdf', CURRENT_SUITE_BASE)
    candidate_a = figure7_maps.build_full_figure(source_pdf, table, paths, display,
                                                  specification, layout='A', outline_width=0.25)
    candidate_b = figure7_maps.build_full_figure(source_pdf, table, paths, display,
                                                  specification, layout='B', outline_width=0.25)
    diagnostic_dir = ROOT/'results/diagnostics/1021/figure7_readability_20261015'
    figure7_maps.write_pdf(diagnostic_dir/'FIG07_LAYOUT_A_BORDERLESS.pdf', candidate_a)
    figure7_maps.write_pdf(diagnostic_dir/'FIG07_LAYOUT_B_ENLARGED.pdf', candidate_b)
    figure7_maps.export_png(diagnostic_dir/'FIG07_LAYOUT_A_BORDERLESS.pdf', diagnostic_dir/'FIG07_LAYOUT_A_BORDERLESS.png')
    figure7_maps.export_png(diagnostic_dir/'FIG07_LAYOUT_B_ENLARGED.pdf', diagnostic_dir/'FIG07_LAYOUT_B_ENLARGED.png')
    details = figure7_maps.build_details(table, paths, display, specification, diagnostic_dir,
                                         outline_width=0.25)
    figure7_maps.write_pdf(diagnostic_dir/'FIG07_MAP_DETAILS_C_D.pdf', details)
    for n, page in enumerate(details, start=1):
        page.get_pixmap(dpi=600, alpha=False).save(str(diagnostic_dir/f'FIG07_MAP_DETAILS_PAGE_{n}.png'))
    accessibility = figure7_maps.build_accessibility_reference(table, paths, specification,
                                                               outline_width=0.25)
    figure7_maps.write_pdf(diagnostic_dir/'FIG07_ACCESSIBILITY_ALIGNED_SEPARATE_MAPS.pdf', accessibility)
    accessibility[0].get_pixmap(dpi=600, alpha=False).save(str(diagnostic_dir/'FIG07_ACCESSIBILITY_ALIGNED_SEPARATE_MAPS.png'))
    width_comparison=figure7_maps.build_outline_comparison(table,paths,display,specification)
    figure7_maps.write_pdf(diagnostic_dir/'FIG07_SCREENING_OUTLINE_WIDTH_COMPARISON.pdf',width_comparison)
    for n, page in enumerate(width_comparison, start=1):
        page.get_pixmap(dpi=300, alpha=False).save(str(diagnostic_dir/f'FIG07_OUTLINE_WIDTH_{n}_300DPI.png'))
    # Three native-width pages compare the unmodified reference, borderless layout A, and enlarged layout B.
    layout_comparison=fitz.open()
    with fitz.open(stream=source_pdf,filetype='pdf') as original:
        layout_comparison.insert_pdf(original)
    layout_comparison.insert_pdf(candidate_a)
    layout_comparison.insert_pdf(candidate_b)
    layout_comparison.set_toc([[1,'Starting Figure 7 with ordinary strokes',1],
                               [1,'Layout A: borderless maps, original footprint',2],
                               [1,'Layout B: borderless maps, enlarged C/D',3]])
    figure7_maps.write_pdf(diagnostic_dir/'FIG07_BOUNDARY_AND_LAYOUT_COMPARISON.pdf',layout_comparison)
    from PIL import Image, ImageDraw, ImageOps
    thumbs=[]
    with fitz.open(diagnostic_dir/'FIG07_BOUNDARY_AND_LAYOUT_COMPARISON.pdf') as comparison:
        for page in comparison:
            pix=page.get_pixmap(dpi=150,alpha=False)
            thumbs.append(Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB'))
    header=34; gap=18
    sheet=Image.new('RGB',(sum(im.width for im in thumbs)+gap*(len(thumbs)-1),
                           max(im.height for im in thumbs)+header),'white')
    draw=ImageDraw.Draw(sheet)
    labels=['Starting map strokes','A: borderless, original map size','B: enlarged C/D']
    x=0
    for label,im in zip(labels,thumbs):
        draw.text((x+8,8),label,fill='#222222')
        sheet.paste(im,(x,header));x+=im.width+gap
    sheet.save(u.lp(diagnostic_dir/'FIG07_BOUNDARY_AND_LAYOUT_COMPARISON.png'))
    figure7_maps.export_png(diagnostic_dir/'FIG07_LAYOUT_B_ENLARGED.pdf',
                            diagnostic_dir/'FIG07_LAYOUT_B_GRAYSCALE_SOURCE.png',dpi=150)
    gray_path=diagnostic_dir/'FIG07_LAYOUT_B_GRAYSCALE_SOURCE.png'
    with Image.open(u.lp(gray_path)) as source_image:
        ImageOps.grayscale(source_image).save(u.lp(diagnostic_dir/'FIG07_LAYOUT_B_GRAYSCALE.png'))
    gray_path.unlink()
    source_pdf_sha=u.digest(source_pdf)
    assert source_pdf_sha=='16407d2060dfce8cb791deda60dd77ae6fcae34ab89b2212e4b858474b10bc3d'
    changed['Main/Fig07']=candidate_b.tobytes(garbage=4,deflate=True,no_new_id=True)
    style_checks['Main/Fig07']={
        'source_commit':CURRENT_SUITE_BASE,'source_pdf_sha256':source_pdf_sha,
        'approved_map_source_commit':MAP_REVIEW_BASE,
        'positive_polygon_parts':len(paths['positive']),'positive_GEOIDs':len(table),
        'NA_polygon_count':len(paths['NA']),'high_high_outline_count':len(paths['high_high']),
        'high_high_population':int(table.set_index('tract_id').Population.loc[
            list(expected_geoids['high_high'])].sum()),
        'high_high_threshold_hr':38.38135467381475,'chosen_outline_width_pt':0.25,
        'contrasting_internal_tract_boundaries':False,
        'same_fill_edge_overprint_pt':figure7_maps.SEAM_OVERLAP_PT,
        'A_and_B_top_panels_preserved_from_source':True,
        'layout_A_size_in':[7.2,9.0],'layout_B_size_in':[7.2,10.0],
        'layout_B_map_scale':1.25,'all_map_geometry_vector':True}
    for stem in ACTIVE:
        original_path='results/figure_review/'+stem+'.pdf'
        original=source(original_path,CURRENT_SUITE_BASE)
        raw=changed.get(stem,original)
        for ext in ['pdf','png']:
            row=next(r.copy() for r in original_manifest if r['final_name']==stem+'.'+ext)
            ix=next(r.copy() for r in original_index if r['source_path']==row['current_source_file'])
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
            before=row['sha256'];current_hash=u.digest(raw)
            row.update(sha256=current_hash,change_in_this_update='UPDATED' if stem in changed else 'RETAINED')
            if stem in changed:
                with fitz.open(stream=raw,filetype='pdf') as art:
                    size=f'{art[0].rect.width*25.4/72:.3f} x {art[0].rect.height*25.4/72:.3f}'
                row.update(source_commit=CURRENT_SUITE_BASE,source_file=original_path,
                    presentation_generator=GEN,presentation_generator_sha256=u.sha(ROOT/GEN),
                    status='AUTHOR_REVIEW_1021_FIGURE7_MAP_UPDATE',min_font_pt='7.500',size_mm=size,
                    parent_sha256=before,parent_source_commit=CURRENT_SUITE_BASE,parent_source_file=original_path)
                ix.update(source_authority=CURRENT_SUITE_BASE,source_data_path=original_path,
                    source_data_sha256=source_pdf_sha,generator=GEN,
                    notes='Figure 7 map presentation only: no tract values or K3 assignments changed.')
            ix['sha256_or_lfs_oid']=current_hash
            ix['current_status']='CURRENT_1021_P2_K3_SUITE'
            manifest.append(row);index.append(ix)
    u.dump(QA/'PRESENTATION_QA.json',dict(source_commit=CURRENT_SUITE_BASE,figures=style_checks,
        generator_sha256=u.sha(ROOT/GEN),no_simulation_or_new_statistical_estimates=True,
        no_stage7_data_or_config_writes=True))
    changes = []
    original_hash={r['final_name']:r['sha256'] for r in original_manifest}
    for row in manifest:
        name=row['final_name'];current_hash=row['sha256']
        changes.append(dict(figure=name,baseline_sha256=original_hash[name],current_sha256=current_hash,
                            unchanged=original_hash[name]==current_hash))
    u.write_csv(DEST/'FIGURE_MANIFEST.csv', manifest)
    u.write_csv(ROOT/'results/figures/FIGURE_INDEX.csv', index)
    u.write_csv(QA/'FIGURE_CHANGE_MANIFEST.csv', changes)
    caps = captions()
    u.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md', '# Manuscript-facing figure captions\n\n'+
            '\n\n'.join('## '+title+'\n\n'+body for title,body in caps)+'\n')
    packets(caps)
    palette=json.loads(source('results/figure_review/CURRENT_CLUSTER_PALETTE.json',CURRENT_SUITE_BASE))
    palette.update(map_version='2026-10-15',map_encoding='continuous SOVI blue-to-amber hue; five-policy service deficit lightness',
        map_regular_tract_outlines=False,NA_fill='#FFFFFF',NA_outline='#333333',NA_outline_width_pt=.45,
        screening_outline_width_pt=.25,map_same_fill_edge_overprint_pt=figure7_maps.SEAM_OVERLAP_PT,
        screening_rule='Frozen SOVI Q4 and five-policy deficit >= cohort P75',
        screening_tracts=94,screening_population=350799,formal_Stage7_pipeline_migrated=False)
    u.dump(DEST/'CURRENT_CLUSTER_PALETTE.json',palette)
    gallery = ['<!doctype html><meta charset="utf-8"><title>Figures - 2026-10-15</title>',
        '<style>body{font:16px Arial;max-width:1000px;margin:24px auto}img{width:100%;height:auto}section{margin:32px 0}</style>',
        '<h1>Figures - 2026-10-15</h1><p>Seven-variable P2/K3 community types; Figure 7D maps continuous SOVI and five-policy recovery burden.</p>']
    for stem,(title,body) in zip(ACTIVE,caps):
        row=next(r for r in manifest if r['final_name']==stem+'.png')
        gallery += [f'<section><h2>{u.escape(title)}</h2><img src="{Path(row["mirror_file"]).name}" alt="{u.escape(title)}">',
                    f'<p>{u.escape(body)}</p></section>']
    u.write(ROOT/'results/figures/FIGURE_REVIEW_GALLERY.html', '\n'.join(gallery))
    info = ('# Figures - 2026-10-15\n\nSeven-variable P2 model, three primary classes, 2,299 positive-population tracts '
        '(1,235 / 428 / 636), 9,066,522 residents. NCV14 is supplementary environmental context, not a fitted coordinate. '
        'K4 remains a saved sensitivity result, not a second primary model.\n\n16 numbered figures: Main 1-7 and Supplement 1-9. '
        'The compact combined packet has 20 pages: 16 native artwork-plus-concise-caption pages and four retained '
        'complementary-evidence pages. Figure 7 uses borderless tract fills, continuous blue-to-amber SOVI hue and '
        'five-policy burden lightness. Thin outlines show the frozen Q4/cohort-P75 screen; this is not a new score. '
        'Unnumbered enlarged map and aligned single-variable accessibility views are in results/diagnostics/1021/figure7_readability_20261015/.\n\nReproduce: '
        '`python src/la_grid/plotting/build_current_figures.py --portable`. This replays the current figures.\n')
    for rel in ['results/figure_review/README.md','results/figures/README.md']:
        u.write(ROOT/rel, info)
    log = source('results/figure_review/UPDATE_LOG.md',CURRENT_SUITE_BASE).decode()
    u.write(DEST/'UPDATE_LOG.md', log+'\n\n## 2026-10-15 - Figure 7 map readability update\n\n'
        'Figure 7C/D now use the exact tract paths without ordinary internal strokes. The 16 N/A tracts retain white fill and charcoal boundaries. '
        'Panel D uses continuous SOVI hue and five-policy recovery-burden lightness; the 94 frozen Q4/P75 outlines use 0.25-pt strokes. '
        'Layout B enlarges the maps to 1.25 times their prior linear scale. Other numbered figure artwork is byte-identical to the 1021 starting suite. '
        'No Stage 7 data, manuscript, simulation, or K-means output was written.\n')
    u.dump(QA/'SOURCE_AUTHORITY_AND_HASHES.json', dict(source_commit=BASE,current_suite_source_commit=CURRENT_SUITE_BASE,
        map_experiment_source_commit=MAP_REVIEW_BASE,sources=SOURCES,adopted_specification=spec,
        no_stage7_or_simulation_changes=True,figure7_map_qa=style_checks['Main/Fig07']))
    outputs = ['results/figure_review/FIGURE_MANIFEST.csv',
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
        numbered_figures=16, packet_pages=20, primary_K=3, fitted_feature_count=7,
        figure7_layout='B',current_source_commit=CURRENT_SUITE_BASE))
    print('Current suite synchronized: 16 figures, 20 pages; Figure 7C/D rebuilt from frozen vectors; no fits or simulations.')


if __name__ == '__main__':
    main()
