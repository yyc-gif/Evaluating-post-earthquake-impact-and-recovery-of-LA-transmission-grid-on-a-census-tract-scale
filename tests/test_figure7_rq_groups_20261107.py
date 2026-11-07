from pathlib import Path
import json
import fitz

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'docs/reproducibility/figure7_rq_groups_20261107/QA.json'
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'


def test_research_question_feature_membership_is_explicit():
    qa=json.loads(QA.read_text(encoding='utf-8'))
    assert qa['RQ_groups']=={
        'RQ1':['Init_Supply','Grid_Impact','Redundancy_HHI'],
        'RQ2':['B_Unconstrained','MeanDelta'],
        'RQ3':['SOVI_SCORE','log1p_Population']}
    with fitz.open(SUITE/'Main/Fig07.pdf') as doc:
        spans=[s for block in doc[0].get_text('dict')['blocks'] for line in block.get('lines',[]) for s in line['spans']]
        for rq in ['RQ1','RQ2','RQ3']:
            selected=[s for s in spans if s['text']==rq]
            assert len(selected)==1
            assert 87.9<selected[0]['bbox'][2]<88.1
            assert selected[0]['size']==7.5
    assert len(qa['printed_cells'])==21
    assert qa['all_21_profile_values_unchanged'] is True


def test_profile_edit_preserves_all_other_artwork_and_science():
    qa=json.loads(QA.read_text(encoding='utf-8'))
    assert qa['A_C_D_pixels_identical'] is True
    assert len(qa['preserved_artwork_sha256'])==30
    assert 'Main/Fig01.pdf' in qa['preserved_artwork_sha256']
    assert 'Main/Fig04.pdf' in qa['preserved_artwork_sha256']
    assert 'Main/Fig06.pdf' in qa['preserved_artwork_sha256']
    assert qa['deterministic_renderer'] is True
    assert qa['models_refitted'] is False
    assert qa['scientific_files_changed'] is False
