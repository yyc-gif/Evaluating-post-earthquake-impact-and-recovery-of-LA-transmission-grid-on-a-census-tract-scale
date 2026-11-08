import hashlib
import importlib.util
import json
from pathlib import Path
import fitz

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'docs/reproducibility/s8_population_white_purple_20261107'
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'

def test_white_purple_geometry_and_preservation():
    q=json.loads((QA/'QA.json').read_text())
    assert q['population_palette']=='white_purple'
    assert q['palette_stops'][0]=='#FFFFFF'
    assert q['palette_stops'][-1]=='#613A80'
    assert q['panels_A_B_pixels_identical'] and q['text_and_positions_identical']
    assert q['all_nonfill_drawing_properties_identical']
    assert q['all_geometry_and_nonfill_properties_unchanged']
    assert q['colorbar_resolution_preserved'] and q['logarithmic_population_normalization_unchanged']
    assert q['paint_colors_changed']>20 and q['deterministic_renderer']
    assert len(q['preserved_artwork_sha256'])==30
    for path,sha in q['preserved_artwork_sha256'].items():
        assert hashlib.sha256((SUITE/path).read_bytes()).hexdigest()==sha
    assert hashlib.sha256((SUITE/'Supplement/FigS08.pdf').read_bytes()).hexdigest()==q['output_sha256']

def test_current_renderer_reproduces_palette():
    spec=importlib.util.spec_from_file_location('refresh_s8',QA/'refresh.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    original=m.u.payload(m.b.CURRENT_SUITE_BASE,'results/figure_review/Supplement/FigS08.pdf')
    assert m.render.priority_geography(original)[0]==(SUITE/'Supplement/FigS08.pdf').read_bytes()

def test_packet_caption_and_mirrors():
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as doc:
        assert len(doc)==16
        text=doc[14].get_text()
        assert 'white-purple' in text and 'blue-green' not in text
        assert 'TARZANA' in text and 'GANESHA' in text
    mirror=ROOT/'results/figures_rq_aligned_20261101'
    for ext in ['pdf','png']:
        assert (SUITE/f'Supplement/FigS08.{ext}').read_bytes()==(mirror/f'FigS08_Priority_Construction.{ext}').read_bytes()
