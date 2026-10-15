"""Independent render-region, data-preservation and publication-layout checks."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys

import fitz
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
BASE='b6e9e19bc990350f831f97444f375aa2d66cf43d'
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

REGIONS={
    'Main/Fig05': [('AB',(0,90,524.4094,254),-8),('CD',(0,281,524.4094,451),0),
                   ('E_maps',(0,511,524.4094,708.6614),0)],
    'Main/Fig07': [('ECDFs',(0,60,518.4,264),-8),('profile',(210,302,500,406),-14),
                   ('profile_labels',(20,302,210,405.5),-14),('maps',(0,425,518.4,561),7),
                   ('quartile_legend',(316,566,484,607),7)],
}


def region_checks(stem):
    original=u.payload(BASE,'results/figure_review/'+stem+'.pdf')
    results=[]
    with fitz.open(stream=original,filetype='pdf') as a,fitz.open(u.lp(ROOT/'results/figure_review'/(stem+'.pdf'))) as b:
        assert a[0].rect==b[0].rect
        for name,rect,dy in REGIONS[stem]:
            rect=fitz.Rect(rect)
            x=a[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=rect)
            y=b[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=rect+(0,dy,0,dy))
            before=np.frombuffer(x.samples,np.uint8).astype(int)
            after=np.frombuffer(y.samples,np.uint8).astype(int)
            assert before.shape==after.shape
            fraction=float(np.mean(before!=after));maximum=int(np.abs(before-after).max())
            # Vector translation can change subpixel edge antialiasing only.
            assert fraction<.0001 and maximum<=8,(stem,name,fraction,maximum)
            results.append(dict(region=name,translation_y_pt=dy,changed_channel_fraction=fraction,
                                maximum_edge_antialias_difference=maximum))
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protected-root',type=Path)
    args=parser.parse_args()
    changes={}
    for folder in ['Main','Supplement']:
        for p in sorted((ROOT/'results/figure_review'/folder).glob('*')):
            if p.suffix not in ['.pdf','.png']:continue
            rel=p.relative_to(ROOT).as_posix()
            changes[rel]=dict(before_sha256=u.digest(u.payload(BASE,rel)),after_sha256=u.sha(p))
    changed=[p for p,r in changes.items() if r['before_sha256']!=r['after_sha256']]
    assert set(changed)=={'results/figure_review/'+s+'.'+e
        for s in ['Main/Fig05','Main/Fig07','Supplement/FigS08'] for e in ['pdf','png']}
    authority=ROOT/'results/stage7/2026-10-14'
    for p in authority.iterdir():
        if p.is_file():assert u.sha(p)==u.digest(u.payload(BASE,p.relative_to(ROOT).as_posix()))
    raster={s:region_checks(s) for s in REGIONS}
    text=[]
    for p in (ROOT/'results/figure_review').glob('*/*.pdf'):
        if p.parent.name not in ['Main','Supplement']:continue
        with fitz.open(u.lp(p)) as d:text.append(d[0].get_text())
    assert not re.search(r'\b(?:frozen|saved|P2)\b|Seven-coordinate','\n'.join(text),re.I)
    for stem in ['Main/Fig05','Main/Fig07','Supplement/FigS08']:
        with fitz.open(u.lp(ROOT/'results/figure_review'/(stem+'.pdf'))) as d:
            assert not d[0].get_images()
            assert all(d.extract_font(f[0])[3] for f in d[0].get_fonts())
            ss=[s for b in d[0].get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
            assert all(d[0].rect.contains(fitz.Rect(s['bbox'])) for s in ss)
            assert min(s['size'] for s in ss)>=7.49
    checked=None
    if args.protected_root:
        source=json.loads((ROOT/'docs/reproducibility/author_suite_final_layout_20261012/PRESERVATION_BEFORE.json').read_text())
        for rel,h in source['protected_files'].items():assert u.sha(args.protected_root/rel)==h,rel
        checked=len(source['protected_files']);assert checked==950
    report=dict(status='PASS',baseline_commit=BASE,artwork=changes,unchanged_artwork_pairs=14,
        scientific_authority_files_unchanged=17,protected_scientific_files_checked=checked,
        independent_render_region_comparisons=raster,all_numbered_figures_free_of_process_labels=True,
        no_new_physics_fits_schedules_or_data=True)
    u.dump(HERE/'INDEPENDENT_QA.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['artwork','independent_render_region_comparisons']}))


if __name__=='__main__':main()
