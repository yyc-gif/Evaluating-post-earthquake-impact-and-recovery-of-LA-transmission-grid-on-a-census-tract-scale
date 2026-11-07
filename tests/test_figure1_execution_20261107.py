import json
from pathlib import Path

import fitz

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'docs/reproducibility/figure1_execution_20261107/QA.json'
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'


def test_execution_modes_and_body_typography():
    with fitz.open(SUITE/'Main/Fig01.pdf') as doc:
        spans=[s for b in doc[0].get_text('dict')['blocks'] for l in b.get('lines',[])
               for s in l['spans'] if 481.7<s['bbox'][1] and s['bbox'][3]<614.7
               and 9.5<s['bbox'][0] and s['bbox'][2]<256.3]
        text=' '.join(s['text'].replace('\xa0',' ').replace('\u037e',';') for s in spans)
        assert len(spans)==9
        assert all(abs(s['size']-7.5)<1e-5 and s['font'].startswith('Arial') for s in spans)
        for phrase in ['Unconstrained reference','Constrained restoration',
                       'Repairs proceed in parallel using sampled durations.',
                       'Priority strategy sets repair order.',
                       'Finite crews; dispatch includes directed travel and repairs.',
                       'Repair completion: station functionality = 1',
                       'Source gate + tract weights','Modeled service availability curves']:
            assert phrase in text
        assert '80%' not in text and 'T80' not in text
        assert not any(s['text']=='Time' for s in spans)


def test_scope_and_deterministic_execution_renderer():
    qa=json.loads(QA.read_text(encoding='utf-8'))
    assert qa['outside_stage4_pixels_identical'] is True
    assert qa['deterministic_renderer'] is True
    assert len(qa['preserved_artwork'])==30
    assert qa['body_sizes_pt']==[7.5]
    assert qa['illustrative_curves_removed'] is True
    assert qa['scientific_files_modified'] is False
    assert qa['packet_pages']==16
