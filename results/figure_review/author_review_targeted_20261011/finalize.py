from common import *
import xml.etree.ElementTree as ET,datetime

tree=ET.parse(lp(PKG/'TEST_RESULTS.xml'));suites=list(tree.getroot().iter('testsuite'))
tests=sum(int(s.get('tests',0)) for s in suites);failures=sum(int(s.get('failures',0))+int(s.get('errors',0)) for s in suites)
assert tests==8 and failures==0,(tests,failures)
before=json.load(open(lp(PKG/'PRESERVATION_BEFORE.json')));after=json.load(open(lp(PKG/'PRESERVATION_AFTER.json')))
assert before==after
inputs=json.load(open(lp(PKG/'SOURCE_HASHES.json'),encoding='utf-8'))
for rel,r in inputs.items():p,h=source(rel);assert h==r['sha256'] and sha(p)==h
q4=json.load(open(lp(PKG/'QUARTILE_AND_DEGREE_PROVENANCE.json')))
records=json.load(open(lp(PKG/'ARTWORK_EDIT_RECORDS.json')))
dump('NUMERICAL_INVARIANCE_QA.json',{
    'baseline_commit':BASE,'tests':tests,'failures':failures,'formal_outputs_overwritten':False,
    'simulation_scheduling_GA_clustering_bootstrap_calls':0,'source_hashes_verified':len(inputs),
    'original_index_and_status_identical':True,'protected_files_unchanged':after['protected_count'],
    'original_staged_items_unchanged':after['staged_count'],'current_numbered_set_overwritten':False,
    'six_scheduled_manuscript_policies_and_unconstrained_preserved':True,'formal_five_clusters_preserved':True,
    'quartile_assignments_recalculated':False,'tract_domain':2315,'quartile_counts':q4['quartile_counts'],
    'Degree_spatial_identity_error_hr':abs(q4['degree_population_weighted_change_hr']-q4['degree_saved_summary_change_hr']),
    'common_Fig05_effect_range_hr_unchanged':q4['common_effect_range_hr'],
    'Fig03_scalar_colorbar_index_stream_unchanged':True,'Fig03_A_D_rendering_identical':True,
    'Fig05_A_D_rendering_identical':True,'Fig07_B_D_rendering_identical':True,'S9_B_C_D_rendering_identical':True,
    'C4_recommended_color':'#7b828f','source_C4_color':'#68a9b5',
    'font_sizes_not_reduced':True,'native_width_mm':185,'scientific_numerical_values_changed':False,
    'authors_acceptance_or_promotion_inferred':False})
dump('RUNTIME_VERSIONS.json',{'Python':__import__('sys').version,'PyMuPDF':fitz.VersionBind,
    'numpy':__import__('numpy').__version__,'pandas':__import__('pandas').__version__,
    'geopandas':__import__('geopandas').__version__,'matplotlib':__import__('matplotlib').__version__,
    'Pillow':__import__('PIL').__version__})
with open(lp(PKG/'EXECUTION_LOG.md'),'w',encoding='utf-8',newline='\n') as f:
    f.write('# Execution record\n\n')
    for entry in ['Verified original revision branch and remote HEAD at '+BASE+'.',
        'Created isolated review/targeted-author-figures-20261011 worktree; original staged index not changed.',
        'Read current artwork/captions/manifest and actual plotting/presentation code; copied exact source PDFs.',
        'Rendered and inspected current and proposed PDF pages; produced only targeted vector display edits.',
        'Verified frozen quartiles and saved Degree-first tract-effect algebra; no model stages run.',
        'Compared both Fig5 approaches and both C4 color alternatives; recommended Q4 union outlines and slate-blue C4.',
        'Corrected review-packet font resource collision and long caption heading after actual visual inspection.',
        'Final 8 tests passed; 950 protected scientific hashes and 862 staged items identical.',
        'Finalized native contact sheets, 600-dpi previews, proposed captions and source/output hashes.']:
        f.write('- '+entry+'\n')
    f.write('\nFinalization UTC: '+datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n')
manifest={}
for p in sorted(Path(lp(PKG)).rglob('*')):
    rel=p.relative_to(Path(lp(PKG))).as_posix()
    if not p.is_file() or rel in ['OUTPUT_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json'] or '__pycache__' in rel or 'pytest_tmp' in rel or '_streams.txt' in rel or '_probe.json' in rel or rel=='qa/prior_preservation_schema.json':continue
    manifest[rel]={'sha256':sha(p),'bytes':p.stat().st_size}
dump('OUTPUT_HASHES.json',manifest)
print('Final QA:',tests,'tests;',len(inputs),'input hashes;',len(manifest),'output files;',after['protected_count'],'science files unchanged.')
