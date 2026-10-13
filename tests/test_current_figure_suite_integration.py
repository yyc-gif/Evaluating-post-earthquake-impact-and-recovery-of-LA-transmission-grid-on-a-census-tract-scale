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
QA = ROOT / 'docs/reproducibility/s05_plain_figure_labels_20261012'
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
    assert 'common linear sequential colorbar' in caps
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


def test_approved_integration_and_bounded_display_edits_preserve_science():
    a = audit()
    assert a['updated_figures'] == ['Supplement/FigS05']
    assert len(a['retained_figures']) == 18
    assert a['operator_edits']['Supplement/FigS05']['curves_bars_points_axes_intervals_and_numerical_labels_unchanged']
    edits = a['prior_round_operator_evidence']
    assert edits['Supplement/FigS05']['reviewed_PDF_and_PNG_copied_exactly']
    assert edits['Main/Fig07']['NA']['white_NA_paths'] == 48
    assert edits['Main/Fig07']['NA']['cluster_membership_hotspot_values_and_study_boundary_unchanged']
    assert edits['Main/Fig07']['palette']['C4_after'] == edits['Supplement/FigS09']['C4_after'] == '#8a83b8'
    assert edits['Supplement/FigS10']['metric'] == 'tract population'
    assert edits['Supplement/FigS10']['population_log_norm_range_geometries_stations_and_text_unchanged']
    assert edits['Supplement/FigS11']['hazard'] == '2pc50'
    assert not edits['Supplement/FigS11']['new_means_or_uncertainty_computed']
    assert edits['Supplement/FigS13']['PDF_retained_exactly']
    assert edits['Supplement/FigS13']['merge_decision'] == 'KEEP_SEPARATE'
    cap = open(lp(SUITE / 'MANUSCRIPT_FACING_CAPTIONS.md'), encoding='utf-8').read()
    assert 'The divider separates T80' not in cap
    assert 'shown in white with dark boundaries as N/A' in cap


def test_s05_has_plain_labels_and_preserves_the_scientific_qualifications():
    d = fitz.open(lp(SUITE/'Supplement/FigS05.pdf'))
    plotted = d[0].get_text()
    assert all(t not in plotted for t in ['Pure-random', 'incumbent injection', 'Strict proximity', 'Post-data', 'Net benefit is dominated'])
    assert all(t in plotted for t in ['20 GA runs', 'Median best-so-far loss', 'Decrease', 'Increase', 'Net change'])
    assert all(t in plotted for t in ['32.995522', '+0.277475', '+0.010638', '-0.820788', '-0.532675', '-0.563982', '-0.502321'])
    text = open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    body = re.search(r'^## Supplementary Figure S5\..*?\n\n(.*?)(?=^## )',text,re.M|re.S)[1].strip()
    assert 'it was not included in the initial population' in body
    assert '10/20 runs' in body and '90% single-run criterion' in body
    assert 'global optimality' in body
    assert 'Bonferroni two-contrast family' in body
    assert 'legacy last-position elitism candidate' in body
    assert '0-480 h' in body and '2,000' in body and '64 fixed' in body
    assert 'burden' not in body
    assert all(t in body for t in ['0.232733', '0.009790'])


def test_retained_artwork_is_exact_and_s11_cells_are_archived_values():
    sources = json.load(open(lp(QA/'SOURCE_HASHES.json'),encoding='utf-8'))
    base = audit()['baseline_commit']
    changed = set(audit()['updated_figures'])
    for stem in EXPECTED:
        if stem not in changed:
            for ext in ['pdf','png']:
                rel = 'results/figure_review/'+stem+'.'+ext
                assert sha(ROOT/rel) == sources[base+':'+rel]['sha256']
    e = audit()['prior_round_operator_evidence']['Supplement/FigS11']
    import subprocess
    rel = e['source_path']
    pointer = subprocess.check_output(['git','-C',str(ROOT),'show','c0a11ffb4df523111efe6c8e65cfe86eadffec3c:'+rel])
    match = re.search(rb'oid sha256:([0-9a-f]{64})',pointer)
    if match:
        assert match[1].decode()==e['source_sha256']
    values=e['saved_display_means']
    assert len(values)==6 and all(len(v)==4 for v in values)
    assert abs(max(x for row in values for x in row)-e['linear_norm_h'][1])<1e-12
    assert e['linear_norm_h'][0]==0
    pdf=fitz.open(lp(SUITE/'Supplement/FigS11.pdf'))
    text=pdf[0].get_text()
    assert all(f'{x:+.2f}' in text for row in values for x in row)
    assert 'San Fernando' not in text and 'Northridge' not in text


def test_s05_original_data_graphics_are_byte_preserved():
    a = audit()['operator_edits']['Supplement/FigS05']
    assert len(a['core_stream_invariance']) > 0
    assert all(r['all_other_text_unchanged'] for r in a['core_stream_invariance'])
    visual = json.load(open(lp(QA/'VISUAL_AND_PACKET_QA.json'),encoding='utf-8'))
    assert all(r['unmodified_data_pixels_identical'] for r in visual['data_region_checks'])
    assert visual['actual_packet_pixels_identical']
    assert visual['all_current_labels_inside_page']
