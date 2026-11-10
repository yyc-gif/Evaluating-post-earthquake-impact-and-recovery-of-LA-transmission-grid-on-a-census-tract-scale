"""Verify the Figure 1 workflow-artifact restore and compact S5 update."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys

import fitz

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import build_s6_main4_review as builder
import figure_presentation

STARTING_COMMIT = 'cb3272058c0d1f244bcaff8d567876a198072ab0'
SUITE = ROOT / 'results/figure_review_s6_main4_20261107'
MIRROR = ROOT / 'results/figures_s6_main4_20261107'
OUT = ROOT / 'docs/reproducibility/figure1_workflow_curves_compact_s5_20261109'
ALLOWED_ARTWORK_CHANGES = {
    'Main/Fig01.pdf', 'Main/Fig01.png',
    'Supplement/FigS05.pdf', 'Supplement/FigS05.png',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(path.read_bytes())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def suite_file_hashes():
    files = {}
    for folder in (SUITE, MIRROR):
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                files[path.relative_to(ROOT).as_posix()] = file_sha(path)
    return files


def validate_outputs():
    records = []
    for stem in builder.NEW:
        for ext in ('pdf', 'png'):
            rel = f'results/figure_review_s6_main4_20261107/{stem}.{ext}'
            expected = builder.u.payload(STARTING_COMMIT, rel)
            current = (ROOT / rel).read_bytes()
            row = {
                'figure': f'{stem}.{ext}',
                'baseline_sha256': sha(expected),
                'current_sha256': sha(current),
                'unchanged_from_start': expected == current,
            }
            records.append(row)
    changed = {row['figure'] for row in records if not row['unchanged_from_start']}
    assert changed == ALLOWED_ARTWORK_CHANGES, changed
    assert sum(row['unchanged_from_start'] for row in records) == 28

    manifest_path = SUITE / 'FIGURE_MANIFEST.csv'
    with manifest_path.open(encoding='utf-8-sig', newline='') as stream:
        manifest = list(csv.DictReader(stream))
    assert len(manifest) == 32
    for row in manifest:
        current = (ROOT / row['current_source_file']).read_bytes()
        mirror = (ROOT / row['mirror_file']).read_bytes()
        assert current == mirror
        assert sha(current) == row['sha256']

    curves = builder.source(builder.WORKFLOW_CURVES)
    pdf = builder.u.payload(builder.WORKFLOW_ARTIFACT_COMMIT, builder.WORKFLOW_ARTIFACT_PDF)
    png = builder.u.payload(builder.WORKFLOW_ARTIFACT_COMMIT, builder.WORKFLOW_ARTIFACT_PNG)
    preview = builder.u.payload(builder.WORKFLOW_ARTIFACT_COMMIT, builder.WORKFLOW_ARTIFACT_PREVIEW)
    generation = json.loads(builder.u.payload(
        builder.WORKFLOW_ARTIFACT_COMMIT, builder.WORKFLOW_GENERATION_RECORD))
    checked_pdf, checked_png, checked_preview, curve_audit = (
        figure_presentation.verify_restoration_workflow_artifact(
            curves, pdf, png, preview, generation))
    assert checked_pdf == (SUITE / 'Main/Fig01.pdf').read_bytes()
    assert checked_png == (SUITE / 'Main/Fig01.png').read_bytes()
    assert checked_preview == (SUITE / 'Page_Previews/Fig01.png').read_bytes()

    plot_data_path = SUITE / 'QA/S5_VULNERABILITY_PLOT_DATA.json'
    plot_data = plot_data_path.read_bytes()
    plot = json.loads(plot_data)
    assert len(plot['series']) == 20
    for panel in ('A', 'B', 'C'):
        assert {item['policy'] for item in plot['series'] if item['panel'] == panel} == {
            'impact-first', 'hospital-first', 'degree-first', 'vulnerability-first'}
    assert {panel: sum(item['panel'] == panel for item in plot['series'])
            for panel in ('A', 'B', 'C')} == {'A': 8, 'B': 4, 'C': 8}
    s5_pdf = SUITE / 'Supplement/FigS05.pdf'
    s5_png = SUITE / 'Supplement/FigS05.png'
    s5_preview = SUITE / 'Page_Previews/FigS05.png'
    with fitz.open(s5_pdf) as document:
        page = document[0]
        width_mm, height_mm = page.rect.width * 25.4 / 72, page.rect.height * 25.4 / 72
        assert abs(width_mm - 185.0) < 0.01 and abs(height_mm - 145.0) < 0.01
        spans = [span for block in page.get_text('dict')['blocks']
                 for line in block.get('lines', []) for span in line.get('spans', [])
                 if span['text'].strip()]
        assert min(span['size'] for span in spans) >= 7.0
        assert {span['font'] for span in spans} == {'ArialMT', 'Arial-BoldMT'}
        visible_text = ' '.join(page.get_text().split())
        for phrase in ('A. Mapping-weight cutoff', 'B. Source-connectivity gate',
                       'C. Functionality threshold', 'Impact-first', 'Hospital-first',
                       'Degree-first', 'Vulnerability-first'):
            assert phrase in visible_text
        assert page.get_pixmap(dpi=600, alpha=False).tobytes('png') == s5_png.read_bytes()
        assert page.get_pixmap(dpi=150, alpha=False).tobytes('png') == s5_preview.read_bytes()

    replay_pdf, replay_png, replay_preview, s5_audit = (
        figure_presentation.supplementary5_four_policy(plot_data))
    assert replay_pdf == s5_pdf.read_bytes()
    assert replay_png == s5_png.read_bytes()
    assert replay_preview == s5_preview.read_bytes()

    qa = json.loads((SUITE / 'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
    margins = qa['s5_vulnerability_plot_audit']['independent_600dpi_png_visible_bounds']
    assert abs(margins['visible_left_mm'] - margins['visible_right_mm']) <= 1.0
    with fitz.open(SUITE / 'ALL_MAIN_FIGURES.pdf') as main_packet, \
         fitz.open(SUITE / 'ALL_SUPPLEMENT_FIGURES.pdf') as supp_packet, \
         fitz.open(SUITE / 'ALL_FIGURES_WITH_CAPTIONS.pdf') as complete_packet:
        packet_pages = {
            'main': len(main_packet),
            'supplement': len(supp_packet),
            'complete': len(complete_packet),
        }
    assert packet_pages == {'main': 8, 'supplement': 8, 'complete': 16}

    return {
        'starting_commit': STARTING_COMMIT,
        'workflow_artifact_commit': builder.WORKFLOW_ARTIFACT_COMMIT,
        'workflow_source_csv': builder.WORKFLOW_CURVES,
        'workflow_source_csv_sha256': sha(curves),
        'workflow_pdf_sha256': sha(pdf),
        'workflow_png_sha256': sha(png),
        'workflow_generation_record_verified': True,
        'figure1_curve_audit': curve_audit,
        's5_plot_data_sha256': sha(plot_data),
        's5_replay_matches_pdf_png_preview': True,
        's5_replay_audit': s5_audit,
        's5_dimensions_mm': [width_mm, height_mm],
        's5_minimum_text_pt': min(span['size'] for span in spans),
        's5_fonts': sorted({span['font'] for span in spans}),
        's5_visible_left_right_mm': [margins['visible_left_mm'], margins['visible_right_mm']],
        'changed_numbered_artwork': sorted(changed),
        'unchanged_numbered_artwork_count': 28,
        'numbered_artwork_count': 32,
        'mirrors_match_manifest': True,
        'packet_pages': packet_pages,
        'packet_sha256': file_sha(SUITE / 'ALL_FIGURES_WITH_CAPTIONS.pdf'),
    }, records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', action='store_true', help='Record the first canonical build hashes.')
    parser.add_argument('--verify-rebuild', action='store_true', help='Compare the second canonical build.')
    args = parser.parse_args()
    assert args.snapshot != args.verify_rebuild, 'Choose exactly one mode.'
    OUT.mkdir(parents=True, exist_ok=True)
    qa, artwork = validate_outputs()
    write_json(OUT / 'INDEPENDENT_FIGURE_QA.json', qa)
    with (OUT / 'ARTWORK_BASELINE_COMPARISON.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(artwork[0]))
        writer.writeheader()
        writer.writerows(artwork)

    hashes = suite_file_hashes()
    snapshot_path = OUT / 'FIRST_CANONICAL_BUILD_HASHES.json'
    if args.snapshot:
        write_json(snapshot_path, hashes)
        qa['first_build_snapshot_sha256'] = sha(snapshot_path.read_bytes())
        qa['second_canonical_build_verified'] = False
    else:
        first = json.loads(snapshot_path.read_text(encoding='utf-8'))
        assert first == hashes, 'Canonical rebuild changed one or more suite outputs.'
        qa['first_build_snapshot_sha256'] = sha(snapshot_path.read_bytes())
        qa['second_canonical_build_verified'] = True
        qa['second_build_output_file_count'] = len(hashes)
    write_json(OUT / 'INDEPENDENT_FIGURE_QA.json', qa)
    print(json.dumps(qa, indent=2))


if __name__ == '__main__':
    main()
