"""Review-only renumbering must preserve every scientific artwork byte."""
import csv
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import fitz

ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'results/figure_review_s6_main4_20261107'
MIRROR=ROOT/'results/figures_s6_main4_20261107'
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
spec=importlib.util.spec_from_file_location('promotion',ROOT/'src/la_grid/plotting/build_s6_main4_review.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def test_exact_numbering_and_inventory():
    manifest=rows(SUITE/'FIGURE_MANIFEST.csv')
    assert len(manifest)==32
    assert {r['final_name'] for r in manifest}=={s+'.'+e for s in builder.NEW for e in ['pdf','png']}
    assert len(list((SUITE/'Main').glob('*.pdf')))==8
    assert len(list((SUITE/'Supplement').glob('*.pdf')))==8
    assert builder.MAPPING['Supplement/FigS06']=='Main/Fig04'
    assert builder.MAPPING['Main/Fig07']=='Main/Fig08'
    assert builder.MAPPING['Supplement/FigS09']=='Supplement/FigS08'
    assert set(builder.MAPPING.values())==set(builder.NEW)

def test_every_artwork_and_mirror_matches_actual_source_bytes():
    for record in rows(SUITE/'FIGURE_MANIFEST.csv'):
        expected=builder.source(record['source_file'])
        assert (ROOT/record['current_source_file']).read_bytes()==expected
        assert (ROOT/record['mirror_file']).read_bytes()==expected
        assert hashlib.sha256(expected).hexdigest()==record['sha256']
    index=rows(MIRROR/'FIGURE_INDEX.csv')
    assert len(index)==32
    assert {r['figure_number'] for r in index}=={Path(s).name for s in builder.NEW}
    for row in index:assert digest(MIRROR/row['file'])==row['sha256']==row['sha256_or_lfs_oid']

def test_all_four_promoted_panels_and_vector_contents_are_unchanged():
    raw=builder.source(builder.SOURCE+'/Supplement/FigS06.pdf')
    with fitz.open(stream=raw,filetype='pdf') as old,fitz.open(SUITE/'Main/Fig04.pdf') as new:
        assert old[0].rect==new[0].rect
        assert old[0].get_text('rawdict')==new[0].get_text('rawdict')
        # Compare original vector operators directly, avoiding expansion of
        # tens of thousands of repeated map paths into Python drawing objects.
        assert old.xref_length()==new.xref_length()
        for xref in range(1,old.xref_length()):
            assert old.xref_object(xref)==new.xref_object(xref)
            if old.xref_is_stream(xref):assert old.xref_stream(xref)==new.xref_stream(xref)
        assert old[0].get_images(full=True)==new[0].get_images(full=True)
        text=new[0].get_text().replace('\xa0',' ')
        for label in ['A. Source connection: full network and fixed path',
                      'B. Additional source connection from alternate routes',
                      'C. Source access from a functional station',
                      'D. Reliability gain from alternate routes']:
            assert label in text
        for strategy in ['Impact-first','Hospital-first','Degree-first','Vulnerability-first','Betweenness-first','Random','Unconstrained']:
            assert strategy in text
        vector_qa=json.loads((ROOT/'docs/reproducibility/s6_main4_promotion_20261107/VERIFICATION.json').read_text())
        assert vector_qa['figure4_vector_and_fonts']['vector_drawings']>100
        assert new[0].get_pixmap(dpi=100).samples==old[0].get_pixmap(dpi=100).samples

def test_packet_sequence_captions_and_native_scale():
    for name,count in [('ALL_MAIN_FIGURES.pdf',8),('ALL_SUPPLEMENT_FIGURES.pdf',8),('ALL_FIGURES_WITH_CAPTIONS.pdf',16)]:
        with fitz.open(SUITE/name) as doc:assert len(doc)==count
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as doc:
        for i,stem in enumerate(builder.NEW):
            assert builder.label(stem)+'.' in doc[i].get_text()
            with fitz.open(SUITE/(stem+'.pdf')) as art:
                assert doc[i].rect.width==art[0].rect.width
                assert doc[i].rect.height>art[0].rect.height
        with fitz.open(SUITE/'Main/Fig04.pdf') as art:
            rect=art[0].rect
            assert doc[3].get_pixmap(dpi=100,clip=rect).samples==art[0].get_pixmap(dpi=100).samples
            assert 'fragility-based station diagnostics' in doc[3].get_text()
            assert 'These topological measures are not delivered electricity' in ' '.join(doc[3].get_text().split())

def test_caption_references_and_simultaneous_renumbering():
    text=(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    assert len(re.findall(r'^## ',text,re.M))==16
    assert 'Figures 5-7 and Supplementary Figure S8' in text
    assert 'Supplementary Figure S9' not in text
    assert builder.references('Figure 4 and Figure 7; Supplementary Figure S6; Figures 4-6; Supplementary Figure S9')==(
        'Figure 5 and Figure 8; Figure 4; Figures 5-7; Supplementary Figure S8')
    for n in re.findall(r'Supplementary Figure S(\d+)',text):assert 1<=int(n)<=8
    for n in re.findall(r'(?<!Supplementary )Figure (\d+)',text):assert 1<=int(n)<=8
    assert (SUITE/'MANUSCRIPT_INTEGRATION.md').is_file()
    assert 'immediately before Section 4.3' in (SUITE/'MANUSCRIPT_INTEGRATION.md').read_text()

def test_palette_and_source_science_preserved():
    expected=json.loads(builder.source(builder.SOURCE+'/CURRENT_CLUSTER_PALETTE.json'))
    actual=json.loads((SUITE/'CURRENT_CLUSTER_PALETTE.json').read_text())
    assert {k.replace('Figure7_','Figure8_'):v for k,v in expected.items()}==actual
    q=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text())
    assert q['all_four_promoted_panels_preserved'] and q['all_16_artwork_pairs_byte_identical']
    assert q['dynamic_full_minus_fixed_identity_max_abs_error']<1e-12
    assert q['static_station_records']==92 and q['static_core_source_records']==14
    for path,record in json.loads((SUITE/'QA/SOURCE_IDENTITIES.json').read_text())['source_files'].items():
        assert hashlib.sha256(builder.source(path)).hexdigest()==record['sha256']

def test_source_suite_files_are_not_overwritten():
    manifest=builder.u.csv_rows(builder.source(builder.SOURCE+'/FIGURE_MANIFEST.csv'))
    for row in manifest:
        assert digest(ROOT/row['current_source_file'])==row['sha256']
        assert digest(ROOT/row['mirror_file'])==row['sha256']
    assert (ROOT/builder.SOURCE/'MANUSCRIPT_FACING_CAPTIONS.md').read_bytes()==builder.source(builder.SOURCE+'/MANUSCRIPT_FACING_CAPTIONS.md')
