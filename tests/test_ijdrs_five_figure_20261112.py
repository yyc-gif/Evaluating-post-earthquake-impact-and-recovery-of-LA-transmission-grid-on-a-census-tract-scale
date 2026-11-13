"""Independent IJDRS configuration: preserve evidence, not a preferred result."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unicodedata

import fitz
from PIL import Image
import pikepdf
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ijdrs_five',ROOT/'src/la_grid/plotting/build_ijdrs_five_figure.py')
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
D=a.DEST


def read(name):return json.loads((D/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def text(path):
    with fitz.open(path) as doc:return unicodedata.normalize('NFKC',doc[0].get_text()).replace('\xad','-').replace('\ufffd',' ')


def test_all_32_accepted_master_payloads_match_frozen_commit():
    rows=read('qa/SOURCE_IDENTITIES.json')['master_files']
    assert len(rows)==32
    for row in rows:
        pointer=subprocess.check_output(['git','show',a.ART_BASE+':'+row['path']],cwd=ROOT)
        expected=re.search(rb'oid sha256:([0-9a-f]{64})',pointer).group(1).decode()
        assert sha(ROOT/row['path'])==row['sha256']==expected


def test_master_caption_and_source_manifest_remain_unchanged():
    for name in ['MANUSCRIPT_FACING_CAPTIONS.md','FIGURE_MANIFEST.csv']:
        path=(a.SOURCE/name).relative_to(ROOT).as_posix()
        expected=subprocess.check_output(['git','show',a.BASE+':'+path],cwd=ROOT).decode().replace('\r\n','\n')
        assert (ROOT/path).read_text(encoding='utf-8')==expected


def test_exactly_five_main_and_thirteen_proposed_supplementary_figures():
    assert sorted(p.stem for p in (D/'Main').glob('*.pdf'))==[f'Fig{i:02d}' for i in range(1,6)]
    assert sorted(p.stem for p in (D/'Supplement').glob('*.pdf'))==[f'FigS{i:02d}' for i in range(1,14)]
    for p in list((D/'Main').glob('*.pdf'))+list((D/'Supplement').glob('*.pdf')):
        assert p.with_suffix('.png').exists() and p.with_suffix('.tif').exists()


def test_all_eight_original_supplements_are_preserved_as_complete_artwork():
    copies=read('qa/ASSEMBLY_REGISTRY.json')['copies']
    for old in range(1,9):
        key=f'Supplement/FigS{old+5:02d}'
        row=copies[key]
        assert row['accepted_master']==f'results/figure_review_s6_main4_20261107/Supplement/FigS{old:02d}.pdf'
        assert sha(D/(key+'.pdf'))==sha(ROOT/row['source'])==row['sha256']
        assert sha(D/(key+'.png'))==sha(a.source_pdf(f'FigS{old:02d}').with_suffix('.png'))


def test_mechanism_figure_contains_decomposition_geography_and_dynamic_routes():
    parts=read('qa/ASSEMBLY_REGISTRY.json')['layouts']['Main/Fig02']['placements']
    main={(p['source'],p['original_panel']) for p in parts}
    assert {('Fig03','B'),('Fig03','C'),('Fig03','E'),('Fig04','A: focal policies'),('Fig04','B: focal policies')}<=main
    t=text(D/'Main/Fig02.pdf')
    for phrase in ['Functionality threshold','Loss of source path','Full network','Fixed precomputed path','Time after earthquake']:
        assert phrase in t
    assert 'Substation damage' in t and 'Mean tract T80' in t


def test_distribution_figure_keeps_absolute_targeted_signed_absolute_and_gini_outcomes():
    t=text(D/'Main/Fig03.pdf')
    for phrase in ['Signed Q4-Q1 gap','Mean within-realization |Q4-Q1|','Gini change',
                   'Hospital-linked tracts','Population T80','Q1 lowest','Q4 highest']:
        assert phrase in t,phrase
    for name in ['Impact-first','Hospital-first','Degree-first','Vulnerability-first','Betweenness-first','Random','Unconstrained']:
        assert name in t


def test_complete_source_connectivity_diagnostic_retains_all_four_panels():
    row=read('qa/ASSEMBLY_REGISTRY.json')['copies']['Supplement/FigS03']
    assert row['identity']=='source_connectivity'
    assert sha(D/'Supplement/FigS03.pdf')==sha(ROOT/row['source'])
    t=text(D/'Supplement/FigS03.pdf')
    for phrase in ['Source access from a functional station','Reliability gain from alternate routes','Random']:
        assert phrase in t


def test_resource_and_typology_figures_are_exact_prior_delivery_pdfs():
    copies=read('qa/ASSEMBLY_REGISTRY.json')['copies']
    for number,identity in [(4,'resource_effects'),(5,'community_context')]:
        row=copies[f'Main/Fig{number:02d}']
        assert row['identity']==identity
        assert sha(D/'Main'/f'Fig{number:02d}.pdf')==sha(ROOT/row['source'])


def test_typology_labels_all_counts_and_screen_legend_are_retained():
    t=text(D/'Main/Fig05.pdf')
    for phrase in ['1,235','428','636','N/A (16)','Initial service availability',
                   'Standardized cluster profiles','38.4']:
        assert phrase in t,phrase
    assert 'NCV14' not in t and 'K4' not in t


def nontext_forms(path):
    result=Counter()
    with pikepdf.open(path) as pdf:
        for obj in pdf.objects:
            if not isinstance(obj,pikepdf.Stream) or obj.get('/Subtype')!='/Form':continue
            operations=[ins for ins in pikepdf.parse_content_stream(obj) if str(ins.operator) not in ['Tj','TJ']]
            result[hashlib.sha256(pikepdf.unparse_content_stream(operations)).hexdigest()]+=1
    return result


def test_workflow_changes_only_reference_strings_not_graphics_or_schedule():
    row=read('qa/ASSEMBLY_REGISTRY.json')['workflow']
    assert nontext_forms(ROOT/row['source'])==nontext_forms(D/'Main/Fig01.pdf')
    assert Counter(c['old'] for c in row['changes'])=={'strategies in Figure 5':7,'See Figure 8 for class key':1}
    t=text(D/'Main/Fig01.pdf')
    assert 'strategies in Figure 3' in t and 'See Figure 5 for class key' in t
    for term in ['Crew 5','Crew 9','Crew 12','Crew 14','Crew 17','18.2 h','30.7 h']:
        assert term in t


def test_panel_vector_placements_do_not_shrink_or_redraw_observations():
    q=read('qa/PANEL_EQUIVALENCE.json')
    assert len(q)==14
    assert all(r['scale']==1 and r['text_tokens_identical'] for r in q)
    assert all(r['mean_absolute_rgb_difference']<6 and r['fraction_delta_over_32']<.06 for r in q)


def test_all_main_panel_identities_are_covered_without_silent_deletion():
    rows=read('FIGURE_PANEL_CROSSWALK.json')['panel_mappings']
    for fig,letters in [('2','ABCD'),('3','ABCDE'),('4','ABCD'),('5','AB'),('6','ABCDE'),('7','ABCDEFGH'),('8','ABCD')]:
        assert {r['original_panel'] for r in rows if r['original_figure']==fig}==set(letters)
    assert all(r['ijdrs_targets'] for r in rows)
    assert len([r for r in rows if r['original_figure'].startswith('S')])==8


def test_three_original_contributions_and_research_questions_are_registered():
    m=read('qa/MANUSCRIPT_IDENTITY.json')
    assert m['sha256']==a.MANUSCRIPT_SHA and len(m['research_questions'])==3
    assert 'three distinct empirical contributions' in m['contribution_statement']
    assert m['inserted_elements']==235 and m['deleted_elements']==97


def test_section4_paragraph_plan_uses_actual_current_manuscript_not_old_numbering():
    q=read('SECTION4_PARAGRAPH_CROSSWALK.json')
    assert q['manuscript_sha256']==a.MANUSCRIPT_SHA
    rows={r['paragraph']:r for r in q['paragraphs']}
    assert len(rows)==23 and 'Figure 3A' in rows['P201']['new']
    assert all(r['anchor'] and len(r['source_text_sha256'])==64 for r in rows.values())
    assert sum(bool(r.get('flag')) for r in rows.values())>=18
    assert not read('qa/MANUSCRIPT_IDENTITY.json')['section_4_6_present']
    assert 'No Section 4.6 exists' in (D/'SECTION4_EDITING_PLAN.md').read_text()


def test_manuscript_is_not_edited_or_copied_into_delivery():
    if a.DEFAULT_MANUSCRIPT.exists():assert sha(a.DEFAULT_MANUSCRIPT)==a.MANUSCRIPT_SHA
    assert not list(D.rglob('*.docx'))


def test_captions_keep_uncertainty_units_and_valid_reference_ranges():
    records=a.caption_records()
    assert 'realization ranges' in records['3'][1] and 'confidence intervals for mean effects' in records['4'][1]
    assert 'unweighted hospital-linked' in records['3'][1]
    assert '38.38135' in records['5'][1] and 'not a significance test' in records['5'][1]
    assert 'station percentiles' in records['S2'][1]
    for title,body in records.values():
        for m in re.finditer(r'(?<!Supplementary )Figure (\d+)',body):assert 1<=int(m[1])<=5
        for m in re.finditer(r'Supplementary Figure S(\d+)',body):assert 1<=int(m[1])<=13


def test_main_caption_upload_file_contains_only_the_five_main_captions():
    main=(D/'MAIN_CAPTIONS.md').read_text(encoding='utf-8')
    supp=(D/'SUPPLEMENTARY_CAPTIONS.md').read_text(encoding='utf-8')
    assert len(re.findall(r'^## Figure ',main,re.M))==5
    assert '## Supplementary Figure' not in main
    assert len(re.findall(r'^## Supplementary Figure ',supp,re.M))==13
    for title,body in a.caption_records().values():assert body in (supp if title.startswith('Supplementary') else main)


def test_each_packet_page_has_artwork_immediately_followed_by_its_caption():
    for filename,expected in [('ALL_MAIN_FIGURES_WITH_CAPTIONS.pdf',5),
        ('ALL_SUPPLEMENT_PROPOSED_WITH_CAPTIONS.pdf',13),('ALL_FIGURES_WITH_CAPTIONS.pdf',18)]:
        with fitz.open(D/filename) as doc:
            assert len(doc)==expected
            for page in doc:
                assert re.search(r'(Supplementary )?Figure (S?\d+)\.',page.get_text())


def test_packet_caption_font_tags_are_bound_in_each_page_not_only_nested_artwork():
    for filename in ['ALL_MAIN_FIGURES_WITH_CAPTIONS.pdf','ALL_SUPPLEMENT_PROPOSED_WITH_CAPTIONS.pdf','ALL_FIGURES_WITH_CAPTIONS.pdf']:
        with pikepdf.open(D/filename) as pdf:
            for page in pdf.pages:
                fonts=page.Resources.get('/Font',{})
                shown=[ins.operands[0] for ins in pikepdf.parse_content_stream(page) if str(ins.operator)=='Tf']
                assert shown
                assert all(name in fonts for name in shown)
                assert any(str(name).startswith('/PacketCaption') for name in shown)


def test_all_real_tiffs_are_600dpi_lossless_rgb_and_equal_pngs():
    rows=read('FIGURE_MANIFEST.json')['figures']
    assert len(rows)==18
    for row in rows:
        pdf=D/row['pdf'];assert sha(pdf)==row['pdf_sha256']
        with Image.open(pdf.with_suffix('.tif')) as tif,Image.open(pdf.with_suffix('.png')) as png:
            assert tif.format=='TIFF' and tif.mode=='RGB' and tif.info['compression']=='tiff_lzw'
            assert abs(tif.info['dpi'][0]-600)<.1 and tif.info.get('icc_profile')
            assert tif.size==png.size and tif.tobytes()==png.convert('RGB').tobytes()


def test_dimensions_and_fonts_do_not_depend_on_uniform_page_shrinking():
    rows=read('FIGURE_MANIFEST.json')['figures']
    for row in rows:
        assert row['minimum_text_pt']>=6.99
        assert 182.8<=row['size_mm'][0]<=185.01
        if row['group']=='Main':assert row['size_mm'][1]<245
        assert all('Arial' in font or 'DejaVu' in font for font in row['fonts'])


def test_no_scientific_or_manuscript_changes_outside_new_configuration():
    changed=subprocess.check_output(['git','diff','--name-only',a.BASE],cwd=ROOT,text=True).splitlines()
    allowed=lambda p:p=='.gitattributes' or p=='src/la_grid/plotting/build_ijdrs_five_figure.py' or p=='tests/test_ijdrs_five_figure_20261112.py' or p.startswith('results/submission_artwork/IJDRS_five_figure/')
    assert all(allowed(p) for p in changed),changed


def test_builder_has_no_scientific_execution_path():
    code=(ROOT/'src/la_grid/plotting/build_ijdrs_five_figure.py').read_text()
    for term in ['KMeans(','.fit_predict(','.read_parquet(','.read_csv(','run_stage_7(','simulate_recovery(']:
        assert term not in code


def test_journal_limits_are_not_falsely_certified():
    t=(D/'JOURNAL_REQUIREMENTS.md').read_text()
    assert '8,000 words including references' in t and 'HTTP 403' in t
    assert 'not an assertion that IJDRS permits thirteen' in (D/'README.md').read_text()
    assert 'four visible table captions' in t
