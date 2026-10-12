"""Record completed visual inspection; not a substitute for looking at pages."""
import json
from common import *


def main():
    renders=json.loads(lp(OUT/'PDF_RENDER_AND_BOUNDS_QA.json').read_text())
    assert len(renders)==8
    for row in renders:assert sha(OUT/'pdf_review'/row['render'])==row['render_sha256']
    dump('VISUAL_QA.json',dict(status='PASS',all_eight_pages_visually_inspected=True,
        inspection='Actual PDF rasterization at 150 dpi, 7.2-inch publication width, reviewed with image viewer.',
        PDF_hashes={p.name:sha(p) for p in (OUT/'figures').glob('*.pdf')},
        pages=[dict(pdf=r['pdf'],page=r['page'],render_sha256=r['render_sha256']) for r in renders],
        corrected_issues=['Long stability labels initially outside page','Map colorbar label initially outside page',
            'Overlapping minor labels on log stock axis','Crowded class-count prose replaced by table',
            'Fixed-inch header spacing on short pages','Stability legend separated from x label and footer'],
        final_checks=['No visible clipping or incoherent overlaps','Units and frozen-data notice legible',
            'No invented physical pathways or schematic generation claims','Model-specific IDs and matching explicit',
            'Means/medians/percentile ranges distinguished','Six PDFs and 600-dpi PNGs remain diagnostic only']))
    print('Completed eight-page visual review recorded.')


if __name__=='__main__':main()
