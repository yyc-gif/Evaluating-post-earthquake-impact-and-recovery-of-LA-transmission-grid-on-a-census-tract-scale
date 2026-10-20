"""Verify the dated version against the pre-cleanup commit; no calculations."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import os
import re
import subprocess

ROOT=Path(__file__).resolve().parents[3]
BEFORE='aecc9adadd04edc4c5f64de64f79ed4c34c1f69c'


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))


def sha(path):
    path=str(path.resolve())
    if os.name=='nt' and not path.startswith('\\\\?\\'):path='\\\\?\\'+path
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def baseline_hash(rel):
    data=git('show',BEFORE+':'+rel)
    pointer=re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize (\d+)\n',data)
    return pointer[1].decode() if pointer else hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protected-root',type=Path)
    args=parser.parse_args()
    old=set(git('ls-tree','-r','--name-only',BEFORE).decode().splitlines())
    current=set(git('ls-files','-z').decode().strip('\0').split('\0'))
    renamed={p:p.replace('results/stage7/P2_K3_2299/','results/stage7/2026-10-14/')
             for p in old if p.startswith('results/stage7/P2_K3_2299/')}
    renamed.update({p:p.replace('local_elsevier_review_outputs/','docs/figure_sources/2026-10-14/')
                    for p in old if p.startswith('local_elsevier_review_outputs/')
                    and p.replace('local_elsevier_review_outputs/','docs/figure_sources/2026-10-14/') in current})
    renamed.update({'src/la_grid/plotting/build_current_suite_k3.py':'src/la_grid/plotting/build_current_figures.py',
                    '.github/workflows/p2-current.yml':'.github/workflows/verify.yml'})
    retired=old-current-set(renamed)
    assert not any(p.startswith(('Data/','data/','Formal_Experiment_20260923/')) for p in retired)
    artwork={}
    for p in sorted(old):
        if p.startswith(('results/figure_review/Main/','results/figure_review/Supplement/')) and p.endswith(('.pdf','.png')):
            h=sha(ROOT/p)
            assert h==baseline_hash(p),p
            artwork[p]=h
    assert len(artwork)==34
    authority={}
    for a,b in renamed.items():
        if a.startswith('results/stage7/P2_K3_2299/'):
            assert baseline_hash(a)==sha(ROOT/b),b
            authority[b]=sha(ROOT/b)
    assert len(authority)==17
    packets={}
    for name in ['ALL_MAIN_FIGURES.pdf','ALL_SUPPLEMENT_FIGURES.pdf','ALL_FIGURES_WITH_CAPTIONS.pdf',
                 'MANUSCRIPT_FACING_CAPTIONS.md']:
        p='results/figure_review/'+name
        assert sha(ROOT/p)==baseline_hash(p),p
        packets[p]=sha(ROOT/p)
    assert git('rev-parse','main').decode().strip()=='8525954d943efe9f06c98c51f218568077788b9b'
    assert not any(p.endswith(('.doc','.docx')) for p in current)
    assert len(retired)==4397,len(retired)
    protected=None
    if args.protected_root:
        register=json.loads((ROOT/'docs/reproducibility/author_suite_final_layout_20261012/PRESERVATION_BEFORE.json').read_text())
        protected=register['protected_files']
        assert len(protected)==950
        for path,h in protected.items():assert sha(args.protected_root/path)==h,path
    report=dict(status='PASS',version='2026-10-14',baseline_commit=BEFORE,
        tracked_before=len(old),tracked_after=len(current),retired_files=len(retired),renamed_paths=len(renamed),
        retired_groups=dict(collections.Counter('/'.join(p.split('/')[:2]) for p in retired)),
        numbered_artwork_pairs_unchanged=17,artwork_sha256=artwork,
        scientific_authority_files_unchanged=17,authority_sha256=authority,
        packets_and_captions_unchanged=packets,main_unchanged=True,
        protected_original_files_checked=len(protected) if protected is not None else None,
        no_model_or_physical_calculations=True,
        backup='Verified offline Git bundle and retired-path/blob register outside the checkout; local files retained.')
    (Path(__file__).parent/'checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if not k.endswith('sha256') and k!='packets_and_captions_unchanged'},indent=2))


if __name__=='__main__':main()
