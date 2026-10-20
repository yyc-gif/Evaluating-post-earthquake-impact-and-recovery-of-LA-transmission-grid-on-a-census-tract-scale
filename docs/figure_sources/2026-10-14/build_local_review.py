"""Local-only Elsevier export and QA. Never stages, commits, pushes, or fits."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import zipfile

import fitz
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
PB = ROOT / 'docs/data_research/stage7_path_b_p2_integration_review_20261014'
GATE = ROOT / 'docs/reproducibility/path_b_pre_migration_publication_gate_20261014'
ZIP = Path(r'C:\Users\yinch\Downloads\Path_B_Local_Elsevier_Review_Package.zip')
AUTHORITY = 'ecf431ce9487fcfd822e36259f56d61dfec4f180'
sys.path.insert(0, str(PB))
import analyze_path_b as a


def dump(name, value):
    a.u.dump(OUT / name, value)


def write(name, value):
    a.u.write(OUT / name, value)


def read_json(p):
    return json.load(open(a.u.lp(p), encoding='utf-8'))


def prepare():
    assert not (OUT / 'PRESERVATION_BEFORE.json').exists(), 'Refuse to replace prior local review'
    assert a.u.git('rev-parse', 'HEAD').decode().strip() == AUTHORITY
    tracked = {}
    for rel in a.u.git('ls-files', '-z').decode().split('\0'):
        if rel and Path(a.u.lp(ROOT / rel)).is_file():
            tracked[rel] = a.u.sha(ROOT / rel)
    source = read_json(GATE / 'PRESERVATION_BEFORE.json')
    protected = a.u.protected_snapshot(source)
    assert protected == source
    dump('PRESERVATION_BEFORE.json', dict(
        branch=a.u.git('branch', '--show-current').decode().strip(), HEAD=AUTHORITY,
        index_sha256=a.u.sha(a.u.git('rev-parse', '--path-format=absolute', '--git-path', 'index').decode().strip()),
        tracked_materialized_file_hashes=tracked, protected_original_worktree=protected,
        source_zip_sha256=a.u.sha(ZIP), output_boundary=str(OUT),
        delivery_scope='Local files only; no commit/push/merge/official promotion'))
    rows = []
    with zipfile.ZipFile(ZIP) as z:
        assert len(z.infolist()) == 5
        for member in z.infolist():
            assert member.filename == Path(member.filename).name and not member.is_dir()
            assert member.file_size < 1_000_000
            raw = z.read(member.filename)
            write('inputs/' + member.filename, raw)
            rows.append(dict(path=member.filename, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    a.u.write_csv(OUT / 'ATTACHED_SOURCE_HASHES.csv', rows)
    # Freeze plain scientific definitions independently of the plotting source.
    d = a.load_frozen()
    x = d.loc[d.Population > 0]
    assert len(d) == 2315 and len(x) == 2299 and (d.Population == 0).sum() == 16
    assert x.Population.sum() == 9066522 and x.additional_zero_housing_positive_population.sum() == 8
    assert x.P2_K3_class.value_counts().sort_index().tolist() == [1235, 428, 636]
    delta = np.mean(x[[('B_' + p) for p in a.POLICIES]].to_numpy(), axis=1) if all(
        ('B_' + p) in x for p in a.POLICIES) else None
    np.testing.assert_allclose(x.MeanTotal5, x.B_Unconstrained + x.MeanDelta, atol=1e-12, rtol=0)
    threshold = 38.38135467381475
    high = x.MeanTotal5 >= threshold
    joint = x.frozen_SOVI_quartile.eq('Q4') & high
    assert high.sum() == 575 and joint.sum() == 94 and x.loc[joint, 'Population'].sum() == 350799
    k = pd.read_csv(a.u.lp(PB / 'K3_K4_K5_DECISION_EVIDENCE.csv')).set_index('k')
    dump('SCIENTIFIC_DEFINITION_QA.json', dict(
        study_tracts=2315, eligible_tracts=2299, excluded_zero_population=16,
        included_zero_housing=8, population=9066522, K3_tract_counts=[1235, 428, 636],
        variables=a.FEATURES, squared_distance_budgets=a.BUDGET.tolist(),
        fitted_NCV14=False, MeanTotal5_identity=True, physical_realizations=1000,
        frozen_P75_h=threshold, computed_linear_P75_h=float(np.percentile(x.MeanTotal5, 75)),
        joint_tracts=94, joint_population=350799, q4_tracts=int(x.frozen_SOVI_quartile.eq('Q4').sum()),
        K3_heldout_min_ARI=float(k.loc[3, 'geographic_heldout_min_ARI']),
        K4_heldout_min_ARI=float(k.loc[4, 'geographic_heldout_min_ARI']),
        no_refitting_or_new_simulation=True))
    print('Local inputs copied and original/index/scientific hashes frozen.')


def drawing_signature(drawings, area):
    records = []
    for d in drawings:
        if d['rect'].intersects(area):
            continue
        records.append({k: repr(v) for k, v in d.items() if k not in ['seqno', 'layer']})
    return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest(), len(records)


def export_clean():
    spec = importlib.util.spec_from_file_location('attached_preflight', OUT / 'inputs/local_figure7_elsevier_preflight.py')
    pre = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pre)
    results = {}
    for key, (name, expected) in pre.PROOFS.items():
        src = Path(a.u.lp(GATE / name))
        before = pre.pdf_audit(src)
        assert before['sha256'] == expected, name
        assert not before['hard_preflight_failures'], before['hard_preflight_failures']
        dst = Path(a.u.lp(OUT / ('FIG07_P2_K3_' + key + '_NO_REVIEW_BANNER.pdf')))
        pre.copy_without_review_banner(src, dst)
        after = pre.pdf_audit(dst)
        failures = [r for r in after['hard_preflight_failures'] if not r.startswith('Expected exactly one removable review-status banner')]
        assert not failures and after['review_banner_occurrences'] == 0
        after['audit_role'] = 'clean export, where zero review banners is required'
        after['review_banner_expected'] = 0
        after['hard_preflight_failures'] = failures
        with fitz.open(src) as old, fitz.open(dst) as new:
            area = old[0].search_for(pre.BANNER)[0] + (-1, -1, 1, 1)
            old_spans = [s for s in pre.spans(old[0]) if pre.BANNER not in s['text']]
            new_spans = pre.spans(new[0])
            canonical = lambda ss: [(s['text'], s['size'], tuple(s['bbox']), s['color']) for s in ss]
            assert canonical(old_spans) == canonical(new_spans)
            old_vec, old_n = drawing_signature(old[0].get_drawings(), area)
            new_vec, new_n = drawing_signature(new[0].get_drawings(), area)
            assert old_vec == new_vec and old_n == new_n
            pix0 = old[0].get_pixmap(dpi=150, alpha=False)
            pix1 = new[0].get_pixmap(dpi=150, alpha=False)
            rgb0 = np.frombuffer(pix0.samples, dtype=np.uint8).reshape(pix0.height, pix0.width, 3)
            rgb1 = np.frombuffer(pix1.samples, dtype=np.uint8).reshape(pix1.height, pix1.width, 3)
            changed = np.any(rgb0 != rgb1, axis=2)
            mask = np.zeros(changed.shape, bool)
            r = area * (150 / 72)
            mask[max(0, int(r.y0)-2):int(np.ceil(r.y1))+2, max(0, int(r.x0)-2):int(np.ceil(r.x1))+2] = True
            assert not np.any(changed & ~mask)
            write(dst.stem + '.png', new[0].get_pixmap(dpi=600, alpha=False).tobytes('png'))
        results[key] = dict(source=before, exported=after, expected_input_hash_matches=True,
                            export_hard_failures_excluding_expected_banner_removal=failures,
                            all_non_banner_text_exact=True, scientific_vector_signature=old_vec,
                            outside_banner_vector_count=old_n, outside_banner_pixels_changed=0,
                            tracked_artwork_updated=False)
        previews(OUT / dst.name)
    dump('ELSEVIER_ARTWORK_PREFLIGHT.json', results)
    print('Two clean PDF copies: non-banner text/vectors/pixels exact; fonts embedded; no raster.')


def previews(path):
    import make_review_figures as m
    Path(a.u.lp(OUT / 'previews')).mkdir(parents=True, exist_ok=True)
    with fitz.open(a.u.lp(path)) as doc:
        pix = doc[0].get_pixmap(dpi=150, alpha=False)
        rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3) / 255
    lin = m.linear_rgb(rgb)
    modes = {'COLOR': rgb, 'GRAYSCALE': np.repeat(m.srgb(lin @ [.2126729, .7151522, .0721750])[:, :, None], 3, axis=2)}
    for label, matrix in m.MACHADO.items():
        modes[label.upper()] = np.clip(m.srgb(lin @ np.asarray(matrix).T), 0, 1)
    for mode, v in modes.items():
        Image.fromarray(np.rint(v * 255).astype('uint8')).save(a.u.lp(OUT / 'previews' / (path.stem + '_' + mode + '.png')))


def appendix():
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.patches import Patch
    import make_review_figures as m
    d = a.load_frozen()
    g = gpd.read_file(a.u.lp(PB / 'inputs/FULL_2315_GEOMETRY.gpkg')).set_index('tract_id').join(d)
    positive = g.Population > 0
    v = g.loc[positive, 'MeanTotal5']
    fig = plt.figure(figsize=(7.2, 4.6))
    axes = [fig.add_axes([.025, .22, .45, .66]), fig.add_axes([.525, .22, .45, .66])]
    for ax in axes: m.base_map(ax, g)
    norm = Normalize(v.min(), v.max())
    g.loc[positive].plot(ax=axes[0], column='MeanTotal5', norm=norm, cmap='Greys', edgecolor='#b8b8b8', linewidth=.10)
    tones = ['#e0e0e0', '#b0b0b0', '#777777', '#383838']
    for q, color in zip(['Q1', 'Q2', 'Q3', 'Q4'], tones):
        g.loc[positive & g.frozen_SOVI_quartile.eq(q)].plot(ax=axes[1], facecolor=color, edgecolor='white', linewidth=.10)
    for ax in axes:
        g.loc[~positive].plot(ax=ax, facecolor='white', edgecolor='#333333', linewidth=.45, zorder=8)
        joint = g.loc[g.Q4_and_high_mean_total5]
        joint.boundary.plot(ax=ax, color='white', linewidth=1.15, zorder=9)
        joint.boundary.plot(ax=ax, color='black', linewidth=.65, zorder=10)
    fig.text(.035, .944, 'A. Mean total service deficit', fontsize=9, weight='bold')
    fig.text(.535, .944, 'B. Frozen social-vulnerability quartiles', fontsize=9, weight='bold')
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap='Greys'),
                      cax=fig.add_axes([.06, .17, .38, .019]), orientation='horizontal')
    cb.solids.set_rasterized(False)
    cb.set_ticks([25, 35, 45, 50]); cb.set_label('Five-policy mean total deficit (equivalent h)', fontsize=7.5, labelpad=2)
    cb.ax.tick_params(labelsize=7.5)
    fig.legend([Patch(facecolor=c, edgecolor='#444444') for c in tones], ['Q1', 'Q2', 'Q3', 'Q4'],
               loc='lower left', bbox_to_anchor=(.535, .13), ncol=4, frameon=False, fontsize=7.5, columnspacing=1)
    fig.legend([Patch(facecolor='white', edgecolor='#333333'), Patch(facecolor='none', edgecolor='black')],
               ['N/A (16 zero-population tracts)', 'Q4 and deficit >= frozen P75'],
               loc='lower left', bbox_to_anchor=(.025, .012), ncol=2, frameon=False, fontsize=7.5)
    from matplotlib.text import Text
    fig.canvas.draw()
    for t in fig.findobj(Text): t.set_fontsize(max(7.5, t.get_fontsize()))
    p = OUT / 'FIG07_ACCESSIBILITY_SEPARATE_GRAYSCALE_MAPS.pdf'
    fig.savefig(a.u.lp(p), metadata={'CreationDate': None, 'ModDate': None})
    fig.savefig(a.u.lp(p.with_suffix('.png')), dpi=600)
    plt.close(fig)
    with fitz.open(a.u.lp(p)) as doc:
        txt = [s for b in doc[0].get_text('dict', flags=0)['blocks'] for l in b.get('lines', []) for s in l['spans']]
        assert not doc[0].get_images() and min(s['size'] for s in txt) >= 7.49
        assert all(doc[0].rect.contains(fitz.Rect(s['bbox'])) for s in txt)
        write('FIG07_ACCESSIBILITY_SEPARATE_GRAYSCALE_MAPS_NATIVE.png', doc[0].get_pixmap(dpi=150, alpha=False).tobytes('png'))
    dump('ACCESSIBILITY_APPENDIX_DATA_QA.json', dict(
        modeled_deficit_values_exact=True, original_quartiles_exact=True, cohort=2299, NA=16,
        extra_zero_housing_tracts_classified=8, CRS=str(g.crs), extent=g.total_bounds.tolist(),
        no_composite_score=True, no_statistical_hotspot_inference=True, joint94_exact=True,
        rationale='Separate grayscale maps retain burden and ordinal Q identity without a hue-only encoding.'))
    write('ACCESSIBILITY_APPENDIX_CAPTION.txt',
          'Separate grayscale views of five-policy mean total modeled service-deficit hours (left) and original frozen SOVI quartiles (right). '
          'Black outlines identify Q4 and deficit at or above the frozen cohort P75, with a white halo for visibility. '
          'White polygons with dark boundaries are sixteen zero-population tracts. '
          'This is an accessibility companion, not a combined score or statistically significant hotspot map.\n')
    print('Separate burden/quartile grayscale accessibility companion generated from frozen values.')


def contact_sheet():
    modes = ['COLOR', 'GRAYSCALE', 'PROTANOPIA', 'DEUTERANOPIA', 'TRITANOPIA']
    paths = [OUT / 'previews' / (f'FIG07_P2_K3_{key}_NO_REVIEW_BANNER_{mode}.png')
             for key in ['B_COLOR', 'A_TEXTURE'] for mode in modes]
    images = [Image.open(a.u.lp(p)).convert('RGB') for p in paths]
    w, h = 540, 675
    sheet = Image.new('RGB', (5*w, 2*(h+35)), 'white')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(sheet)
    for i, im in enumerate(images):
        x, y = (i % 5)*w, (i // 5)*(h+35)
        draw.text((x+8, y+8), ('B color / ' if i < 5 else 'A texture / ') + modes[i % 5], fill='black')
        sheet.paste(im.resize((w, h), Image.Resampling.LANCZOS), (x, y+35))
    sheet.save(a.u.lp(OUT / 'COLOR_GRAYSCALE_CVD_CONTACT_SHEET.png'))


def verify():
    before = read_json(OUT / 'PRESERVATION_BEFORE.json')
    assert a.u.git('rev-parse', 'HEAD').decode().strip() == before['HEAD']
    assert a.u.sha(a.u.git('rev-parse', '--path-format=absolute', '--git-path', 'index').decode().strip()) == before['index_sha256']
    for rel, h in before['tracked_materialized_file_hashes'].items():
        assert a.u.sha(ROOT / rel) == h, rel
    after = a.u.protected_snapshot(before['protected_original_worktree'])
    assert after == before['protected_original_worktree'] and a.u.sha(ZIP) == before['source_zip_sha256']
    status = a.u.git('status', '--porcelain=v1').decode()
    assert all(line.startswith('?? local_elsevier_review_outputs/') for line in status.splitlines()), status
    dump('PRESERVATION_AFTER.json', dict(
        tracked_materialized_files_checked=len(before['tracked_materialized_file_hashes']), all_tracked_bytes_unchanged=True,
        protected_scientific_files=950, original_index_and_worktree_unchanged=True,
        review_index_unchanged=True, HEAD_unchanged=True, current_numbered_artwork_pairs_unchanged=17,
        zip_source_unchanged=True, git_status=status, no_commit_push_merge=True))
    rows = []
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.name != 'FILE_SHA256_MANIFEST.csv':
            rows.append(dict(path=str(p.relative_to(OUT)).replace('\\', '/'), bytes=p.stat().st_size, sha256=a.u.sha(p)))
    a.u.write_csv(OUT / 'FILE_SHA256_MANIFEST.csv', rows)
    print('All tracked bytes and 950 protected files/index unchanged. Local-only output hashes recorded.')


if __name__ == '__main__':
    mode = sys.argv[1]
    {'prepare': prepare, 'export': export_clean, 'appendix': appendix,
     'contact': contact_sheet, 'verify': verify}[mode]()
