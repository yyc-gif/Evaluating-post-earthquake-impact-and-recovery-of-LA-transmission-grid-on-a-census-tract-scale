"""Read-only scientific extraction and final artwork preflight; no model runs."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import subprocess
import sys

import fitz
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u

DEST = ROOT / 'docs/reproducibility/figure_scientific_publication_review_20261111'
SUITE = ROOT / 'results/figure_review_s6_main4_20261107'
BASE = '96367fe564e065933e828d82afd2b5a8909b84e5'


def extract_event():
    from audit_s5_vulnerability_extension import DEFAULT_ARCHIVE
    folder = DEFAULT_ARCHIVE / 'Formal_Trajectories/2pc50/C57_D1/impact-first'
    stem = '2pc50__evaluation_0000'
    raw = (folder / (stem + '.npz')).read_bytes()
    task_raw = (folder / (stem + '__TASK_EVENTS.csv')).read_bytes()
    record = json.loads((folder / (stem + '.json')).read_text())
    assert u.digest(raw) == record['npz_sha256']
    assert u.digest(task_raw) == record['task_events_sha256']
    assert record['identity']['mapping_method_id'] == 'M1_UTILITY_003'
    source = 'Data/JULY_UTILITY_CONSTRAINED_92.csv'
    mapping_raw = u.payload('75cd19d4a0249d006efa00d4532762d0ee406c5a', source)
    mapping = pd.read_csv(io.BytesIO(mapping_raw), dtype={'tract_id': str, 'substation_id': str})
    tasks = pd.read_csv(io.BytesIO(task_raw), dtype={'task_id': str})
    event = tasks.loc[tasks.task_id.eq('300558')].iloc[0]
    assert int(event.crew_index) == 4
    # Highest dependency weight, then lowest GEOID: a declared representative,
    # not an invented spatial state or a typical-tract claim.
    example = mapping.loc[mapping.substation_id.eq('300558')].sort_values(
        ['weight', 'tract_id'], ascending=[False, True]).iloc[0]
    with np.load(io.BytesIO(raw), allow_pickle=False) as a:
        ids = a['station_ids'].astype(str)
        j = list(ids).index('300558')
        t = a['event_time_hr']
        finish = int(np.argmin(abs(t - event.completion_hr)))
        assert abs(t[finish] - event.completion_hr) < 1e-10
        connected = int(np.flatnonzero((t >= t[finish]) & (a['C'][:, j] == 1))[0])
        ix = [finish - 1, finish, connected]
        w = mapping.loc[mapping.tract_id.eq(example.tract_id)].set_index('substation_id').weight.reindex(ids).fillna(0).to_numpy()
        assert abs(w.sum() - 1) < 1e-12 and w[j] == 1
        service = a['e'][ix] @ w
        values = [a['f'][ix, j].tolist(), a['C'][ix, j].tolist(), service.tolist()]
        assert values == [[.03, 1., 1.], [0., 0., 1.], [0., 0., 1.]]
        np.testing.assert_array_equal(a['F'], a['f']>=.5)
        np.testing.assert_allclose(a['f'] * a['F'] * a['C'], a['e'], atol=1e-12, rtol=0)
        output = dict(identity=record['identity'], station_id='300558',
            tract_id=str(example.tract_id), tract_dependency_weight=float(w[j]),
            crew_number=5, completion_hr=float(t[finish]), source_connection_hr=float(t[connected]),
            archived_state_times_hr=t[ix].tolist(), columns=['Before', 'Repair', 'Connected'],
            rows=['Raw function', 'Source link', 'Tract service'], values=values,
            crew_released_at_completion=True, next_task_start_hr=float(
                tasks.loc[tasks.crew_index.eq(4)].sort_values('completion_hr').iloc[1].crew_available_before_hr),
            source_archive=str(folder / (stem + '.npz')), source_npz_sha256=u.digest(raw),
            source_manifest_sha256=u.sha(folder / (stem + '.json')),
            task_events_sha256=u.digest(task_raw), mapping_source=source,
            mapping_commit='75cd19d4a0249d006efa00d4532762d0ee406c5a', mapping_sha256=u.digest(mapping_raw),
            selection='First shown crew, first task; maximum dependency weight then lowest GEOID',
            no_gate_or_schedule_rerun=True)
    assert abs(output['completion_hr'] - output['next_task_start_hr']) < 1e-10
    u.dump(DEST / 'EVENT_STATE_EXAMPLE.json', output)
    print(json.dumps(output, indent=2))


def audit():
    records = []
    preview_dir=ROOT/'tmp/pdfs/publication_review'
    preview_dir.mkdir(parents=True,exist_ok=True)
    for p in sorted(SUITE.glob('Main/*.pdf')) + sorted(SUITE.glob('Supplement/*.pdf')):
        with fitz.open(p) as doc:
            page = doc[0]
            text = [s for b in page.get_text('dict')['blocks'] for l in b.get('lines', [])
                    for s in l['spans'] if s['text'].strip()]
            pix = page.get_pixmap(dpi=150, alpha=False)
            pix.save(str(preview_dir/(p.stem+'.png')))
            rgb = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
            yy, xx = np.where(np.any(rgb < 245, axis=2))
            baseline = u.payload(BASE, p.relative_to(ROOT).as_posix())
            records.append(dict(figure=p.stem, source_file=p.relative_to(ROOT).as_posix(),
                width_mm=page.rect.width*25.4/72, height_mm=page.rect.height*25.4/72,
                visible_margins_mm=dict(left=float(xx.min()*25.4/150), right=float((pix.width-1-xx.max())*25.4/150),
                    top=float(yy.min()*25.4/150), bottom=float((pix.height-1-yy.max())*25.4/150)),
                min_text_pt=min(s['size'] for s in text), fonts=sorted({s['font'] for s in text}),
                text_below_7pt=[s['text'] for s in text if s['size']<6.99],
                clipped_text=[s['text'] for s in text if not (page.rect+(-.5,-.5,.5,.5)).contains(fitz.Rect(s['bbox']))],
                vector_forms=len(page.get_xobjects()), raster_objects=len(page.get_images()),
                unembedded_fonts=[font[3] for font in page.get_fonts() if not doc.extract_font(font[0])[3]],
                sha256=u.sha(p), baseline_sha256=u.digest(baseline), unchanged=u.digest(baseline)==u.sha(p)))
    u.dump(DEST/'ARTWORK_METRICS.json', dict(baseline=BASE, figures=records,
        note='Ink threshold 245 at 150 dpi; visible margins are measured, not journal requirements. Font extraction includes inherited thumbnail labels.'))
    print(json.dumps([dict(figure=r['figure'],min_pt=round(r['min_text_pt'],2),
        size_mm=[round(r['width_mm'],1),round(r['height_mm'],1)],clipped=r['clipped_text'],
        margins={k:round(v,1) for k,v in r['visible_margins_mm'].items()}) for r in records],indent=2))


def verify_damage_boxes():
    from audit_s5_vulnerability_extension import DEFAULT_ARCHIVE
    from matplotlib.cbook import boxplot_stats
    folder=DEFAULT_ARCHIVE/'Stage 1 Output_expanded'
    manifest=json.loads((folder/'PHYSICAL_INPUTS_FROZEN.json').read_text())
    with fitz.open(SUITE/'Main/Fig03.pdf') as doc:
        caps=set()
        for d in doc[0].get_cdrawings():
            for item in d['items']:
                if item[0]!='l':continue
                (x0,y0),(x1,y1)=item[1:]
                if 83<x0<230 and 50<y0<171 and abs(y0-y1)<1e-5 and 12<abs(x1-x0)<12.5:
                    caps.add((round((x0+x1)/2,5),round(y0,5)))
    centers=sorted({x for x,y in caps});assert len(centers)==4
    # Calibrated from the PDF's y=1 and y=4 tick marks; no scientific plot changes.
    scale=(144.87844848632812-52.11663818359375)/3
    zero=144.87844848632812+scale
    records=[]
    for h,cx in zip(['LongBeach','SanFernando','Northridge','2pc50'],centers):
        p=folder/f'physical_inputs_{h}.npz'
        assert u.sha(p)==manifest['files_sha256'][h]
        with np.load(p,allow_pickle=False) as a:
            assert a['evaluation_ds'].shape==(92,1000)
            means=a['evaluation_ds'].mean(axis=1)
        stats=boxplot_stats(means,whis=(5,95))[0]
        expected=[float(stats['whislo']),float(stats['whishi'])]
        observed=sorted((zero-y)/scale for x,y in caps if x==cx)
        assert len(observed)==2
        error=float(np.max(abs(np.array(expected)-observed)))
        assert error<1e-5
        records.append(dict(hazard=h,source=str(p),source_sha256=u.sha(p),
            stations=92,realizations=1000,median=float(stats['med']),
            expected_whiskers=expected,pdf_whiskers=observed,max_abs_error=error))
    u.dump(DEST/'DAMAGE_BOXPLOT_QA.json',dict(statistical_unit='station mean over 1000 evaluation realizations',
        whiskers='observed values within the 5th-95th station-percentile interval',records=records))
    print(json.dumps(records,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--extract-event', action='store_true')
    parser.add_argument('--verify-damage-boxes', action='store_true')
    args=parser.parse_args()
    if args.extract_event:extract_event()
    elif args.verify_damage_boxes:verify_damage_boxes()
    else:audit()
