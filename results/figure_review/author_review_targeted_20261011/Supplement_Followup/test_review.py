"""Check retained scientific values, map geometry, and packet readability."""
from pathlib import Path
import sys, re, json, hashlib
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common as c
import numpy as np
import pandas as pd
from matplotlib.colors import SymLogNorm
from PIL import Image
P=Path(__file__).resolve().parent

def read(name):
    with open(c.lp(P/name), encoding='utf-8') as f:return json.load(f)

def doc(name, before=False):
    return c.fitz.open(c.lp(P/('before/'+name+'.pdf' if before else name+'_Candidate.pdf')))

def pixels(d, box):
    # 254 dpi = ten pixels/mm, making the 7-mm map translation exact.
    pix=d[0].get_pixmap(matrix=c.fitz.Matrix(254/72,254/72),
        clip=c.fitz.Rect(*[v*c.MM for v in box]),alpha=False)
    return np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)

def test_source_identity():
    for rel,record in read('SOURCE_HASHES.json').items():
        f=Path(record['actual_local_path']) if 'actual_local_path' in record else c.source(rel)[0]
        assert c.sha(f)==record['sha256'],rel
    for name in ['FigS03','FigS06','FigS07','FigS10','FigS11']:
        assert c.sha(P/'before'/f'{name}.pdf')==c.source(f'results/figure_review/Supplement/{name}.pdf')[1]

def test_s03_matrix_and_transparency():
    with doc('FigS03',True) as a,doc('FigS03') as b:
        assert not re.search(r'\b\d{6}\b',b[0].get_text())
        # Geographic path geometry remains identical; alpha changes visibility.
        old_drawings=a[0].get_drawings();new_drawings=b[0].get_drawings()
        old=[tuple(round(v,3) for v in d['rect']) for d in old_drawings if d['rect'].y1<110*c.MM]
        new=[tuple(round(v,3) for v in d['rect']) for d in new_drawings if d['rect'].y1<110*c.MM]
        assert old==new
        assert any(abs(d['fill_opacity']-.62)<1e-5 for d in new_drawings)
        # Native PDFs contain earlier, clipped form copies. The final mesh is
        # the last 92*92 quadrilaterals, rather than all hidden form paths.
        def mesh(drawings):
            return [q for q in drawings if q['fill'] is not None and
              2<q['rect'].width<4 and 2<q['rect'].height<4 and q['rect'].y0>110*c.MM
              and all(item[0]=='l' for item in q['items'])][-92*92:]
        left=mesh(old_drawings);right=mesh(new_drawings)
        assert len(left)==len(right)==92*92
        np.testing.assert_array_equal([q['fill'] for q in left],[q['fill'] for q in right])
        np.testing.assert_allclose([list(q['rect']) for q in left],[list(q['rect']) for q in right],rtol=0,atol=.0001)
    record=read('ARTWORK_EDIT_RECORDS.json')['FigS03']
    assert record['full_directed_matrix_display_preserved']
    t=pd.read_csv(c.lp(c.source('data/travel/travel_task_to_task.csv')[0]),index_col=0)
    assert t.shape==(92,92)
    assert float(abs(t.values-t.values.T).max())==record['max_directional_difference_h']

def test_s06_retained_data_and_joint_gate_definition():
    with doc('FigS06',True) as a,doc('FigS06') as b:
        for box in [(60,9,181,58),(38,74,178,125),(6,130,184,203)]:
            np.testing.assert_array_equal(pixels(a,box),pixels(b,box))
    r=read('S06_GATE_DESIGN_AUDIT.json')
    assert r['combined_removal']=='e = f'
    assert not r['isolated_threshold_removal_available'] and not r['isolated_source_removal_available']
    assert not r['new_gate_evaluation_performed']
    registered=json.load(open(c.lp(c.source('docs/reproducibility/SUPPLEMENT_ASSUMPTIONS_LAYOUT_UPDATE_20261006.json')[0]),encoding='utf-8'))
    actual=next(x for x in registered if x.get('file')=='Supplement/FigS06.pdf')
    assert r['displayed_statistics']==actual['displayed_summary']

def test_s07_all_curve_values_legends_and_static_maps():
    r=read('S07_DISPLAYED_VALUES.json')
    t=pd.read_csv(c.lp(c.source('results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv')[0]))
    for row in r['displayed_rows']:
        actual=t.loc[t.strategy.eq(row['strategy'])&t.time_hr.eq(row['time_hr']),row['field']].item()
        assert row['value']==actual
    for view in r['legend_identities']:
        for panel in ['A','B']:
            curves={x['strategy'] for x in r['displayed_rows'] if x['view']==view['view'] and x['panel']==panel}
            assert curves==set(view['policy_legend'])==set(view['policy_curves'])
        assert not view['markers_in_legend']
    with doc('FigS07',True) as a,doc('FigS07') as b:
        # Compare vector positions/colors directly. Tiny float rounding in a
        # copied PDF form can change antialiasing at edges, but not the paths.
        def maps(d,dy):
            return [q for q in d[0].get_drawings() if q['rect'].y0>=149*c.MM+dy and q['rect'].y1<=207*c.MM+dy]
        left=maps(a,0);right=maps(b,7*c.MM)
        assert len(left)==len(right)
        assert [(q['fill'],q['color'],q['width']) for q in left]==[(q['fill'],q['color'],q['width']) for q in right]
        # Float32 coordinates and serialized form matrices are allowed 0.001
        # point (<0.00036 mm) rounding, never a scientific-value tolerance.
        np.testing.assert_allclose([list(q['rect']) for q in left],
          [[r[0],r[1]-7*c.MM,r[2],r[3]-7*c.MM] for r in [q['rect'] for q in right]],rtol=0,atol=.001)

def test_s10_only_population_colors_changed():
    with doc('FigS10',True) as a,doc('FigS10') as b:
        np.testing.assert_array_equal(pixels(a,(0,0,185,176)),pixels(b,(0,0,185,176)))
        assert a[0].get_text()==b[0].get_text()
        def paths(d):
            return [(tuple(x['rect']),str(x['items']),x['width']) for x in d[0].get_drawings()]
        assert paths(a)==paths(b)
        def image_indices(d):
            return Counter(hashlib.sha256(d.xref_stream(x[0])).hexdigest() for x in d[0].get_images())
        assert image_indices(a)==image_indices(b)

def test_s11_exact_values_and_common_nonclipping_scale():
    r=read('S11_DISPLAYED_VALUES.json')
    t=pd.read_csv(c.lp(c.source('provenance/figure_review_history/candidate_v2.1/CROSS_HAZARD_POLICY_EFFECTS.csv')[0]))
    for h,values in zip(r['hazards'],r['values']):
        for strategy,row in zip(r['policy_order'],values):
            for metric,v in zip(r['fields'],row):
                assert v==t.loc[t.hazard.eq(h)&t.strategy_id.eq(strategy)&t.metric.eq(metric),'mean_paired_difference'].item()
    with doc('FigS11',True) as a,doc('FigS11') as b:
        annotations=lambda d:Counter(re.findall(r'[+]\d+\.\d{2}',d[0].get_text()))
        assert annotations(a)==annotations(b)
        assert sum(annotations(b).values())==96
    limit=float(np.abs(r['values']).max())
    assert r['same_hour_limits']==[-limit,limit]
    assert not r['outliers_clipped'] and not r['metric_or_hazard_specific_rescaling']
    norm=SymLogNorm(.1,vmin=-limit,vmax=limit,base=10)
    assert norm(0)==.5 and norm(-limit)==0 and norm(limit)==1
    assert np.all(np.diff(norm(np.linspace(-limit,limit,1001)))>0)

def test_native_width_fonts_preview_and_caption_packet():
    for name in ['FigS03','FigS06','FigS07','FigS10','FigS11']:
        with doc(name) as d:
            p=d[0];assert abs(p.rect.width/c.MM-185)<1e-3
            assert min(s['size'] for s in c.spans(p))>=6.99
            assert all(p.rect.contains(c.fitz.Rect(s['bbox'])) for s in c.spans(p))
            with Image.open(c.lp(P/(name+'_Candidate.png'))) as im:
                assert abs(im.info['dpi'][0]-600)<.1
                assert abs(im.width-185/25.4*600)<2
    captions=(P/'PROPOSED_CAPTIONS.md').read_text(encoding='utf-8')
    bodies=[m.split('\n\n',1)[1].strip() for m in captions.split('\n## ')[1:]]
    # The embedded Arial cmap maps semicolon to Greek question mark and ASCII
    # hyphen to soft hyphen; normalize only these known glyph equivalents.
    normalize=lambda x:re.sub(r'\s+','',x).replace('\u00a0','').replace('\xad','-').replace('\u037e',';')
    with c.fitz.open(c.lp(P/'COMBINED_TARGETED_AUTHOR_REVIEW.pdf')) as d:
        assert len(d)==22
        for i,body in zip([13,15,17,19,21],bodies):
            assert normalize(body) in normalize(d[i].get_text())
            assert min(s['size'] for s in c.spans(d[i]))>=10
            assert all(d[i].rect.contains(c.fitz.Rect(s['bbox'])) for s in c.spans(d[i]))
    with c.fitz.open(c.lp(P/'NATIVE_SUPPLEMENT_BEFORE_AFTER.pdf')) as d:
        assert len(d)==5
        assert all(abs(p.rect.width/c.MM-410)<.001 for p in d)
