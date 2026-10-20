"""Independent presentation and preservation checks; never runs a model."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import re
import os
from collections import Counter

import fitz

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
BASE='96297fb12fceb8e61137b456648d2655a5909b6b'


def sha(p):
    p=Path(p)
    if os.name=='nt':p=Path('\\\\?\\'+str(p.resolve()))
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snapshot():
    paths=list((ROOT/'results/figure_review').glob('Main/*'))
    paths+=list((ROOT/'results/figure_review').glob('Supplement/*'))
    paths+=list((ROOT/'results/stage7/2026-10-14').glob('*'))
    return {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in paths if p.is_file()}


def main():
    before=HERE/'BEFORE.json'
    if '--before' in sys.argv:
        assert not before.exists()
        state=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
                   status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).decode(),hashes=snapshot())
        assert state['commit']==BASE
        before.write_text(json.dumps(state,indent=2)+'\n')
        return
    original=json.loads(before.read_text())['hashes']
    for p,h in original.items():
        if p.startswith('results/stage7/'):
            assert sha(ROOT/p)==h,p
    sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
    import consolidate_current_figure_suite as u
    manifest=u.csv_rows((ROOT/'results/figure_review/FIGURE_MANIFEST.csv').read_bytes())
    assert len(manifest)==32
    changes=[]
    for r in manifest:
        assert sha(ROOT/r['current_source_file'])==sha(ROOT/r['mirror_file'])==r['sha256']
        old=r['current_source_file']
        if '/FigS08.' in old:old=old.replace('/FigS08.','/FigS09.')
        elif '/FigS09.' in old:old=old.replace('/FigS09.','/FigS10.')
        changes.append(dict(figure=r['final_name'],baseline_path=old,baseline_sha256=original[old],
                            current_sha256=r['sha256'],unchanged=original[old]==r['sha256']))
    u.write_csv(HERE/'ARTWORK_COMPARISON.csv',changes)
    text_checks=[]
    for r in manifest:
        stem=r['final_name'].removesuffix('.pdf')
        if not r['final_name'].endswith('.pdf') or stem in ['Supplement/FigS04','Supplement/FigS05']:continue
        old={'Supplement/FigS08':'Supplement/FigS09','Supplement/FigS09':'Supplement/FigS10'}.get(stem,stem)
        raw=u.payload(BASE,'results/figure_review/'+old+'.pdf')
        def body(p):
            ss=[s['text'].replace('\u00a0',' ').replace('\u00ad','-')
                for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
            return Counter(s for s in ss if not re.match(r'^[A-H]\. ',s))
        with fitz.open(stream=raw,filetype='pdf') as a,fitz.open(ROOT/r['current_source_file']) as b:
            expected,actual=body(a[0]),body(b[0])
            if stem=='Supplement/FigS03':
                expected.update(['Four focal policies','Other selected policies'])
            if stem=='Main/Fig03':
                # PDF clipping may split spans without changing their characters.
                letters=lambda c:Counter(ch for text,n in c.items() for _ in range(n) for ch in text if not ch.isspace())
                assert letters(expected)==letters(actual)
                rect=fitz.Rect(40,25,56,195)
                assert a[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=rect).samples==b[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=rect).samples
            else:
                assert expected==actual,(stem,'missing',expected-actual,'extra',actual-expected)
        text_checks.append(stem)
    book=fitz.open(ROOT/'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf')
    assert len(book)==20
    text=fitz.open(ROOT/'results/figure_review/Supplement/FigS05.pdf')[0].get_text()
    assert '0.05' in text and '0.75' in text and '0.50' in text
    assert 'C and D retain' not in text and 'Mean and 5th' not in text
    assert not (ROOT/'results/figure_review/Supplement/FigS10.pdf').exists()
    assert 'Clustering diagnostics' not in '\n'.join(p.get_text() for p in book)
    result=dict(status='PASS',baseline=BASE,scientific_authority_files_unchanged=17,
        numbered_figures=16,complete_packet_pages=20,
        packet_sha256=sha(ROOT/'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),
        removed='previous FigS08 clustering artwork; source evidence retained',
        renumbering={'previous S09':'S08','previous S10':'S09'},
        unchanged_artwork_files=sum(r['unchanged'] for r in changes))
    result['unmodified_body_text_checks']=text_checks
    if '--protected-root' in sys.argv:
        protected_root=Path(sys.argv[sys.argv.index('--protected-root')+1])
        registry=json.loads((ROOT/'docs/reproducibility/author_suite_final_layout_20261012/PRESERVATION_BEFORE.json').read_text())
        for rel,h in registry['protected_files'].items():
            assert sha(protected_root/rel)==h,rel
        assert len(registry['protected_files'])==950
        result.update(protected_scientific_files_checked=950,protected_root=str(protected_root),
                      protected_manifest_sha256=sha(ROOT/'docs/reproducibility/author_suite_final_layout_20261012/PRESERVATION_BEFORE.json'))
    u.dump(HERE/'INDEPENDENT_QA.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
