"""Reproduce compact post-processing, record hashes and final preservation."""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).parent))
import analyze_path_b as a


def main():
    figures=list(Path(a.u.lp(a.HERE/'figures')).glob('*.pdf'))+list(Path(a.u.lp(a.HERE/'figures')).glob('*.png'))
    figures=[p for p in figures if p.name!='D_MAP_ACCESSIBILITY_COMPARISON.png']
    science=['FROZEN_P2_TRACT_TABLE_2315.csv','P2_FROZEN_MEMBERSHIPS.csv','P2_STANDARDIZER_AND_WEIGHTS.csv',
             'P2_ORDINARY_COHORT_Z_CLASS_MEANS.csv','VERIFIED_94_COOCCURRENCE_GEOIDS.csv','CLUSTER_ORIGINAL_UNIT_PROFILES.csv']
    before={str(p):a.u.sha(p) for p in figures+[a.HERE/x for x in science]}
    t=time.time()
    command=['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(a.HERE/'run_review.ps1'),'-Python',sys.executable]
    r=subprocess.run(command,cwd=a.ROOT,text=True,capture_output=True)
    a.u.write(a.HERE/'COMPACT_REPRODUCTION_OUTPUT.txt',r.stdout+r.stderr)
    assert r.returncode==0,r.stdout+r.stderr
    after={p:a.u.sha(p) for p in before}
    assert before==after,'Non-identical scientific or figure reproduction'
    a.dump('BUILD_REPRODUCIBILITY_QA.json',dict(command=command,returncode=r.returncode,seconds=time.time()-t,
        outputs_checked=len(before),all_bytes_identical=True,scientific_and_figure_hashes=after,
        clean_room_full_physical_pipeline_run=False,compact_archived_input_replay=True))
    a.dump('REPRODUCTION_ENVIRONMENT.json',dict(python=sys.version,platform=platform.platform(),
        packages={n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','geopandas',
            'matplotlib','Pillow','PyMuPDF','ReportLab','tabulate']}))
    live_before=json.load(open(a.u.lp(a.HERE/'PRESERVATION_BEFORE.json')))
    live_after=a.u.protected_snapshot(live_before)
    assert live_before==live_after
    a.dump('PRESERVATION_AFTER.json',live_after)
    cap=a.ROOT/'docs/reproducibility/figure_suite_concise_captions_20261013/SOURCE_WORKTREE_BEFORE.json'
    original=json.load(open(a.u.lp(cap)))
    source_after=dict(
        HEAD=a.u.git('rev-parse','HEAD',root=a.ROOT.parent/'_ac13').decode().strip(),
        status=a.u.git('status','--porcelain=v1',root=a.ROOT.parent/'_ac13').decode(),
        index_sha256=a.u.sha(a.u.git('rev-parse','--path-format=absolute','--git-path','index',root=a.ROOT.parent/'_ac13').decode().strip()))
    assert source_after['HEAD']==original['HEAD'] and not source_after['status']
    assert source_after['index_sha256']==original['index_sha256']
    a.dump('SOURCE_SUITE_WORKTREE_AFTER.json',source_after)
    heads=a.u.git('ls-remote','origin','refs/heads/review/*','refs/heads/analysis/*').decode().splitlines()
    a.dump('ACTIVE_SOURCE_BRANCH_HEADS.json',[dict(SHA=h.split()[0],ref=h.split()[1]) for h in heads if
        any(s in h for s in ['official-figure-suite','path-b','multi-policy','natural-hazard','author-clarity','fig7d'])])
    a.u.write(a.HERE/'FILE_SCOPE_CHECK.txt',a.u.git('diff','--name-only')+a.u.git('status','--short'))
    record_manifest()
    print('Reproduction byte-identical:',len(before),'outputs. Protected950/index unchanged.')


def record_manifest():
    rows=[]
    for p in sorted(Path(a.u.lp(a.HERE)).rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:continue
        rel=str(p.relative_to(Path(a.u.lp(a.HERE)))).replace('\\','/')
        if rel=='OUTPUT_FILE_MANIFEST.csv':continue
        rows.append(dict(path=rel,bytes=p.stat().st_size,sha256=a.u.sha(p),
            role='exact_source_copy' if rel.startswith('inputs/') else 'review_derived_output_or_script'))
    a.save('OUTPUT_FILE_MANIFEST.csv',__import__('pandas').DataFrame(rows))


if __name__=='__main__':main()
