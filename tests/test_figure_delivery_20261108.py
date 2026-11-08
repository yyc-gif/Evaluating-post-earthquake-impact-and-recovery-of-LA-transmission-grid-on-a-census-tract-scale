import hashlib
import json
from pathlib import Path
import zipfile
import fitz

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/figure_delivery_20261108'

def test_zip_inventory_hashes_and_caption_separation():
    qa=json.loads((OUT/'PACKAGE_QA.json').read_text())
    archive=OUT/'LA_Grid_Figures_2026-11-08.zip'
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==qa['zip_sha256']
    assert qa['figure_pairs']==16 and qa['individual_artwork_files']==32
    assert qa['zip_members']==36 and qa['captions_embedded_in_individual_artwork'] is False
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        names=set(z.namelist())
        assert 'Figure_Captions.md' in names
        assert 'All_Figures_With_Captions.pdf' in names
        assert len([n for n in names if n.startswith('Figures/') and n.endswith('.pdf')])==16
        assert len([n for n in names if n.startswith('Figures/') and n.endswith('.png')])==16
        sums={}
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            digest,name=line.split('  ',1);sums[name]=digest
        assert set(sums)==names-{'SHA256SUMS.txt'}
        for name,digest in sums.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest

def test_loose_captions_and_combined_pdf_match_archive():
    with zipfile.ZipFile(OUT/'LA_Grid_Figures_2026-11-08.zip') as z:
        assert (OUT/'FIGURE_CAPTIONS.md').read_bytes()==z.read('Figure_Captions.md')
        assert (OUT/'ALL_FIGURES_WITH_CAPTIONS.pdf').read_bytes()==z.read('All_Figures_With_Captions.pdf')

def test_browsable_individual_figure_section_matches_archive():
    folder=OUT/'Individual_Figures'
    assert (folder/'README.md').is_file()
    with zipfile.ZipFile(OUT/'LA_Grid_Figures_2026-11-08.zip') as z:
        for archived in z.namelist():
            if not archived.startswith('Figures/'):
                continue
            relative=Path(*Path(archived).parts[1:])
            assert (folder/relative).read_bytes()==z.read(archived)
        assert len(list((folder/'Main').glob('*.pdf')))==8
        assert len(list((folder/'Main').glob('*.png')))==8
        assert len(list((folder/'Supplement').glob('*.pdf')))==8
        assert len(list((folder/'Supplement').glob('*.png')))==8

def test_figure1_stage4_uses_frozen_recovery_curves():
    qa=json.loads((OUT/'PACKAGE_QA.json').read_text())
    assert qa['stage4_result_curves']['scenario']=='2pc50'
    assert qa['stage4_result_curves']['source_sha256']=='b4a0889e12ed855f1f681b73dbb429306f513585fd00afe058480e6aa5a43922'
    fig1=OUT/'Individual_Figures/Main/Fig01_Methodology_Workflow.pdf'
    with fitz.open(fig1) as doc:
        assert len(doc)==1
        page=doc[0]
        spans=[s for b in page.get_text('dict')['blocks'] for line in b.get('lines',[])
               for s in line['spans'] if s['bbox'][0]<258 and 481<s['bbox'][1]<615]
        stage4=' '.join(s['text'].replace('\xa0',' ').replace('\xad','-') for s in spans)
        assert 'Mean population-weighted service availability' in stage4
        assert 'Unconstrained' in stage4 and 'Impact-first' in stage4
        assert 'Time after earthquake (h)' in stage4
        assert 'Time to 80%' not in stage4
        assert 'Time to 80% service' in page.get_text()
        assert len(page.get_drawings())>100
