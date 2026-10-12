"""Record completed human-visible PDF rendering inspection, not automatic approval."""
from common import *


def main():
    rendered=json.loads(lp(OUT/'PDF_RENDER_AND_BOUNDS_QA.json').read_text())
    assert len(rendered)==8 and len(set(r['pdf'] for r in rendered))==6
    dump('VISUAL_QA.json',dict(all_eight_pages_visually_inspected=True,
        actual_publication_width_inches=7.2,render_inspected_dpi=150,preview_dpi=600,
        corrected_defects=['Shortened clipped profile table header','Separated bottom colorbar labels from footnotes'],
        remaining_clipping_or_overlap=False,notice_visible_on_all_pages=True,
        native_Matplotlib_vector_PDFs=True,no_AI_generated_graphics=True,
        PDF_hashes={p.name:sha(p) for p in FIG.glob('*.pdf')}))


FIG=OUT/'figures'
if __name__=='__main__':main()
