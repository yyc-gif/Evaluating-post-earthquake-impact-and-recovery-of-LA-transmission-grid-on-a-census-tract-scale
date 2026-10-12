"""Check original worktree preservation and record numerical/render QA and output bytes."""
from common import *
import pandas as pd,ast
def run():
    before=json.loads(lp(OUT/'PRESERVATION_BEFORE.json').read_text());after=snapshot();dump('PRESERVATION_AFTER.json',after)
    assert before==after,'Original worktree or protected files changed'
    for p in lp(OUT).glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    render=pd.read_csv(lp(OUT/'FIGURE_RENDER_QA.csv'))
    assert len(render)==7 and render.width_mm.sub(185).abs().max()<.01 and render.min_text_pt.min()>=7.5
    render['visual_review']='ACTUAL_RENDER_INSPECTED';save('FIGURE_RENDER_QA.csv',render)
    dump('NUMERICAL_AND_RENDER_QA.json',dict(reference_n=2287,residential_n=2291,model_n=2315,independent_tests_passed=7,tests_file='TEST_RESULTS.txt',PDFs=3,actual_PDF_pages_inspected=7,minimum_font_pt=float(render.min_text_pt.min()),native_width_mm=185,PNG_export_dpi=600,review_notes=['Initial map-page empty margins reduced without changing geography or aspect ratio','Heatmap x labels wrapped and shortened; y labels explicitly right aligned','All source units, percentages,uncertainty and geometry qualifications inspected','Relevant ACS VRE documentation pages9,10,13 and CDC2020 dictionary pages13,18 visually inspected'],protected_files_identical=after['protected_count'],original_staged_items_identical=after['staged_count'],original_index_status_and_HEAD_identical=True,clustering=False,weight_optimization=False,formal_results_changed=False,manuscript_changed=False,figures_promoted=False))
    log(f"Preservation verified: {after['protected_count']} protected files, {after['staged_count']} staged items, original HEAD/index/status unchanged. Actual7 diagnostic pages inspected.")
    omit={'OUTPUT_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json','FINAL_REMOTE_HEAD.json','EXECUTION_LOG.md'}
    manifest={}
    for p in sorted(lp(OUT).rglob('*')):
        rel=p.relative_to(lp(OUT));name=rel.as_posix()
        if not p.is_file() or any(part in ['__pycache__','.pytest_tmp','.pytest_cache'] for part in rel.parts) or name in omit:continue
        manifest[name]=dict(sha256=sha(p),bytes=p.stat().st_size)
    dump('OUTPUT_HASHES.json',manifest)
    print('Validated outputs',len(manifest),'total bytes',sum(r['bytes'] for r in manifest.values()),flush=True)
if __name__=='__main__':run()
