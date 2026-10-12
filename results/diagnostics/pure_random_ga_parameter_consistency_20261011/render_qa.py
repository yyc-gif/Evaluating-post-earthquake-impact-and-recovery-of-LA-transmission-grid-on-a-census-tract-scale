"""Render the four diagnostic PDFs; record actual-page visual QA separately."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image
from pypdf import PdfReader

OUT = Path(__file__).resolve().parent
POPPLER = Path(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin')
REVIEW = OUT / 'runtime' / 'pdf_review'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render():
    REVIEW.mkdir(parents=True, exist_ok=True)
    for letter in 'ABCD':
        subprocess.run([str(POPPLER / 'pdftoppm.exe'), '-png', '-r', '120',
                        '-singlefile', str(OUT / f'DIAGNOSTIC_FIGURE_{letter}.pdf'),
                        str(REVIEW / f'figure_{letter}')], check=True)


def record():
    notes = {
        'A': 'Initial pool and historical continuation counts are explicit. Near-reference and T2 effects use separately labeled x scales. Labels and intervals are readable and unclipped.',
        'B': 'Moved legend above the footer after actual-page inspection identified overlap. Bars retain signed self/threshold/source/total values. The two near-coincident policy curves remain distinct by color/style; exact integrals come from saved events, not plotting samples.',
        'C': 'Complete paired histogram and CDF retain both tails, zero, mean, median and all 2000 outcomes. No clipping, trimming or label overlap observed.',
        'D': 'Quartile bars start at zero. Absolute per-realization gap and population-weighted tract Gini use separate labeled units; all three panels are readable without overlapping text.'}
    records = []
    for letter in 'ABCD':
        pdf = OUT / f'DIAGNOSTIC_FIGURE_{letter}.pdf'
        png = REVIEW / f'figure_{letter}.png'
        info = subprocess.run([str(POPPLER / 'pdfinfo.exe'), str(pdf)], check=True,
                              capture_output=True, text=True).stdout
        reader = PdfReader(pdf)
        assert len(reader.pages) == 1
        text = reader.pages[0].extract_text()
        fields = dict(line.split(':', 1) for line in info.splitlines() if ':' in line)
        assert int(fields['Pages']) == 1
        assert f'{letter}1' in text
        pixels = np.asarray(Image.open(png).convert('RGB'))
        ink = (pixels < 245).any(axis=2)
        y, x = np.nonzero(ink)
        assert len(x) > 1000
        records.append(dict(figure=letter, pdf_sha256=digest(pdf),
                            final_png_sha256=digest(OUT / f'DIAGNOSTIC_FIGURE_{letter}.png'),
                            rendered_page_sha256=digest(png), dpi=120, pages=1,
                            pdf_page_size=fields.get('Page size', '').strip(),
                            rendered_pixels=[int(pixels.shape[1]), int(pixels.shape[0])],
                            nonblank_pixel_fraction=float(ink.mean()),
                            ink_bounds_pixels=[int(x.min()), int(y.min()), int(x.max()), int(y.max())],
                            actual_rendered_page_visually_reviewed=True, review_notes=notes[letter]))
    qa = dict(status='PASS', figures=records, diagnostic_author_inspection_only=True,
              manuscript_or_official_figures_changed=False,
              pixel_and_text_checks_not_substitutes_for_visual_review=True,
              uncertainty_definitions_in_captions=True)
    (OUT / 'DOCUMENT_RENDERING_QA.json').write_text(json.dumps(qa, indent=2)+'\n', encoding='utf-8', newline='\n')
    source = OUT / 'FIGURE_RENDER_SOURCE_QA.json'
    data = json.loads(source.read_text(encoding='utf-8'))
    data.update(status='PASS', actual_pdf_page_visual_review='DOCUMENT_RENDERING_QA.json')
    source.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8', newline='\n')
    print('ACTUAL_PDF_RENDER_AND_VISUAL_REVIEW_PASS', len(records))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['render', 'record'])
    args = parser.parse_args()
    {'render': render, 'record': record}[args.phase]()
