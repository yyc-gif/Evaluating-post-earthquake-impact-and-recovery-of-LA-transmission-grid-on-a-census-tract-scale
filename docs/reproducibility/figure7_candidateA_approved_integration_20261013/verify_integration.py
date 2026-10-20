"""Independent frozen-source, preservation and presentation verification."""
from pathlib import Path
import hashlib
import io
import json
import os
import subprocess
import sys

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE = ROOT / 'docs/reproducibility/figure7_candidateA_approved_integration_20261013'
sys.path.append(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages')
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import fitz
import numpy as np
import pandas as pd

BASE = '8f2dcb3b9762137b9f2686609c34480334f5d44e'
REVIEW = 'aa55131cc5455aca9e1a6dead98e8f0eb8944217'
FROZEN = '0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
DECISION = '05a78645b17bf8de04326e54181f9db432d7186c'
RP = 'docs/data_research/figure7_scientific_layout_author_review_20261013/'
DP = 'docs/data_research/stage7_fig7d_policy_robustness_and_final_integration_gate_20261013/'


def snapshot():
    reference = json.loads(u.payload(DECISION, DP + 'STARTING_STATE_AND_PROTECTION.json'))
    protected = u.protected_snapshot(reference)
    assert protected['protected_files'] == reference['protected_files'], 'Protected scientific source hash changed'
    states = {}
    for name in ['_ok13', '_xc13', '_fl13']:
        path = ROOT.parent / name
        index = Path(u.git('rev-parse', '--path-format=absolute', '--git-path', 'index', root=path).decode().strip())
        states[name] = {'head': u.git('rev-parse', 'HEAD', root=path).decode().strip(),
            'status': u.git('status', '--porcelain=v1', '-uall', root=path).decode(),
            'index_sha256': u.sha(index)}
    return {'protected': protected, 'source_worktrees': states}


def prepare():
    before = snapshot()
    assert before['protected']['protected_count'] == 950
    assert before['protected']['staged_count'] == 862
    u.dump(HERE / 'PRESERVATION_BEFORE.json', before)
    # Hydrate only present pointer files in this isolated sparse checkout.
    paths = u.git('ls-files', '-z').decode().split('\0')
    count = 0
    for rel in paths:
        path = ROOT / rel
        if rel and Path(u.lp(path)).is_file():
            with open(u.lp(path), 'rb') as handle:
                pointer = handle.read(44).startswith(b'version https://git-lfs')
            if pointer:
                u.write(path, u.payload(BASE, rel))
                count += 1
    for rel in ['.gitattributes', '.gitignore']:
        if not (ROOT / rel).exists():
            u.write(ROOT / rel, u.git('show', BASE + ':' + rel))
    manifest = u.csv_rows(u.payload(BASE, 'results/figure_review/FIGURE_MANIFEST.csv'))
    assert len(manifest) == 34
    artwork = {}
    for row in manifest:
        for rel in [row['current_source_file'], row['mirror_file']]:
            assert u.sha(ROOT / rel) == row['sha256']
            artwork[rel] = row['sha256']
    sources = {}
    for name in ['build_layout_review.py', 'FIGURE7_CONSERVATIVE_RESTORATION.pdf',
                 'FIGURE7_NA_FILL_SEPARATE_APPROVAL_COMPARISON.pdf']:
        rel = RP + name
        payload = u.payload(REVIEW, rel)
        sources[rel] = {'commit': REVIEW, 'sha256': u.digest(payload), 'bytes': len(payload)}
    u.dump(HERE / 'CURRENT_SUITE_BASELINE.json', {
        'branch': 'review/official-figure-suite-ncv14-h2-k3-d3-20261013', 'HEAD': BASE,
        'implementation_branch': u.git('branch', '--show-current').decode().strip(),
        'implementation_initial_status': u.git('status', '--porcelain=v1', '-uall').decode(),
        'artwork': artwork, 'approved_review_sources': sources, 'hydrated_pointer_files': count,
        'S10_correction_present_on_baseline': False,
        'separate_S10_correction_authority': '7795638a73ac533d544971c20db13cf6662d13d3',
        'S10_correction_carried_forward_explicitly': True})
    print('Baseline verified,', count, 'pointer files hydrated; 950 scientific files protected.', flush=True)


def verify():
    from build_current_suite_k3 import FEATURES, SP, COLORS
    import figure7_candidate_a as a
    f = pd.read_csv(io.BytesIO(u.payload(FROZEN, SP + 'candidate/EIGHT_VARIABLE_FROZEN_TABLE.csv')),
                    dtype={'tract_id': str}, float_precision='round_trip')
    m = pd.read_csv(io.BytesIO(u.payload(FROZEN, SP + 'candidate/K3_CLUSTER_MEMBERSHIP.csv')),
                    dtype={'tract_id': str}, float_precision='round_trip')
    w = pd.read_csv(io.BytesIO(u.payload(FROZEN, SP + 'candidate/COHORT_STANDARDIZER_AND_WEIGHTS.csv')),
                    float_precision='round_trip').set_index('variable').loc[FEATURES]
    f['class'] = m.candidate_display_cluster
    z = (f[FEATURES].to_numpy() - w.cohort_mean.to_numpy()) / w.population_SD.to_numpy()
    rows = u.csv_rows(open(u.lp(HERE / 'PROFILE_CELLS.csv'), 'rb').read())
    assert len(rows) == 24
    for row in rows:
        c = int(row['class'][1:]); field = row['variable']; j = FEATURES.index(field)
        value = z[f['class'].eq(c), j].mean()
        assert abs(value - float(row['ordinary_z_mean'])) < 1e-12
    points = pd.read_csv(u.lp(HERE / 'ECDF_POINTS.csv'), float_precision='round_trip')
    assert len(points.groupby(['variable', 'class'])) == 18
    for (field, c), group in points.groupby(['variable', 'class'], sort=False):
        values = f.loc[f['class'].eq(int(c[1:])), field].to_numpy()
        unique, counts = np.unique(values, return_counts=True)
        np.testing.assert_array_equal(group.value, unique)
        np.testing.assert_array_equal(group.value_count, counts)
        np.testing.assert_array_equal(group.cumulative_fraction, np.cumsum(counts) / len(values))
    baseline = json.load(open(u.lp(HERE / 'CURRENT_SUITE_BASELINE.json')))
    comparison = []
    for rel, expected in baseline['artwork'].items():
        new = u.sha(ROOT / rel)
        changed = '/Fig07.' in rel or 'Fig07_Community_' in rel
        if not changed:
            assert new == expected
        comparison.append({'file': rel, 'baseline_sha256': expected, 'current_sha256': new,
                           'status': 'AUTHORIZED_FIG07_CHANGE' if changed else 'BYTE_IDENTICAL'})
    u.write_csv(HERE / 'UNCHANGED_ARTWORK_HASH_COMPARISON.csv', comparison)
    figure = fitz.open(u.lp(ROOT / 'results/figure_review/Main/Fig07.pdf'))
    assert abs(figure[0].rect.width / a.MM - 185) < 1e-4
    assert abs(figure[0].rect.height / a.MM - 253) < 1e-4
    assert not figure[0].get_images()
    text = figure[0].get_text()
    assert 'LAYOUT PROPOSAL' not in text
    assert all(s in text for s in ['distributions', 'Standardized', 'C1', 'C2', 'C3', 'Q4 boundary'])
    vector_and_pixel_qa(figure)
    full = fitz.open(u.lp(ROOT / 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'))
    assert len(full) == 38
    from build_current_suite_k3 import ACTIVE
    for i, stem in enumerate(ACTIVE):
        art = fitz.open(u.lp(ROOT / ('results/figure_review/' + stem + '.pdf')))
        assert art[0].rect == full[2*i].rect
        assert art[0].get_pixmap(dpi=100).samples == full[2*i].get_pixmap(dpi=100).samples
    before_packet = fitz.open(stream=u.payload(BASE, 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'), filetype='pdf')
    for page in range(38):
        if page not in [12, 13, 31]:
            assert before_packet[page].get_pixmap(dpi=100).samples == full[page].get_pixmap(dpi=100).samples
    assert u.sha(ROOT / 'results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf') == u.digest(u.payload(BASE, 'results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf'))
    manifest = u.csv_rows(open(u.lp(ROOT / 'results/figure_review/FIGURE_MANIFEST.csv'), 'rb').read())
    assert len(manifest) == 34
    for row in manifest:
        assert u.sha(ROOT / row['current_source_file']) == row['sha256'] == u.sha(ROOT / row['mirror_file'])
    after = snapshot()
    assert after == json.load(open(u.lp(HERE / 'PRESERVATION_BEFORE.json')))
    u.dump(HERE / 'PRESERVATION_AFTER.json', after)
    u.dump(HERE / 'INDEPENDENT_QA.json', {'ecdfs_independently_reconstructed': 18,
        'standardized_profile_cells_independently_reconstructed': 24,
        'unchanged_numbered_artwork_pairs': 16, 'packet_pages': 38,
        'all_packet_figure_pixels_identical_to_actual_artwork': True,
        'all_unaffected_packet_pages_identical': True, 'protected_files': 950,
        'original_staged_count': 862, 'protected_source_state_exactly_unchanged': True,
        'packet_sha256': u.sha(ROOT / 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf')})
    from PIL import Image
    with Image.open(u.lp(ROOT/'results/figure_review/Main/Fig07.png')) as preview:
        png={'pixels':list(preview.size),'dpi':list(preview.info['dpi'])}
    u.dump(HERE/'COMPLETE_PACKET_AND_MIRROR_QA.json',{
        'numbered_figures':17,'main_figures':7,'supplement_figures':10,'complete_pages':38,
        'figure_caption_pairs':17,'unchanged_evidence_pages':4,'unchanged_artwork_pairs':16,
        'all_mirrors_match_actual_authoritative_bytes':True,
        'Fig07_native_size_mm':[figure[0].rect.width/a.MM,figure[0].rect.height/a.MM],
        'Fig07_raster_image_objects':len(figure[0].get_images()),'Fig07_PNG':png,
        'file_SHA256':{rel:u.sha(ROOT/rel) for rel in [
            'results/figure_review/Main/Fig07.pdf','results/figure_review/Main/Fig07.png',
            'results/figure_review/ALL_MAIN_FIGURES.pdf','results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf',
            'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf']}})
    print('Independent numerical, packet, mirror and scientific protection checks passed.', flush=True)


def vector_and_pixel_qa(figure):
    import figure7_candidate_a as a
    old = fitz.open(stream=u.payload(BASE,'results/figure_review/Main/Fig07.pdf'),filetype='pdf')
    previous = [d for d in old[0].get_cdrawings() if d['rect'][1] >= 132*a.MM]
    current = [d for d in figure[0].get_cdrawings() if d['rect'][1] >= 140*a.MM]
    assert len(previous) == len(current)
    for i,(p,n) in enumerate(zip(previous,current)):
        assert len(p['items']) == len(n['items'])
        for item1,item2 in zip(p['items'],n['items']):
            assert item1[0] == item2[0]
            for v1,v2 in zip(item1[1:],item2[1:]):
                if isinstance(v1,(tuple,list,fitz.Point,fitz.Rect)):
                    v1=np.array(v1,dtype=float);v2=np.array(v2,dtype=float)
                    v2[1::2]-=8*a.MM
                    # MuPDF exposes transformed coordinates as float32; original path bytes are exact.
                    np.testing.assert_allclose(v1,v2,rtol=0,atol=2e-4)
                else:
                    assert v1==v2
        for key in ['type','closePath','fill_opacity','stroke_opacity','lineCap','lineJoin','dashes','even_odd']:
            assert p.get(key)==n.get(key)
        if a.is_na(p):
            assert n['fill']==(1,1,1) and abs(n['width']-.45)<1e-6
        else:
            for key in ['fill','color','width']:
                assert p.get(key)==n.get(key)
    mask=fitz.open();page=mask.new_page(width=old[0].rect.width,height=old[0].rect.height)
    for d in previous:
        if not a.is_na(d):continue
        shape=page.new_shape()
        for item in d['items']:
            if item[0]=='l':shape.draw_line(item[1],item[2])
            elif item[0]=='re':shape.draw_rect(item[1])
            elif item[0]=='c':shape.draw_bezier(*item[1:])
            elif item[0]=='qu':shape.draw_quad(item[1])
            else:raise AssertionError(item[0])
        shape.finish(color=(0,0,0),fill=(0,0,0),width=1.2,closePath=d['closePath'],even_odd=d['even_odd'])
        shape.commit()
    def pixels(p):
        pix=p.get_pixmap(dpi=254,alpha=False)
        return np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
    # Both locked regions use the same new-page origin; this eliminates float32 MediaBox
    # raster rounding when comparing pages of different heights, without resampling.
    aligned=fitz.open();aligned_page=aligned.new_page(width=figure[0].rect.width,height=figure[0].rect.height)
    clip=fitz.Rect(0,132*a.MM,old[0].rect.width,old[0].rect.height)
    aligned_page.show_pdf_page(clip+(0,8*a.MM,0,8*a.MM),old,0,clip=clip,keep_proportion=False)
    oldpixels=pixels(aligned_page)[1400:2530]
    newpixels=pixels(figure[0])[1400:2530]
    authorized=np.any(pixels(page)[1320:2450]<250,axis=2)
    # One renderer pixel of antialias coverage around the authorized stroked path mask.
    pad=np.pad(authorized,1)
    authorized=np.logical_or.reduce([pad[y:y+authorized.shape[0],x:x+authorized.shape[1]]
                                     for y in range(3) for x in range(3)])
    assert oldpixels.shape==newpixels.shape
    changes=np.any(oldpixels!=newpixels,axis=2)
    outside=changes & ~authorized
    assert outside.sum()==0, ('Changed pixels outside N/A path masks',int(outside.sum()))
    # Review-versus-production A/B comparison at the same native coordinates.
    candidate=fitz.open(stream=u.payload(REVIEW,RP+'FIGURE7_CONSERVATIVE_RESTORATION.pdf'),filetype='pdf')
    reference=pixels(candidate[0])[:1400]
    newtop=pixels(figure[0])[:1400]
    topchanges=np.any(reference!=newtop,axis=2)
    warning=np.zeros_like(topchanges);warning[:80,:]=True
    assert not np.any(topchanges & ~warning), 'Unapproved difference in Candidate A layout'
    u.dump(HERE/'CD_VECTOR_AND_ALIGNED_PIXEL_QA.json',{
        'map_and_legend_vector_drawings':len(previous),'exact_paint_except_34_NA_paths':True,
        'geometry_translation_mm':[0,8],'geometry_coordinate_comparison_tolerance_pt':2e-4,
        'aligned_render_dpi':254,'map_region_pixels':int(changes.size),
        'changed_pixels':int(changes.sum()),'outside_authorized_NA_path_masks_changed_pixels':0,
        'mask_description':'Exact original N/A vector paths with 1.2-pt stroke and one-pixel antialias envelope',
        'approved_candidate_AB_pixels_identical_except_removed_review_warning':True,
        'approved_candidate_SHA256':u.digest(u.payload(REVIEW,RP+'FIGURE7_CONSERVATIVE_RESTORATION.pdf'))})
    full=fitz.open(u.lp(ROOT/'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'))
    for number,name in [(12,'PACKET_FIG07_NATIVE_PREVIEW'),(13,'FIG07_CAPTION_NATIVE_PREVIEW'),(31,'S10_CAPTION_NATIVE_PREVIEW')]:
        full[number].get_pixmap(dpi=160,alpha=False).save(u.lp(HERE/(name+'.png')))
    aligned.close();mask.close();old.close();candidate.close();full.close()


if __name__ == '__main__':
    prepare() if '--prepare' in sys.argv else verify()
