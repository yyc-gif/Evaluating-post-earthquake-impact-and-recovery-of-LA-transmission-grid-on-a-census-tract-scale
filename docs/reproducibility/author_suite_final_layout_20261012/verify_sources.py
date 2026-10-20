"""Verify actual cached and original frozen input bytes; no model execution."""
import ast,io,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
QA=Path(__file__).parent
BASE='37e71b3e15b0f4e1be3a651344e3f9e6475dc24b'
sys.path.append(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages')
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u


if __name__=='__main__':
    paths=['Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_TRACT_EFFECTS.parquet',
           'Formal_Experiment_20260923/Formal_Results/TRACT_PAIRED_EFFECTS.parquet',
           'Data/LA_Tracts_With_Population.dbf',
           'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/kmeans_k_diagnostics.csv',
           'src/la_grid/revision/r1_mapping_gate_robustness.py',
           'docs/reproducibility/SUPPLEMENT_ASSUMPTIONS_LAYOUT_UPDATE_20261006.json']
    records={}
    payloads={}
    for rel in paths:
        data=u.payload(BASE,rel);payloads[rel]=data
        records[rel]={'source_commit':BASE,'sha256':u.digest(data),'bytes':len(data),'actual_bytes_verified':True}
    source=ast.parse(payloads['src/la_grid/revision/r1_mapping_gate_robustness.py'].decode())
    node=next(n for n in source.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='GATE_CASES')
    cases=ast.literal_eval(node.value)
    assert cases['G1_BASELINE_050']==('source_gate',.5)
    assert cases['G2_RELAXED_005']==('source_gate',.05)
    assert cases['G3_STRICT_075']==('source_gate',.75)
    producer=next(r for r in json.loads(payloads[paths[-1]]) if r['file']=='Supplement/FigS06.pdf')
    offline=[]
    for r in producer['source_tables']:
        path=u.ORIGINAL/r['path'];actual=u.sha(path);assert actual==r['sha256']
        offline.append({'path':r['path'],'sha256':actual,'bytes':Path(u.lp(path)).stat().st_size,
                        'actual_frozen_local_bytes_verified':True})
    u.dump(QA/'SOURCE_INPUT_VALIDATION.json',{'pinned_cached_sources':records,'gate_definitions':cases,
        'source_requirement_fixed_not_realized_reachability':True,'offline_archives':offline,
        'new_computations_or_source_downloads':False})
    print('Cached source bytes, all three offline hashes and fixed source-gate definitions verified.')
