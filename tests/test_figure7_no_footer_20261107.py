from pathlib import Path
import ast
import json
import fitz

ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'


def test_artwork_and_packet_have_no_bottom_explanatory_block():
    for path,page_number in [(SUITE/'Main/Fig07.pdf',0),(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf',6)]:
        with fitz.open(path) as doc:
            page=doc[page_number]
            assert not page.get_textbox(fitz.Rect(0,650,518.4,684)).strip()
            legend=page.get_textbox(fitz.Rect(0,625,518.4,646)).replace('\xa0',' ')
            assert 'N/A' in legend and 'Q4' in legend and 'P75' in legend


def test_canonical_renderer_cannot_restore_the_removed_lines():
    source=ROOT/'src/la_grid/plotting/figure7_final_presentation_20261016.py'
    tree=ast.parse(source.read_text(encoding='utf-8'))
    compose=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='compose_figure')
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                   and n.func.attr=='_text' for n in ast.walk(compose))
    qa=json.loads((ROOT/'docs/reproducibility/figure7_remove_footer_20261107/QA.json').read_text())
    assert qa['summary_line_count']==0 and qa['footer_empty']
    assert qa['other_figure7_pixels_identical'] and qa['legends_preserved']
    assert len(qa['preserved_artwork_sha256'])==30
