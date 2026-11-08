"""Package the current S6-main4 suite for coauthors after rebuilding it."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

REVIEW='results/figure_review_s6_main4_20261107'
MIRROR='results/figures_s6_main4_20261107'
OUT=ROOT/'results/figure_delivery_20261108'
ZIP_PATH=OUT/'LA_Grid_Figures_2026-11-08.zip'
INDIVIDUAL=OUT/'Individual_Figures'

def sha(data):return hashlib.sha256(data).hexdigest()

def entry(name,data):return {'name':name,'data':data,'sha256':sha(data),'bytes':len(data)}

def build():
    manifest=u.csv_rows((ROOT/REVIEW/'FIGURE_MANIFEST.csv').read_bytes())
    index=u.csv_rows((ROOT/MIRROR/'FIGURE_INDEX.csv').read_bytes())
    caps=(ROOT/REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md').read_bytes()
    full=(ROOT/REVIEW/'ALL_FIGURES_WITH_CAPTIONS.pdf').read_bytes()
    suite_qa=json.loads((ROOT/REVIEW/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
    assert suite_qa['figure1_updated_only_with_frozen_result_curve']
    assert suite_qa['figure1_source_curve_audit']['source_sha256']=='b4a0889e12ed855f1f681b73dbb429306f513585fd00afe058480e6aa5a43922'
    assert suite_qa['figure8_shared_map_legend_updated']
    assert suite_qa['figure8_legend_audit']['new_NA_entries']==1
    assert len(manifest)==32 and len(index)==32
    figures=[]
    for row in manifest:
        if not row['final_name'].endswith('.pdf'):continue
        stem=row['final_name'][:-4]
        pngrow=next(r for r in manifest if r['final_name']==stem+'.png')
        idx=next(r for r in index if r['figure_number']==Path(stem).name and r['format']=='pdf')
        friendly=Path(idx['file']).stem
        folder='Main' if stem.startswith('Main/') else 'Supplement'
        pdf=(ROOT/row['current_source_file']).read_bytes()
        png=(ROOT/pngrow['current_source_file']).read_bytes()
        assert sha(pdf)==row['sha256'] and sha(png)==pngrow['sha256']
        figures.extend([entry(f'Figures/{folder}/{friendly}.pdf',pdf),
                        entry(f'Figures/{folder}/{friendly}.png',png)])
    assert len(figures)==32
    readme=(
        'LA Grid manuscript figures - 2026-11-08, refreshed 2026-11-08\n\n'
        '16 numbered figures: Main Figures 1-8 and Supplementary Figures S1-S8. '
        'Each figure has a separate vector PDF and caption-free PNG. Figure 4 is the complete four-panel source-connectivity figure. '
        'Figure 1 Stage 4 now includes saved population-weighted Unconstrained and Impact-first service-availability curves. '
        'Figure 8 uses one aligned key; N/A appears once, and the screening line spells out the upper-quarter deficit cutoff as 38.4 h. '
        'Figure_Captions.md is separate from the artwork. All_Figures_With_Captions.pdf is the current combined collection.\n\n'
        'Contents: Figures/Main/ (8 PDF/PNG pairs); Figures/Supplement/ (8 pairs); Figure_Captions.md; All_Figures_With_Captions.pdf; SHA256SUMS.txt.\n'
    ).encode('utf-8')
    contents=figures+[entry('Figure_Captions.md',caps),
        entry('All_Figures_With_Captions.pdf',full),entry('README.txt',readme)]
    sums='\n'.join(f"{item['sha256']}  {item['name']}" for item in contents)+'\n'
    contents.append(entry('SHA256SUMS.txt',sums.encode('utf-8')))
    OUT.mkdir(parents=True,exist_ok=True)
    individual_index=[]
    for item in figures:
        parts=Path(item['name']).parts
        folder='Main' if parts[1]=='Main' else 'Supplement'
        target=INDIVIDUAL/folder/parts[-1]
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(item['data'])
        individual_index.append(f"- `{folder}/{parts[-1]}`")
    individual_readme=(
        '# Individual Figures\n\n'
        'Separate caption-free PDF and PNG for every numbered figure. Captions are in the sibling `FIGURE_CAPTIONS.md`.\n\n'
        '## Main Figures\n' + '\n'.join(x for x in individual_index if x.startswith('- `Main/')) +
        '\n\n## Supplementary Figures\n' + '\n'.join(x for x in individual_index if x.startswith('- `Supplement/')) + '\n'
    )
    (INDIVIDUAL/'README.md').write_text(individual_readme,encoding='utf-8')
    temp=ZIP_PATH.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=True) as zf:
        for item in contents:
            info=zipfile.ZipInfo(item['name'],date_time=(2026,11,8,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3
            info.external_attr=0o100644<<16
            zf.writestr(info,item['data'],compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
    temp.replace(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        assert zf.testzip() is None
        assert set(zf.namelist())=={x['name'] for x in contents}
        for item in contents:assert sha(zf.read(item['name']))==item['sha256']
    # Keep convenient loose copies alongside the portable archive.
    (OUT/'FIGURE_CAPTIONS.md').write_bytes(caps)
    (OUT/'ALL_FIGURES_WITH_CAPTIONS.pdf').write_bytes(full)
    individual_hashes={}
    for item in figures:
        parts=Path(item['name']).parts
        folder='Main' if parts[1]=='Main' else 'Supplement'
        name=f"{folder}/{parts[-1]}"
        data=(INDIVIDUAL/folder/parts[-1]).read_bytes()
        assert sha(data)==item['sha256']
        individual_hashes[name]=sha(data)
    qa={'source_commit':suite_qa['source_commit'],
        'figure_suite_source_base_commit':suite_qa['source_commit'],
        'figure1_stage4_curve_sha256':suite_qa['figure1_source_curve_audit']['source_sha256'],
        'stage4_result_curves':suite_qa['figure1_source_curve_audit'],
        'source_main_figures':8,'source_supplementary_figures':8,
        'figure_pairs':16,'zip_members':len(contents),'individual_artwork_files':32,
        'browsable_individual_directory':'Individual_Figures',
        'browsable_individual_artwork_files':len(individual_hashes),
        'browsable_individual_artwork_sha256':individual_hashes,
        'separate_caption_file_sha256':sha(caps),'combined_pdf_sha256':sha(full),
        'zip_sha256':sha(ZIP_PATH.read_bytes()),'zip_bytes':ZIP_PATH.stat().st_size,
        'archive_crc_and_payload_sha256_verified':True,
        'all_figure_artwork_matches_committed_review_suite':True,
        'captions_embedded_in_individual_artwork':False}
    qa['figure8_shared_legend']=suite_qa['figure8_legend_audit']
    u.dump(OUT/'PACKAGE_QA.json',qa)
    readme_md=(
        '# Figure package - 2026-11-08\n\n'
        'Open `Individual_Figures/` to browse or download each figure separately. It contains eight main and eight supplementary figures, each as a separate caption-free PDF and PNG. Captions are in the standalone `FIGURE_CAPTIONS.md` file.\n\n'
        'Download `LA_Grid_Figures_2026-11-08.zip` for the portable coauthor package. Figure 8 has one aligned legend row, one N/A entry, and a plain-language upper-quarter service-deficit cutoff (38.4 h).\n\n'
        'Rebuild with `python src/la_grid/plotting/build_s6_main4_review.py` followed by `python docs/reproducibility/figure_delivery_20261108/package_delivery.py`. The package builder verifies every artwork against the active review manifest and checks archive CRCs and member hashes.\n'
    )
    (OUT/'README.md').write_text(readme_md,encoding='utf-8')
    print(json.dumps(qa,indent=2))

if __name__=='__main__':build()
