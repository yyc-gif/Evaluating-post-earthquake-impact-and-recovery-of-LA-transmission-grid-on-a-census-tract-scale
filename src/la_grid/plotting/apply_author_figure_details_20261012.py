"""Pinned, bounded PDF presentation edits. No model, data or statistic is run."""
from pathlib import Path
import hashlib, io, json, re, sys
import fitz
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, to_rgb
import consolidate_current_figure_suite as suite

ROOT = suite.ROOT
DEST = suite.DEST
BASE = '9b98e2cd571a43ab632a8d3a68c7cdd03d2d84d4'
QA = ROOT / 'docs/reproducibility/figure_details_20261012'
MM = suite.MM
NUMBER = rb'[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
RGB = re.compile(rb'(' + NUMBER + rb')\s+(' + NUMBER + rb')\s+(' + NUMBER + rb')\s+(rg|RG)\b')

def streams(doc):
    return sorted(set(doc[0].get_contents()) | {x for x in range(1, doc.xref_length())
        if doc.xref_get_key(x, 'Subtype')[1] == '/Form'})

def spans(page):
    return [s for b in page.get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)['blocks']
        for l in b.get('lines', []) for s in l['spans']]

def native(stem):
    return fitz.open(stream=suite.payload(BASE, 'results/figure_review/' + stem + '.pdf'), filetype='pdf')

def add_text(page, x, y, value, size=8, center=False):
    font = fitz.Font(fontfile='C:/Windows/Fonts/arial.ttf')
    page.insert_font(fontname='DetailArial', fontfile='C:/Windows/Fonts/arial.ttf')
    if center:
        x -= font.text_length(value, fontsize=size) / 2
    page.insert_text((x, y), value, fontsize=size, fontname='DetailArial', color=(.1,.1,.1))

def remove_text(doc, phrase):
    """Delete only a PDF text object containing the exact UTF-16 source phrase."""
    count = 0
    needle = phrase.encode('utf-16-be')
    for x in streams(doc):
        raw = doc.xref_stream(x)
        def replace(m):
            nonlocal count
            if needle in m[0]:
                count += 1
                return b''
            return m[0]
        updated = re.sub(rb'\bBT\b.*?\bET\b', replace, raw, flags=re.S)
        if updated != raw:
            doc.update_stream(x, updated)
    assert count == 1, (phrase, count)

def framework():
    d = native('Main/Fig01')
    # The visible 185 x 220 mm framework Form, not the historical clipped
    # artwork nested in its illustrations. Match all four exact original paths.
    originals = [
        b'q .35 .4 .44 RG .7 w 132.51969 385.51185 m 132.51969 357.16539 l S Q',
        b'q .35 .4 .44 rg .35 .4 .44 RG .5 w 132.51969 357.16539 m 130.8756 360.42524 l 134.16378 360.42524 l 132.51969 357.16539 l h B Q',
        b'q .35 .4 .44 RG .7 w 391.88978 385.51185 m 391.88978 357.16539 l S Q',
        b'q .35 .4 .44 rg .35 .4 .44 RG .5 w 391.88978 357.16539 m 390.24568 360.42524 l 393.53385 360.42524 l 391.88978 357.16539 l h B Q',
    ]
    joined = (b'q .35 .4 .44 RG .7 w '
        b'132.51969 385.51185 m 132.51969 371.33862 l '
        b'391.88978 385.51185 m 391.88978 371.33862 l '
        b'132.51969 371.33862 m 391.88978 371.33862 l '
        b'262.2047 371.33862 m 262.2047 357.16539 l S Q '
        b'q .35 .4 .44 rg .35 .4 .44 RG .5 w '
        b'262.2047 357.16539 m 260.56061 360.42524 l '
        b'263.84879 360.42524 l 262.2047 357.16539 l h B Q')
    found = []
    for x in streams(d):
        raw = d.xref_stream(x)
        if originals[0] not in raw:
            continue
        assert all(raw.count(s)==1 for s in originals)
        stripped = raw
        for s in originals:
            stripped = stripped.replace(s,b'')
        updated = raw.replace(originals[0], joined)
        for s in originals[1:]:
            updated = updated.replace(s,b'')
        assert updated.replace(joined,b'') == stripped
        d.update_stream(x, updated)
        found.append(x)
    # The source PDF includes the main framework and two clipped reuses.
    # Apply the same connector edit to all three identical framework Forms.
    assert len(found)==3, found
    return d, {'visible_framework_streams':found, 'original_arrows':2, 'joined_arrow':1,
        'all_nonconnector_bytes_unchanged':True, 'scientific_text_unchanged':True}

def median():
    d = native('Main/Fig03')
    remove_text(d,'Median 43.3 h')
    original = b'153.340404 180.69626 m\n160.340404 180.69626 l\n167.340404 180.69626 l\n\nS'
    count = 0
    for x in streams(d):
        raw = d.xref_stream(x)
        if original in raw:
            count += raw.count(original)
            d.update_stream(x, raw.replace(original,b''))
    assert count==1
    # Vertical median line is unchanged at x=139.573707 pt, y=422.362182 pt.
    add_text(d[0],139.573707,419.0,'Median 43.3 h',8,center=True)
    return d, {'median_hr':43.3, 'vertical_median_line_unchanged':True,
        'label_origin_pt':[139.573707,419.0], 'leader_or_horizontal_key_line':False}

def quartile_key():
    d = native('Main/Fig05')
    remove_text(d,'Thin dark outlines: Q4 areas')
    value = 'Q4 areas (highest social vulnerability)'
    font = fitz.Font(fontfile='C:/Windows/Fonts/arial.ttf')
    line, gap = 18, 6
    width = line + gap + font.text_length(value,fontsize=8)
    start = (d[0].rect.width-width)/2
    baseline = 174.9 * MM
    d[0].draw_line((start,baseline-2.5),(start+line,baseline-2.5),
        color=to_rgb('#303030'),width=.24,stroke_opacity=.75)
    add_text(d[0],start+line+gap,baseline,value,8)
    return d, {'Q4_outline_line_sample':{'color':'#303030','width_pt':.24,'opacity':.75,'length_pt':18},
        'legend_baseline_mm':174.9, 'map_heading_baseline_mm':520.296875/MM,
        'all_three_effect_maps_and_Q4_geometries_unchanged':True}

def na_gray():
    d = native('Main/Fig07')
    counts = {'map_fills':0,'legend_fills':0}
    gray = 217/255
    for x in streams(d):
        raw = d.xref_stream(x)
        def maps(m):
            counts['map_fills'] += 1
            return f'{gray:.9f} g'.encode()
        updated = re.sub(rb'(?<![0-9.])\.72\s+g\b',maps,raw)
        def legend(m):
            if all(abs(float(m[i])-.72)<1e-7 for i in [1,2,3]) and m[4]==b'rg':
                counts['legend_fills'] += 1
                return (f'{gray:.9f} {gray:.9f} {gray:.9f} rg').encode()
            return m[0]
        updated = RGB.sub(legend,updated)
        if updated != raw:
            assert re.sub(rb'(?<![0-9.])(?:\.72|0\.850980392)\s+g\b',b'NA_FILL',RGB.sub(b'COLOR',updated)) == re.sub(rb'(?<![0-9.])\.72\s+g\b',b'NA_FILL',RGB.sub(b'COLOR',raw))
            d.update_stream(x,updated)
    assert counts=={'map_fills':48,'legend_fills':1}, counts
    return d, {'N/A_fill_before':'#b8b8b8 (PDF gray 0.72)', 'N/A_fill_after':'#d9d9d9',
        'changed_operators':counts, 'cluster_colors_and_hotspot_scale_unchanged':True,
        'all_geometry_and_noncolor_bytes_unchanged':True}

def population_palette():
    d = native('Supplement/FigS10')
    t = np.linspace(0,1,256)
    old = LinearSegmentedColormap.from_list('old',['#f3f3f3','#c6c6c6','#8d8d8d'])(t)[:,:3]
    new = LinearSegmentedColormap.from_list('new',['#f3f3f3','#c6c6c6','#555555'])(t)[:,:3]
    count = 0
    touched = []
    for x in streams(d):
        raw = d.xref_stream(x)
        def change(m):
            nonlocal count
            if m[4]!=b'rg':
                return m[0]
            rgb = np.array([float(m[i]) for i in [1,2,3]])
            delta = np.max(abs(old-rgb),axis=1)
            i = int(delta.argmin())
            if delta[i]<2e-6 and i>=128:
                count += 1
                return ('%.9f %.9f %.9f rg'%tuple(new[i])).encode()
            return m[0]
        updated = RGB.sub(change,raw)
        if updated!=raw:
            assert RGB.sub(b'COLOR',updated)==RGB.sub(b'COLOR',raw)
            d.update_stream(x,updated)
            touched.append(x)
    assert count>1000, count
    images = []
    for x in range(1,d.xref_length()):
        if d.xref_get_key(x,'Subtype')[1]!='/Image':
            continue
        cs = d.xref_get_key(x,'ColorSpace')[1]
        m = re.search(r'<([0-9A-Fa-f]+)>',cs)
        if not m:
            continue
        arr = np.frombuffer(bytes.fromhex(m[1]),dtype=np.uint8).reshape(-1,3)/255
        indices = [int(np.max(abs(old-rgb),axis=1).argmin()) for rgb in arr]
        assert all(np.max(abs(old[i]-rgb))<.01 for i,rgb in zip(indices,arr))
        mapped = np.array([np.rint(new[i]*255) if i>=128 else np.rint(rgb*255)
            for i,rgb in zip(indices,arr)],dtype=np.uint8)
        before = suite.digest(d.xref_stream(x))
        d.xref_set_key(x,'ColorSpace',cs[:m.start(1)]+mapped.tobytes().hex()+cs[m.end(1):])
        assert before == suite.digest(d.xref_stream(x))
        images.append({'xref':x,'scalar_indices_sha256':before,'scalar_indices_unchanged':True})
    assert len(images)==1, images
    return d, {'C_dark_end_before':'#8d8d8d','C_dark_end_after':'#555555',
        'lower_half_colors_unchanged':True,'paint_only_streams':touched,'paint_operators':count,
        'colorbar':images,'population_values_log_normalization_and_geometry_unchanged':True}

def dividers():
    d = native('Supplement/FigS11')
    pattern = re.compile(rb'(217\.629921|458\.858268) (319\.748031|103\.91811) m\s+\1 (471\.628346|255\.798425) l\s+S\b')
    count = 0
    for x in streams(d):
        raw = d.xref_stream(x)
        updated,n = pattern.subn(b'',raw)
        count += n
        if n:
            d.update_stream(x,updated)
    assert count==4, count
    return d, {'vertical_white_dividers_removed':count,'cell_values_colors_and_uncertainty_definition_unchanged':True,
        'four_scenarios_retained':True,'reason':'Cross-scenario comparisons add evidence; a 2pc50-only version would repeat Figure 4 outcomes.'}

CHANGES = {
    'Main/Fig01':(framework,'Stages 1/2 join before a single arrow into Stage 3.'),
    'Main/Fig03':(median,'D median value centered at the upper end of its vertical median line; horizontal key removed.'),
    'Main/Fig05':(quartile_key,'E uses a real Q4-outline line sample, farther from the three map headings.'),
    'Main/Fig07':(na_gray,'Only N/A fills in C/D and their key become light gray; formal five clusters remain unchanged.'),
    'Supplement/FigS10':(population_palette,'C population palette has a darker high end; exact logarithmic scale is preserved.'),
    'Supplement/FigS11':(dividers,'Four white vertical dividers removed; four-scenario scientific purpose retained.'),
}

def export(doc,stem):
    p = doc[0]
    info = {'size_mm':[p.rect.width/MM,p.rect.height/MM], 'min_font_pt':min(s['size'] for s in spans(p)),
        'page_count':len(doc),'image_count':len(p.get_images())}
    assert abs(info['size_mm'][0]-185)<.05
    suite.write(DEST/(stem+'.pdf'),doc.tobytes(garbage=4,deflate=True))
    for dpi,path in [(600,DEST/(stem+'.png')),(160,DEST/'Page_Previews'/(Path(stem).name+'.png'))]:
        pix = p.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False)
        pix.set_dpi(dpi,dpi)
        pix.save(suite.lp(path))
    return info

def main():
    reference = json.loads(suite.payload(BASE,'docs/reproducibility/figure_suite_integration_20261011/PRESERVATION_BEFORE.json'))
    before = suite.protected_snapshot(reference)
    assert before==reference
    suite.dump(QA/'PRESERVATION_BEFORE.json',before)
    previous = json.loads(suite.payload(BASE,'docs/reproducibility/figure_suite_integration_20261011/INTEGRATION_QA.json'))
    records = previous['figures']
    info = previous['native_pdf_metrics']
    edits = {}
    for stem,(function,description) in CHANGES.items():
        doc,edit = function()
        original = native(stem)
        old_text,new_text = original[0].get_text(),doc[0].get_text()
        if stem not in ['Main/Fig03','Main/Fig05']:
            assert old_text==new_text, stem
        elif stem=='Main/Fig03':
            assert sorted(old_text.split())==sorted(new_text.split())
        else:
            normalized = lambda t:' '.join(t.split())
            assert normalized(old_text).replace('Thin dark outlines: Q4 areas (highest social vulnerability)','').split()==normalized(new_text).replace('Q4 areas (highest social vulnerability)','').split()
        original.close()
        info[stem] = export(doc,stem)
        doc.close()
        edits[stem] = edit
        print('UPDATED',stem,flush=True)
    caps = suite.payload(BASE,'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode().replace('\r\n','\n')
    caps = caps.replace('24 not-applicable tracts shown in gray as N/A','24 not-applicable tracts shown in light gray as N/A')
    caps = caps.replace(' The divider separates T80 from the loss integrals.','')
    suite.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md',caps)
    manifest = suite.csv_rows(suite.payload(BASE,'results/figure_review/FIGURE_MANIFEST.csv'))
    index = suite.csv_rows(suite.payload(BASE,'results/figures/FIGURE_INDEX.csv'))
    for row in manifest:
        stem = row['final_name'].rsplit('.',1)[0]
        row['change_in_this_update'] = 'UPDATED' if stem in CHANGES else 'RETAINED'
        row['presentation_generator'] = 'src/la_grid/plotting/apply_author_figure_details_20261012.py' if stem in CHANGES else ''
        row['presentation_generator_sha256'] = suite.sha(__file__) if stem in CHANGES else ''
        if stem in CHANGES:
            row.update(parent_source_file=row['current_source_file'],parent_source_commit=BASE,parent_sha256=row['sha256'],
                source_file=row['current_source_file'], source_commit=BASE,
                sha256=suite.sha(DEST/row['final_name']),min_font_pt=f"{info[stem]['min_font_pt']:.3f}")
            suite.write(ROOT/row['mirror_file'],open(suite.lp(DEST/row['final_name']),'rb').read())
            idx = next(r for r in index if r['source_path']==row['current_source_file'])
            idx.update(sha256_or_lfs_oid=row['sha256'],notes=CHANGES[stem][1],generator=row['presentation_generator'])
            r = next(r for r in records if r['current_file']==row['current_source_file'])
            r.update(source_commit=BASE,source_file=row['source_file'],sha256=row['sha256'],
                bytes=Path(suite.lp(DEST/row['final_name'])).stat().st_size,change='UPDATED',
                presentation_generator=row['presentation_generator'],presentation_generator_sha256=row['presentation_generator_sha256'])
        else:
            assert suite.sha(DEST/row['final_name'])==row['sha256']
    suite.write_csv(DEST/'FIGURE_MANIFEST.csv',manifest)
    suite.write_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    suite.pdfmetrics.registerFont(suite.TTFont('SuiteArial','C:/Windows/Fonts/arial.ttf'))
    suite.pdfmetrics.registerFont(suite.TTFont('SuiteBold','C:/Windows/Fonts/arialbd.ttf'))
    main_doc,supp_doc,full_doc = fitz.open(),fitz.open(),fitz.open()
    for stem,(heading,body) in zip(suite.FIGURES,suite.captions(caps).items()):
        figure = fitz.open(suite.lp(DEST/(stem+'.pdf')))
        (main_doc if stem.startswith('Main/') else supp_doc).insert_pdf(figure)
        full_doc.insert_pdf(figure)
        caption = suite.caption_pdf(heading,body)
        full_doc.insert_pdf(caption)
        figure.close();caption.close()
    old = fitz.open(stream=suite.payload(BASE,'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),filetype='pdf')
    full_doc.insert_pdf(old,from_page=38,to_page=41)
    old.close()
    for name,doc in [('ALL_MAIN_FIGURES',main_doc),('ALL_SUPPLEMENT_FIGURES',supp_doc),('ALL_FIGURES_WITH_CAPTIONS',full_doc)]:
        suite.write(DEST/(name+'.pdf'),doc.tobytes(garbage=4,deflate=True))
        doc.close()
    log = ['# Current figure update — 2026-10-12','',f'Artwork source: `{BASE}`.','',
        'All current figures remain in this single directory on the revision branch. Changes in this round:', '',
        '| Figure | Action | Change |','|---|---|---|']
    for stem in suite.FIGURES:
        action = 'UPDATED' if stem in CHANGES else 'RETAINED'
        message = CHANGES[stem][1] if stem in CHANGES else 'Exact current artwork retained.'
        log.append(f'| [{Path(stem).name}]({stem}.pdf) | {action} | {message} |')
    log += ['', 'S11 retains four earthquake scenarios. Figure 4 already presents the 2pc50 recovery and the same three service-loss outcomes plus T80. Reducing S11 to 2pc50 would remove its cross-scenario evidence and duplicate that main figure. No merger is justified in this round. Historical cases are not interpreted as a pure hazard-intensity experiment.', '',
        'The N/A category means no residential typology, including eight positive-population tracts without housing units; it is not renamed “No residents.” The reference to 7Z is applied to the hotspot map, 7D. Cluster colors and S9 remain identical to the preceding suite.', '',
        'Captions, 600-dpi exports, publication-size previews, all three review packets and results/figures mirrors are synchronized. All numerical values, model outputs, quartiles, cluster assignments and hotspot ranks remain unchanged. Detailed operator checks and preservation records: docs/reproducibility/figure_details_20261012. Prior changes remain traceable in Git.']
    suite.write(DEST/'UPDATE_LOG.md','\n'.join(log)+'\n')
    readme = suite.payload(BASE,'results/figure_review/README.md').decode()
    readme += '\nLatest update (2026-10-12): Figure 1 joined connector, Figure 3D median label, Figure 5E line key and spacing, Figure 7C/D light-gray N/A, S10C darker high end, and S11 divider removal. All other numbered artwork is retained. See UPDATE_LOG.md.\n'
    suite.write(DEST/'README.md',readme)
    after = suite.protected_snapshot(reference)
    assert before==after
    suite.dump(QA/'PRESERVATION_AFTER.json',after)
    audit = {'baseline_commit':BASE,'figures':records,'native_pdf_metrics':info,
        'operator_edits':edits,'updated_figures':list(CHANGES),'retained_figures':[s for s in suite.FIGURES if s not in CHANGES],
        'scientific_results_recomputed':False,'original_worktree_unchanged':before==after,
        'protected_file_count':before['protected_count'],'staged_item_count':before['staged_count'],
        'packet_pages':{'main':7,'supplement':12,'with_captions':42}}
    suite.dump(QA/'INTEGRATION_QA.json',audit)
    print('COMPLETE six bounded edits; 19 numbered figures; three unified packets; original worktree preserved.',flush=True)

def inspect():
    for stem in ['Main/Fig01', 'Main/Fig03', 'Main/Fig05', 'Main/Fig07', 'Supplement/FigS10', 'Supplement/FigS11']:
        d = native(stem)
        print(stem, 'size', tuple(round(v / MM, 3) for v in (d[0].rect.width, d[0].rect.height)), flush=True)
        for s in spans(d[0]):
            if any(t in s['text'] for t in ['Median', 'Thin dark', 'Compared with', 'N/A', 'Damage-to-Service']):
                print(s['text'], s['origin'], flush=True)
        for x in streams(d):
            raw = d.xref_stream(x)
            if stem == 'Main/Fig01' and len(raw) > 10000:
                print('STREAM', x, len(raw), raw[:10000].decode('latin1'), flush=True)
                break
            if stem in ['Main/Fig03', 'Supplement/FigS11']:
                needles = [b'139.573', b'1.2 w', b'1 1 1 RG', b'3.7 1.6']
                for n in needles:
                    for m in list(re.finditer(re.escape(n), raw))[:6]:
                        print('PATH', x, raw[max(0, m.start()-100):m.end()+150].decode('latin1'), flush=True)
            if stem == 'Main/Fig07' and len(raw)>100000:
                colors = {}
                for m in RGB.finditer(raw):
                    rgb = tuple(round(float(m[i]), 5) for i in [1,2,3])
                    if max(rgb)-min(rgb)<.00001 and .5 < rgb[0] < .95:
                        colors[rgb] = colors.get(rgb,0)+1
                print('GRAY', x, colors, flush=True)
        d.close()

if __name__ == '__main__':
    inspect() if '--inspect' in sys.argv else main()
