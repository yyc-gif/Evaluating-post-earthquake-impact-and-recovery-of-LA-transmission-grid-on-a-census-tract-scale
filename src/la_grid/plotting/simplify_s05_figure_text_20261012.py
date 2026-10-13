"""Edit S05 vector text/keys only; never execute a scientific evaluator.

Input is the pinned, already integrated vector artwork. Scientific paths,
numerical labels and uncertainty intervals remain byte-identical in its source
content streams. New streams contain only replacement text and legend glyphs.
"""
from pathlib import Path
import io
import json
import re
import subprocess
import sys

import fitz
import consolidate_current_figure_suite as util
from integrate_final_s05_and_suite_review_20261012 import pdf_info, streams

BASE = 'f010a4b42ebb7b160ab78556405bdb5c8e8a3ef6'
ROOT = util.ROOT
DEST = ROOT / 'results/figure_review'
QA = ROOT / 'docs/reproducibility/s05_plain_figure_labels_20261012'
PRIOR_QA = ROOT / 'docs/reproducibility/official_figure_suite_review_20261012'
STEM = 'Supplement/FigS05'
SCRIPT = 'src/la_grid/plotting/simplify_s05_figure_text_20261012.py'
TEXT = re.compile(rb'BT\b.*?\bET', re.S)
LITERAL = re.compile(rb'\((?:\\.|[^\\()])*\)', re.S)


def literal_value(raw):
    raw = raw[1:-1]
    def unescape(m):
        value = m[1]
        if value[:1] in b'01234567':
            return bytes([int(value, 8)])
        return {b'n': b'\n', b'r': b'\r', b't': b'\t', b'b': b'\b',
                b'f': b'\f', b'\r\n': b'', b'\n': b'', b'\r': b''}.get(value, value)
    raw = re.sub(rb'\\([0-7]{1,3}|\r\n|.)', unescape, raw, flags=re.S)
    return raw.decode('utf-16-be')


def text_value(block):
    return ''.join(literal_value(m[0]) for m in LITERAL.finditer(block))


def source(rel):
    data = util.payload(BASE, rel)
    sources[BASE + ':' + rel] = {'sha256': util.digest(data), 'bytes': len(data)}
    return data


sources = {}


def plain_font(page, doc, name, path):
    xref = page.insert_font(fontname=name, fontfile=path)
    font = fitz.Font(fontfile=path)
    # Arial has duplicate Unicode aliases for several glyphs. Explicitly map
    # the ASCII labels so copied/searchable PDF text does not acquire NBSP,
    # soft hyphens or a Greek question mark in place of ordinary punctuation.
    pairs = []
    for code in range(32, 127):
        glyph = font.has_glyph(code)
        assert glyph > 0
        pairs.append(f'<{glyph:04x}> <{code:04x}>')
    cmap = ('/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n'
            '/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n'
            '/CMapName /PlainLabelUnicode def\n/CMapType 2 def\n'
            '1 begincodespacerange\n<0000> <ffff>\nendcodespacerange\n'
            f'{len(pairs)} beginbfchar\n'+'\n'.join(pairs)+'\nendbfchar\n'
            'endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n')
    cx = doc.get_new_xref()
    doc.update_object(cx, '<<>>')
    doc.update_stream(cx, cmap.encode('ascii'))
    doc.xref_set_key(xref, 'ToUnicode', f'{cx} 0 R')
    return font


def edit_s05(data):
    d = fitz.open(stream=data, filetype='pdf')
    page = d[0]
    spans = [s for b in page.get_text('dict', flags=0)['blocks']
             for line in b.get('lines', []) for s in line['spans']]
    replacements = {
        'A. Pure-random search convergence': 'A. GA search progress',
        'B. Initial and final search outcomes': 'B. Initial and final planning loss',
        'D. Population-loss accounting': 'D. Service-loss components',
        '20 optimizer seeds; 64 fixed planning realizations': '20 runs; 64 planning realizations',
        '20 paired initial/final seed observations': 'Initial and final loss for 20 runs',
        '2,000 new physical realizations; frozen legacy GA': '2,000 paired validation realizations',
        '20 independent runs': '20 GA runs',
        'Median best-observed archive': 'Median best-so-far loss',
        'Impact-first (reference only)': 'Impact-first',
        'Best-observed planning loss (h)': 'Best planning service loss (h)',
        'Planning loss (h)': 'Planning service loss (h)',
        'Mean service-loss difference (h)': 'Change from Impact-first (h)',
    }
    removed = {
        'Selected seed: 2026103108', 'Final: 32.995522 h',
        'Same 2,000 realizations; GA minus Impact-first',
        'Strict proximity: 10/20 (90% criterion not met).',
        'Post-data method choice; no universal reliability.',
        'Blue: reduced loss   Red: increased loss',
        'Net benefit is dominated by source-path loss.',
        'Legacy pure-random GA; no incumbent injection. Finite-budget evidence, not global optimality.',
    }
    expected = set(replacements) | removed
    assert expected <= {s['text'] for s in spans}
    edits = []
    found = []
    for xref in streams(d):
        raw = d.xref_stream(xref)
        def change(m):
            value = text_value(m[0])
            if value in expected:
                found.append(value)
                return b''
            return m[0]
        changed = TEXT.sub(change, raw)
        if changed != raw:
            assert TEXT.sub(b'', raw) == TEXT.sub(b'', changed)
            old_text = [text_value(m[0]) for m in TEXT.finditer(raw)]
            new_text = [text_value(m[0]) for m in TEXT.finditer(changed)]
            assert new_text == [t for t in old_text if t not in expected]
            d.update_stream(xref, changed)
            edits.append({'source_xref': xref,
                          'source_stream_sha256': util.digest(raw),
                          'edited_stream_sha256': util.digest(changed),
                          'unchanged_graphics_sha256': util.digest(TEXT.sub(b'', raw)),
                          'all_other_text_unchanged': True})
    assert sorted(found) == sorted(expected), (found, expected)
    font = plain_font(page, d, 'PlainArial', 'C:/Windows/Fonts/arial.ttf')
    plain_font(page, d, 'PlainBold', 'C:/Windows/Fonts/arialbd.ttf')
    for span in spans:
        old = span['text']
        if old not in replacements:
            continue
        text = replacements[old]
        title = old.startswith(('A.', 'B.', 'D.'))
        size = 9.5 if title else max(8, span['size'])
        p = fitz.Point(span['origin'])
        if old in ['Best-observed planning loss (h)', 'Planning loss (h)']:
            # Keep the original vertical-axis center and orientation.
            center_y = (span['bbox'][1] + span['bbox'][3]) / 2
            p.y = center_y + font.text_length(text, fontsize=size) / 2
            page.insert_text(p, text, fontsize=size, fontname='PlainArial', rotate=90, color=(0, 0, 0))
        else:
            if old == 'Mean service-loss difference (h)':
                center_x = (span['bbox'][0] + span['bbox'][2]) / 2
                p.x = center_x - font.text_length(text, fontsize=size) / 2
            page.insert_text(p, text, fontsize=size,
                             fontname='PlainBold' if title else 'PlainArial', color=(0, 0, 0))
    blue = (40/255, 91/255, 121/255)
    red = (182/255, 79/255, 63/255)
    ink = (48/255, 58/255, 64/255)
    # Use an actual diamond in the B key, matching the selected-run glyph.
    p = fitz.Point(402, 59.2)
    diamond = [p+(-2.2, 0), p+(0, -2.2), p+(2.2, 0), p+(0, 2.2), p+(-2.2, 0)]
    shape = page.new_shape()
    shape.draw_polyline(diamond)
    shape.finish(color=blue, fill=blue, width=.5, closePath=True)
    shape.commit()
    page.insert_text((409, 61.6), 'Selected run: 32.995522 h', fontsize=8,
                     fontname='PlainArial', color=(0, 0, 0))
    # D key sits directly below its heading, not below the plotted panel.
    x, y = 325.2, 286.9
    for color, label in [(blue, 'Decrease'), (red, 'Increase'), (ink, 'Net change')]:
        page.draw_rect(fitz.Rect(x, y-5.5, x+7, y+.5), color=color, fill=color, width=.4)
        page.insert_text((x+10, y), label, fontsize=8, fontname='PlainArial', color=(0, 0, 0))
        x += 10 + font.text_length(label, fontsize=8) + 13
    assert x < page.rect.width - 5
    # The removed footer leaves only white space below the axis labels.
    # Trim that blank margin while preserving all chart coordinates and width.
    page.set_cropbox(fitz.Rect(0, 0, page.rect.width, 472))
    out = d.tobytes(garbage=4, deflate=True)
    info = pdf_info(d)
    d.close()
    return out, info, {'removed_or_replaced_text': found, 'replacement_text': replacements,
                       'legend_keys': ['Selected run (diamond)', 'Decrease (blue)',
                                       'Increase (red)', 'Net change (charcoal)'],
                       'core_stream_invariance': edits,
                       'blank_footer_margin_trimmed_to_page_height_pt': 472,
                       'curves_bars_points_axes_intervals_and_numerical_labels_unchanged': True,
                       'no_scientific_evaluator_executed': True}


def replace_pages(data, replacement):
    old = fitz.open(stream=data, filetype='pdf')
    out = fitz.open()
    for i in range(len(old)):
        if i in replacement:
            out.insert_pdf(replacement[i])
        else:
            out.insert_pdf(old, from_page=i, to_page=i)
    assert len(out) == len(old)
    result = out.tobytes(garbage=4, deflate=True)
    old.close()
    out.close()
    return result


def main():
    reference = json.load(open(util.lp(PRIOR_QA/'PRESERVATION_AFTER.json'), encoding='utf-8'))
    before = util.protected_snapshot(reference)
    assert before == reference, 'Protected original worktree changed before this edit'
    util.dump(QA/'PRESERVATION_BEFORE.json', before)
    util.dump(QA/'STARTING_STATE.json', {'HEAD': util.git('rev-parse', 'HEAD').decode().strip(),
              'branch': util.git('branch', '--show-current').decode().strip(),
              'starting_tracked_status': util.git('status', '--short', '--untracked-files=no').decode(),
              'input_commit': BASE})
    rel = 'results/figure_review/' + STEM + '.pdf'
    data, info, edit = edit_s05(source(rel))
    util.write(ROOT/rel, data)
    renderer = PRIOR_QA/'render_one.py'
    subprocess.run([sys.executable, str(renderer), str(ROOT/rel),
                    str(DEST/(STEM+'.png')), str(DEST/'Page_Previews/FigS05.png')], check=True)
    old_caps = util.captions(source('results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    key = next(h for h in old_caps if h.startswith('Supplementary Figure S5.'))
    body = old_caps[key].replace('pure-random genetic algorithm', 'randomly initialized genetic algorithm')
    body = body.replace('Impact-first is a reference only, not an inserted chromosome.',
                        'Impact-first was used only for comparison; it was not included in the initial population.')
    body = body.replace('Pure-random initialization', 'Random initialization')
    body = body.replace('population burden', 'population-weighted service loss')
    body = body.replace('burden disparity', 'service-loss disparity')
    new_key = 'Supplementary Figure S5. GA search and independent validation'
    caps = {new_key if h == key else h: body if h == key else b for h, b in old_caps.items()}
    assert len(caps) == 19
    assert all(caps[h] == b for h, b in old_caps.items() if h != key)
    util.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md', '# Manuscript-facing figure captions\n\n' +
               '\n\n'.join('## '+h+'\n\n'+b for h,b in caps.items())+'\n')
    old_manifest = util.csv_rows(source('results/figure_review/FIGURE_MANIFEST.csv'))
    index = util.csv_rows(source('results/figures/FIGURE_INDEX.csv'))
    manifest = []
    for old in old_manifest:
        row = old.copy()
        row['change_in_this_update'] = 'RETAINED'
        if row['final_name'].rsplit('.',1)[0] == STEM:
            ext = row['final_name'].rsplit('.',1)[1]
            row.update(source_file=old['current_source_file'], source_commit=BASE,
                       parent_source_file=old['current_source_file'], parent_source_commit=BASE,
                       parent_sha256=old['sha256'], sha256=util.sha(ROOT/old['current_source_file']),
                       size_mm=' x '.join(f'{v:.3f}' for v in info['size_mm']),
                       min_font_pt=f"{info['min_font_pt']:.3f}",
                       change_in_this_update='UPDATED', presentation_generator=SCRIPT,
                       presentation_generator_sha256=util.sha(__file__))
            util.write(ROOT/row['mirror_file'], open(util.lp(ROOT/row['current_source_file']), 'rb').read())
            idx = next(r for r in index if r['source_path'] == row['current_source_file'])
            idx.update(generator=SCRIPT, sha256_or_lfs_oid=row['sha256'],
                       scientific_question='What do randomly initialized GA searches and independent validation show?',
                       main_message='Search progress and paired validation; scientific quantities retained.',
                       notes='S05 display text simplified; real color/marker keys replace panel footnotes.')
        else:
            assert row['sha256'] == util.sha(ROOT/row['current_source_file'])
            source(row['current_source_file'])
        manifest.append(row)
    util.write_csv(DEST/'FIGURE_MANIFEST.csv',manifest)
    util.write_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    util.pdfmetrics.registerFont(util.TTFont('SuiteArial','C:/Windows/Fonts/arial.ttf'))
    util.pdfmetrics.registerFont(util.TTFont('SuiteBold','C:/Windows/Fonts/arialbd.ttf'))
    figure = fitz.open(stream=data, filetype='pdf')
    caption = util.caption_pdf(new_key, body)
    util.write(DEST/'ALL_SUPPLEMENT_FIGURES.pdf', replace_pages(
        source('results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf'), {3:figure}))
    util.write(DEST/'ALL_FIGURES_WITH_CAPTIONS.pdf', replace_pages(
        source('results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'), {20:figure,21:caption}))
    figure.close(); caption.close()
    assert util.sha(DEST/'ALL_MAIN_FIGURES.pdf') == util.digest(source('results/figure_review/ALL_MAIN_FIGURES.pdf'))
    records = [{'current_file':r['current_source_file'],'source_file':r['source_file'],
                'source_commit':r['source_commit'],'sha256':r['sha256'],
                'mirror_file':r['mirror_file'],'change':r['change_in_this_update']} for r in manifest]
    after = util.protected_snapshot(reference)
    assert before == after
    util.dump(QA/'PRESERVATION_AFTER.json',after)
    prior = json.load(open(util.lp(PRIOR_QA/'INTEGRATION_QA.json'), encoding='utf-8'))
    util.dump(QA/'INTEGRATION_QA.json', {'baseline_commit':BASE,'figures':records,
              'updated_figures':[STEM],'retained_figures':[s for s in util.FIGURES if s != STEM],
              'operator_edits':{STEM:edit}, 'prior_round_operator_evidence':prior['operator_edits'],
              'native_pdf_metrics':{STEM:info},'packet_pages':{'main':7,'supplement':12,'with_captions':42},
              'scientific_results_recomputed':False,'original_worktree_unchanged':before==after,
              'manuscripts_modified':False,'protected_file_count':950,'staged_item_count':862})
    util.dump(QA/'SOURCE_HASHES.json',sources)
    print('S05 figure text and keys updated; 18 other figures retained exactly.', flush=True)


if __name__ == '__main__':
    main()
