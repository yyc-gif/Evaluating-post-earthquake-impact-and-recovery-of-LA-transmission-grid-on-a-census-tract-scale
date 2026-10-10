"""Finalize actual-output measurements and non-target preservation evidence."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import fitz
import pandas as pd
from PIL import Image
from build_preview import sha,dump

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--visual-inspection-confirmed',action='store_true');a=ap.parse_args()
    assert a.visual_inspection_confirmed,'Run only after actual rendered PDF pages have been visually inspected.'
    repo=a.repo.resolve();out=repo/'docs/data_research/built_environment_20261009/manuscript_integration_preview_20261010'
    baseline=json.loads((out/'PRESERVATION_BASELINE.json').read_text())
    changed=[p for p,h in baseline['protected_files'].items() if not (repo/p).exists() or sha(repo/p)!=h]
    index=subprocess.check_output(['git','-C',str(repo),'ls-files','--stage','-z'])
    index_ok=hashlib.sha256(index).hexdigest()==baseline['logical_index_sha256'];assert index_ok and not changed
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip();assert head==baseline['original_head']
    dump(out/'PRESERVATION_FINAL_QA.json',{'protected_files_checked':len(baseline['protected_files']),
         'scientific_files_changed':changed,'scientific_files_changed_count':len(changed),
         'original_862_staged_items_preserved':index_ok,'original_worktree_HEAD_unchanged':head,
         'new_KMeans_fits':0,'simulations':0,'GA_runs':0,'manuscript_or_formal_figures_changed':0})
    figures=[]
    for n in ['FIG_STAGE7_TYPOLOGY_MAP','FIG_STAGE7_CLUSTER_PROFILE','FIG_STAGE7_SPATIAL_ROBUSTNESS']:
        doc=fitz.open(out/(n+'.pdf'));page=doc[0]
        spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
        fonts=page.get_fonts(full=True)
        embedded=[]
        for font in fonts:
            name,ext,kind,buf=doc.extract_font(font[0]);embedded.append({'name':name,'embedded_bytes':len(buf)})
        with Image.open(out/(n+'.png')) as im: px=list(im.size)
        assert not page.get_images() and all(x['embedded_bytes']>0 for x in embedded)
        figures.append({'figure':n,'size_mm':[round(page.rect.width/72*25.4,3),round(page.rect.height/72*25.4,3)],
                        'minimum_normal_font_pt':min(x['size'] for x in spans),'font_resources':embedded,
                        'raster_images_in_PDF':len(page.get_images()),'vector_paths':len(page.get_drawings()),
                        'PNG_pixels':px,'effective_PNG_dpi':px[0]/(185/25.4),
                        'all_text_bounds_within_page':all(page.rect.contains(fitz.Rect(x['bbox'])) for x in spans),
                        'actual_rendering_review':'Poppler 160-dpi rendering of native-width PDF opened and inspected; corrected colorbar/legend spacing and north-arrow placement; no visible overlap or clipped labels in final render',
                        'visual_notes':{'FIG_STAGE7_TYPOLOGY_MAP':'Map fills native page; categorical class colors distinct, four nulls gray, scale and true north separate from data.',
                                        'FIG_STAGE7_CLUSTER_PROFILE':'All feature labels right aligned; five domain labels separated; actual z values annotate saturated cells; raw units in companion tables.',
                                        'FIG_STAGE7_SPATIAL_ROBUSTNESS':'Four related panels, training-support limitation and purity visible; legends separated; membership-expansion map legible.'}[n]})
    dump(out/'VISUAL_QA.json',{'native_width_mm':185,'inspected_all_three_actual_PDF_pages':True,'renderer':'Poppler','figures':figures})
    j=json.loads((out/'STAGE7_CANDIDATE_FREEZE.json').read_text())
    definitions=pd.read_csv(out/'VALIDATED_FEATURE_DEFINITIONS.csv')
    j['feature_definitions_units_vintages']=definitions[definitions.feature.isin(j['coordinate_order'])].to_dict('records')
    j['frozen_output_hashes']={p.name:sha(p) for p in out.iterdir() if p.is_file() and (p.name.startswith('FIG_STAGE7_') or p.name in ['STAGE7_CANDIDATE_LABELS_2291.csv','STAGE7_CANDIDATE_PARAMETERS.npz','STAGE7_CLUSTER_PROFILES.csv','STAGE7_OLD_NEW_CROSSWALK.csv'])}
    dump(out/'STAGE7_CANDIDATE_FREEZE.json',j)
    (out/'EXECUTION_LOG.md').write_text('''# Execution record - 2026-10-10

1. Read original manuscript Sections 2.6 and 3.4 and references, feature QA/decision packets, FEMA composition audit and complete k4 spatial records.
2. Verified actual local source payload hashes against the four authoritative commits. Recorded source bytes, including original study polygons and exact saved partition.
3. Preserved all 950 protected files, original worktree HEAD and the logical index containing 862 staged additions. Used only an isolated preview output directory and a separate analysis branch for the scoped commit.
4. Recovered deterministic preprocessing from identical raw inputs. Weighted matrix SHA-256 exactly reproduces the saved matrix. Preserved every seed42 k4 label; no clustering fit or search.
5. Calculated original-unit profiles, four unclassified records, descriptive old/new contingency and saved-label sensitivity summaries. No physical simulation, scheduling, GA, bootstrap or GIS extraction.
6. Generated three 185-mm Arial vector PDFs and 600-dpi PNGs. Opened actual Poppler renderings and corrected bottom colorbar/legend crowding, map scale placement and profile-label grouping. Re-rendered and inspected all three final pages. Native PDF font embedding, bounds and absence of raster panels are measured in VISUAL_QA.json.
7. Wrote scientific section drafts after reading manuscript terminology. Explicitly retained partial coverage, vintage, small-class specificity, reference-domain and descriptive/causal boundaries.
8. Relevant automated tests and protected-file/index checks are stored with the preview. Remote verification is performed after the scoped commit/push and returned to the author. No formal promotion.
''',encoding='utf-8')
    # Scope normalization to this new preview; scientific source bytes untouched.
    for p in out.iterdir():
        if p.is_file() and (p.suffix in ['.md','.py','.json','.txt'] or p.name in ['.gitignore','.gitattributes']):
            b=p.read_bytes()
            if b.startswith(b'\xff\xfe'):b=b.decode('utf-16').encode('utf-8')
            p.write_bytes(b.replace(b'\r\n',b'\n'))
    files=[]
    for p in sorted(out.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts and p.name not in ['OUTPUT_HASHES.csv','REMOTE_VERIFICATION.json']:
            files.append({'file':p.relative_to(out).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
    pd.DataFrame(files).to_csv(out/'OUTPUT_HASHES.csv',index=False)
    print(json.dumps({'protected_changes':len(changed),'index_preserved':index_ok,'figure_measurements':figures},indent=2))

if __name__=='__main__':main()
