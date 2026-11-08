import json
from pathlib import Path

import fitz

ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'


def test_seven_strategy_scope_and_matched_saved_values():
    qa=json.loads((SUITE/'QA/FIG04_MECHANISM_AND_OUTCOME_QA.json').read_text(encoding='utf-8'))
    assert qa['main_panels']==['A','B']
    assert qa['single_pair_decomposition_in_main'] is False
    assert qa['strategies']=={key:1000 for key in ['impact-first','hospital-first',
        'degree-first','vulnerability-first','betweenness-first','random','unconstrained']}
    assert qa['saved_outcome_rows_identical'] and qa['saved_component_rows_identical']
    assert qa['source_trajectory_curves_regenerated'] is False
    assert qa['source_panel_A_translations_pt']=={'legend':22.92,'curves':-18.43}
    with fitz.open(SUITE/'Main/Fig04.pdf') as doc:
        text=doc[0].get_text().replace('\xa0',' ').replace('\u00ad','-')
        assert 'A. Population-weighted service recovery' in text
        assert 'B. Service loss and recovery time' in text
        assert 'C. Why' not in text and 'Degree-first minus Hospital-first' not in text
        assert 'Means; whiskers:' not in text
        for label in ['Impact-first','Hospital-first','Degree-first','Vulnerability-first',
                      'Betweenness-first','Random','Unconstrained']:
            assert label in text


def test_matched_clearance_preservation_and_determinism():
    qa=json.loads((ROOT/'docs/reproducibility/figure4_scope_spacing_20261107/QA.json').read_text(encoding='utf-8'))
    assert all(abs(gap-12)<.05 for gap in qa['title_legend_gaps_pt'])
    assert 18<qa['previous_plot_to_next_title_pt']<23
    assert qa['title_font_size_pt']==9.5
    assert len(qa['preserved_artwork'])==30
    assert 'Main/Fig01.pdf' in qa['preserved_artwork']
    assert 'Main/Fig07.pdf' in qa['preserved_artwork']
    assert qa['deterministic_renderer'] is True
    assert qa['scientific_files_modified'] is False
