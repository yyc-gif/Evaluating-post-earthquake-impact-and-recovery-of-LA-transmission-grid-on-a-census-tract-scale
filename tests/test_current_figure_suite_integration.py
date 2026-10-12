"""Integrity gates for the complete author-facing presentation, not model tests."""
from pathlib import Path
import csv
import hashlib
import json
import re
import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / 'results/figure_review'
QA = ROOT / 'docs/reproducibility/figure_suite_integration_20261011'
EXPECTED = [f'Main/Fig{i:02d}' for i in range(1, 8)] + [f'Supplement/FigS{i:02d}' for i in [1, *range(3, 14)]]


def lp(p):
    s = str(p.resolve())
    return s if s.startswith('\\\\?\\') else '\\\\?\\' + s


def sha(p):
    return hashlib.sha256(open(lp(p), 'rb').read()).hexdigest()


def audit():
    return json.load(open(lp(QA / 'INTEGRATION_QA.json'), encoding='utf-8'))


def test_every_numbered_artifact_and_mirror_is_the_exact_selected_payload():
    rows = list(csv.DictReader(open(lp(SUITE / 'FIGURE_MANIFEST.csv'), encoding='utf-8-sig')))
    assert len(rows) == 38
    assert {r['final_name'] for r in rows} == {s + '.' + x for s in EXPECTED for x in ['pdf', 'png']}
    records = {r['current_file']: r for r in audit()['figures']}
    for r in rows:
        current = 'results/figure_review/' + r['final_name']
        assert r['current_source_file'] == current
        assert sha(ROOT / current) == r['sha256'] == records[current]['sha256']
        assert sha(ROOT / r['mirror_file']) == r['sha256']
        assert r['source_commit'] == records[current]['source_commit']
    assert not (SUITE / 'Supplement/FigS02.pdf').exists()


def test_packet_contains_every_figure_at_native_width_followed_by_its_caption():
    full = fitz.open(lp(SUITE / 'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    assert len(full) == 42
    text = open(lp(SUITE / 'MANUSCRIPT_FACING_CAPTIONS.md'), encoding='utf-8').read()
    headings = re.findall(r'^## (.+)', text, re.M)
    assert len(headings) == 19
    for i, (stem, title) in enumerate(zip(EXPECTED, headings)):
        source = fitz.open(lp(SUITE / (stem + '.pdf')))
        native = full[2*i]
        assert abs(native.rect.width - 185 * 72 / 25.4) < .15
        assert tuple(native.rect) == tuple(source[0].rect)
        assert native.get_text() == source[0].get_text()
        cap = full[2*i+1]
        normalized = lambda s: ' '.join(s.split())
        assert normalized(title) in normalized(cap.get_text())
        blocks = cap.get_text('dict')['blocks']
        spans = [s for b in blocks for l in b.get('lines', []) for s in l['spans']]
        assert min(s['size'] for s in spans) >= 9.99
        assert all(cap.rect.contains(fitz.Rect(s['bbox'])) for s in spans)
    assert len(fitz.open(lp(SUITE / 'ALL_MAIN_FIGURES.pdf'))) == 7
    assert len(fitz.open(lp(SUITE / 'ALL_SUPPLEMENT_FIGURES.pdf'))) == 12


def test_pdf_and_png_pairs_are_complete_and_publication_resolution():
    for stem in EXPECTED:
        pdf = fitz.open(lp(SUITE / (stem + '.pdf')))
        assert len(pdf) == 1
        with Image.open(lp(SUITE / (stem + '.png'))) as im:
            assert im.width >= 4360
            target_ratio = pdf[0].rect.width / pdf[0].rect.height
            assert abs(im.width / im.height - target_ratio) < .002
        assert (SUITE / 'Page_Previews' / (Path(stem).name + '.png')).is_file()


def test_explanation_preserves_gate_and_formal_cluster_boundaries():
    caps = open(lp(SUITE / 'MANUSCRIPT_FACING_CAPTIONS.md'), encoding='utf-8').read()
    assert 'Combined removal of the station functionality threshold and source-connectivity requirement' in caps
    assert 'Independent removal-only controls were not evaluated' in caps
    assert 'conditional on the target station being functional' in caps
    assert 'Cluster IDs 1–5' in caps
    assert 'linear within +/-0.10 h' in caps
    assert 'N/A does not mean that every excluded tract has no residents' in caps
    assert 'review candidate' not in caps.lower()
    assert 'companion review evidence' not in caps.lower()


def test_original_science_and_staged_work_remain_unchanged():
    before = json.load(open(lp(QA / 'PRESERVATION_BEFORE.json'), encoding='utf-8'))
    after = json.load(open(lp(QA / 'PRESERVATION_AFTER.json'), encoding='utf-8'))
    assert before == after
    assert before['protected_count'] == 950
    assert before['staged_count'] == 862
    assert not audit()['scientific_results_recomputed']
    assert audit()['original_worktree_unchanged']
