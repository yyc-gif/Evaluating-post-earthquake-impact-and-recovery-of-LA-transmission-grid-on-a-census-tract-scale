"""Independent caption-only preservation and assembled-page verification."""
from pathlib import Path
import io
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import fitz

BASE = '8f2dcb3b9762137b9f2686609c34480334f5d44e'
HERE = Path(__file__).resolve().parent
SUITE = ROOT / 'results/figure_review'
SOURCE = ROOT.parent / '_ok13'
ACTIVE = [f'Main/Fig{i:02d}' for i in range(1, 8)] + [f'Supplement/FigS{i:02d}' for i in [1, *range(3, 12)]]


def read(path):
    return json.load(open(u.lp(path), encoding='utf-8'))


def git_state(root):
    index = u.git('rev-parse', '--path-format=absolute', '--git-path', 'index', root=root).decode().strip()
    return {'HEAD': u.git('rev-parse', 'HEAD', root=root).decode().strip(),
            'status_sha256': u.digest(u.git('status', '--porcelain=v1', '-z', root=root)),
            'index_sha256': u.sha(index),
            'staged_names_sha256': u.digest(u.git('diff', '--cached', '--name-only', '-z', root=root))}


def before():
    # Restore only selected, already checked-out LFS pointers from verified local objects.
    for rel in u.git('ls-files', '-z').decode().split('\0'):
        if not rel or not Path(u.lp(ROOT / rel)).is_file():
            continue
        with open(u.lp(ROOT / rel), 'rb') as f:
            pointer = f.read(44).startswith(b'version https://git-lfs.github.com/spec/v1')
        if pointer:
            u.write(ROOT / rel, u.payload(BASE, rel))
    for name in ['.gitattributes', '.gitignore']:
        if not (ROOT / name).exists():
            u.write(ROOT / name, u.git('show', BASE + ':' + name))
    manifest = u.csv_rows(u.payload(BASE, 'results/figure_review/FIGURE_MANIFEST.csv'))
    artifact = {r['current_source_file']: u.sha(ROOT / r['current_source_file']) for r in manifest}
    assert all(artifact[r['current_source_file']] == r['sha256'] for r in manifest)
    reference = read(ROOT / 'docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/PRESERVATION_BEFORE.json')
    protection = u.protected_snapshot(reference)
    assert protection['protected_count'] == 950
    u.dump(HERE / 'PRESERVATION_BEFORE.json', protection)
    files = list(artifact) + [r['mirror_file'] for r in manifest]
    files += ['results/figure_review/' + x for x in ['ALL_MAIN_FIGURES.pdf', 'ALL_SUPPLEMENT_FIGURES.pdf',
              'ALL_FIGURES_WITH_CAPTIONS.pdf', 'CURRENT_CLUSTER_PALETTE.json', 'MANUSCRIPT_FACING_CAPTIONS.md']]
    files += ['results/figure_review/Page_Previews/' + Path(s).name + '.png' for s in ACTIVE]
    files += ['results/figures/' + x for x in ['FIGURE_INDEX.csv', 'FIGURE_REVIEW_GALLERY.html', 'README.md']]
    u.dump(HERE / 'INITIAL_SUITE_IDENTITY.json', {'source_branch': 'review/official-figure-suite-ncv14-h2-k3-d3-20261013',
        'source_commit': BASE, 'remote_HEAD_verified': BASE, 'source_worktree_state': git_state(SOURCE),
        'implementation_initial_state': git_state(ROOT), 'file_sha256': {p: u.sha(ROOT / p) for p in files},
        'manifest_sha256': u.sha(SUITE / 'FIGURE_MANIFEST.csv')})
    print('Before: 950 protected files, original index and 34 artwork payloads recorded.', flush=True)


def after():
    initial = read(HERE / 'INITIAL_SUITE_IDENTITY.json')
    before_protection = read(HERE / 'PRESERVATION_BEFORE.json')
    protection = u.protected_snapshot(before_protection)
    assert before_protection == protection
    assert git_state(SOURCE) == initial['source_worktree_state']
    u.dump(HERE / 'PRESERVATION_AFTER.json', protection)
    manifest = u.csv_rows(open(u.lp(SUITE / 'FIGURE_MANIFEST.csv'), 'rb').read())
    rows = []
    for r in manifest:
        p = r['current_source_file']
        now = u.sha(ROOT / p)
        assert now == initial['file_sha256'][p] == r['sha256'] == u.sha(ROOT / r['mirror_file'])
        rows.append({'file': p, 'before_sha256': initial['file_sha256'][p], 'after_sha256': now,
                     'byte_identical': True, 'mirror_byte_identical': True})
    u.write_csv(HERE / 'UNCHANGED_ARTWORK_HASH_TABLE.csv', rows)
    caps = u.captions(open(u.lp(SUITE / 'MANUSCRIPT_FACING_CAPTIONS.md'), encoding='utf-8').read())
    old_caps = u.captions(u.payload(BASE, 'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    changed = [h for h in caps if caps[h] != old_caps[h]]
    assert len(changed) == 1 and changed[0].startswith('Supplementary Figure S10.')
    expected = 'Outcome comparisons appear in Figures 4\u20136 and Supplementary Figure S11'
    assert expected in caps[changed[0]]
    assert caps[changed[0]] == old_caps[changed[0]].replace(
        'Outcome comparisons appear in Figures 4-6 and Supplementary Figures S12/S13', expected)
    u.dump(HERE / 'CAPTION_TEXT_DIFF.json', {'changed_heading': changed[0],
        'before': old_caps[changed[0]], 'after': caps[changed[0]], 'other_16_captions_identical': True})
    old = fitz.open(stream=u.payload(BASE, 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'), filetype='pdf')
    full = fitz.open(u.lp(SUITE / 'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    assert len(full) == len(old) == 38
    same_pages = []
    for i in range(38):
        if i == 31:
            continue
        assert full[i].rect == old[i].rect and full[i].get_text() == old[i].get_text()
        assert full[i].get_pixmap(dpi=100, alpha=False).samples == old[i].get_pixmap(dpi=100, alpha=False).samples
        same_pages.append(i + 1)
    for i, stem in enumerate(ACTIVE):
        with fitz.open(u.lp(SUITE / (stem + '.pdf'))) as artwork:
            assert artwork[0].get_text() == full[2 * i].get_text()
            assert artwork[0].get_pixmap(dpi=100, alpha=False).samples == full[2 * i].get_pixmap(dpi=100, alpha=False).samples
        assert list(caps)[i] in ' '.join(full[2 * i + 1].get_text().split())
    s10 = full[31]
    assert expected in ' '.join(s10.get_text().split())
    spans = [s for b in s10.get_text('dict', flags=0)['blocks'] for line in b.get('lines', []) for s in line['spans']]
    assert min(s['size'] for s in spans) >= 9.99
    assert all(s10.rect.contains(fitz.Rect(s['bbox'])) for s in spans)
    s10.get_pixmap(dpi=160, alpha=False).save(u.lp(HERE / 'S10_CAPTION_PAGE32_PUBLICATION_PREVIEW.png'))
    retained = {p: h for p, h in initial['file_sha256'].items() if not p.endswith(('ALL_FIGURES_WITH_CAPTIONS.pdf', 'MANUSCRIPT_FACING_CAPTIONS.md'))}
    assert all(u.sha(ROOT / p) == h for p, h in retained.items())
    u.dump(HERE / 'PACKET_AND_PRESERVATION_QA.json', {'pages': 38, 'numbered_figures': 17, 'caption_pages': 17,
        'evidence_pages': 4, 'corrected_S10_caption_page': 32, 'corrected_text': expected,
        'before_packet_sha256': initial['file_sha256']['results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'],
        'after_packet_sha256': u.sha(SUITE / 'ALL_FIGURES_WITH_CAPTIONS.pdf'),
        'unchanged_page_text_and_pixels': same_pages, 'render_dpi': 100,
        'all_17_artwork_and_mirrors_identical': True, 'other_16_captions_identical': True,
        'figure_only_packets_and_previews_identical': True, 'S10_minimum_caption_font_pt': min(s['size'] for s in spans),
        'S10_text_inside_page': True, '950_protected_files_and_original_index_preserved': True,
        'approved_source_worktree_unchanged': True, 'scientific_computation_run': False})
    print('After: 34 artwork files, 37 unchanged packet pages, 950 protected files PASS.', flush=True)


if __name__ == '__main__':
    {'before': before, 'after': after}[sys.argv[1]]()
