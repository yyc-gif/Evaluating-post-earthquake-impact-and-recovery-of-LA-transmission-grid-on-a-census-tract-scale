import ast
import json
from pathlib import Path

import fitz

ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'


def test_labels_correct_in_artwork_and_both_packets():
    for path,index in [(SUITE/'Supplement/FigS05.pdf',0),
                       (SUITE/'ALL_SUPPLEMENT_FIGURES.pdf',4),
                       (SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf',11)]:
        with fitz.open(path) as doc:
            text=' '.join(doc[index].get_text().replace('\xa0',' ').split())
            assert 'production' not in text.lower()
            assert '3% cutoff' in text
            assert 'Change from 3% cutoff (h)' in text
            assert '+0.543' in text and '+0.153' in text


def test_current_route_and_scientific_preservation():
    qa=json.loads((ROOT/'docs/reproducibility/s5_cutoff_wording_20261107/QA.json').read_text())
    assert qa['outside_label_pixels_identical']
    assert qa['deterministic_renderer']
    assert qa['captions_unchanged']
    assert len(qa['preserved_artwork_sha256'])==30
    assert len(qa['active_figure_word_audit'])==16
    assert not any(qa['active_figure_word_audit'].values())
    tree=ast.parse((ROOT/'src/la_grid/plotting/build_current_suite_p2.py').read_text())
    assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
               and n.func.attr=='mapping_cutoff_labels' for n in ast.walk(tree))
