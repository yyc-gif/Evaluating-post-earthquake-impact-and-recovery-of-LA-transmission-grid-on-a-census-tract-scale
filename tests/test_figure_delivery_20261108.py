import hashlib
import json
from pathlib import Path
import zipfile

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
