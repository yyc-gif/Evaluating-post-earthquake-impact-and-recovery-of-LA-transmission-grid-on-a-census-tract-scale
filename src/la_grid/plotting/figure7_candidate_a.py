"""Approved Candidate A: frozen empirical plots and surgical vector-map reuse."""
import io
import re

import fitz
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

import consolidate_current_figure_suite as u

MM = 72 / 25.4
A_FEATURES = ['Grid_Impact', 'Redundancy_HHI', 'B_Unconstrained', 'MeanDelta',
              'SOVI_SCORE', 'FEMA_NCV14_CA_v119']
COLORS = ['#147f98', '#d07734', '#7a5899']
STYLES = ['-', '--', ':']
NA_OUTLINE = '#777777'
NA_WIDTH = .45
TOKEN = re.compile(rb'\((?:\\.|[^\\)])*\)|%[^\r\n]*|<[^<>]*>|/[^\s\[\]()<>/%]+|[^\s\[\]()<>/%]+|[\[\]<>]', re.S)
INSERT_BEFORE = b'q\n1 g\n0.4666666667 G\n0.45 w\n'
INSERT_AFTER = b'\nQ'


def is_na(drawing):
    return drawing.get('fill') is not None and max(abs(v - 229 / 255) for v in drawing['fill']) < 2e-4


def paint_na(doc):
    """Add local graphics-state overrides at N/A paints; never rewrite paths."""
    before = doc[0].get_cdrawings()
    assert sum(is_na(d) for d in before) == 34
    streams = []
    total = 0
    for xref in doc[0].get_contents():
        original = doc.xref_stream(xref)
        state, stack, operands, patches = (0., 0., 0.), [], [], []
        in_text = False
        for token in TOKEN.finditer(original):
            value = token.group()
            if value.startswith((b'(', b'%', b'<', b'/')):
                continue
            if value == b'BT':
                in_text = True
            elif value == b'ET':
                in_text = False
            if in_text:
                continue
            try:
                operands.append(float(value))
                continue
            except ValueError:
                pass
            if value == b'q':
                stack.append(state)
            elif value == b'Q':
                state = stack.pop()
            elif value == b'g':
                state = (operands[-1],) * 3
            elif value == b'rg':
                state = tuple(operands[-3:])
            elif value in [b'B', b'B*', b'f', b'f*', b'b', b'b*']:
                if max(abs(v - 229 / 255) for v in state) < 1e-7:
                    patches.append((token.start(), token.end()))
            operands.clear()
        revised = original
        for start, end in reversed(patches):
            revised = revised[:start] + INSERT_BEFORE + revised[start:end] + INSERT_AFTER + revised[end:]
        stripped = re.sub(re.escape(INSERT_BEFORE) + rb'(B\*?|f\*?|b\*?)' + re.escape(INSERT_AFTER),
                          rb'\1', revised)
        assert stripped == original
        if patches:
            doc.update_stream(xref, revised)
        total += len(patches)
        streams.append({'xref': xref, 'paint_overrides': len(patches),
            'original_stream_sha256': u.digest(original),
            'stripped_revised_stream_sha256': u.digest(stripped), 'all_original_stream_bytes_preserved': True})
    assert total == 34
    after = doc[0].get_cdrawings()
    assert len(before) == len(after)
    changed = []
    for i, (old, new) in enumerate(zip(before, after)):
        if is_na(old):
            assert new['fill'] == (1., 1., 1.)
            assert abs(new['width'] - NA_WIDTH) < 1e-6
            assert max(abs(v - 119/255) for v in new['color']) < 2e-4
            assert {k:v for k,v in old.items() if k not in ['fill', 'color', 'width']} == {
                k:v for k,v in new.items() if k not in ['fill', 'color', 'width']}
            assert old['rect'][1] > 132 * MM
            changed.append(i)
        else:
            assert old == new, ('Non-N/A vector changed', i)
    assert len(changed) == 34
    return {'authorized_NA_drawings': 34, 'map_polygons': 32, 'legend_swatches': 2,
        'fill': '#FFFFFF', 'outline': NA_OUTLINE, 'outline_width_pt': NA_WIDTH,
        'path_geometry_and_all_other_vector_properties_exact': True,
        'non_NA_vectors_exact': True, 'changed_drawing_indices': changed, 'content_streams': streams}


def approved_top(f, means, features, qa):
    """Literal approved review layout, omitting only the review-only warning."""
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 8, 'axes.labelsize': 8,
        'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5, 'axes.spines.top': False,
        'axes.spines.right': False, 'pdf.fonttype': 42, 'axes.linewidth': .6})
    width, height = 185, 253
    fig = plt.figure(figsize=(width / 25.4, height / 25.4))
    ft = lambda x, y, s, **kw: fig.text(x / width, 1 - y / height, s, **kw)
    ft(5, 11, 'A. Feature distributions across the saved K3 classes', fontsize=9.5, weight='bold')
    handles = [Line2D([0], [0], color=color, ls=line, lw=1.3,
                     label=f'C{c} (n={n:,})') for c, n, color, line in zip([1,2,3], [1242,475,582], COLORS, STYLES)]
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(5 / width, 1 - 14 / height),
               ncol=3, frameon=False, fontsize=8, columnspacing=2.4, handlelength=2.0, borderaxespad=0)
    titles = ['RQ1: Spectral grid impact', 'RQ1: Dependency concentration',
              'RQ2: Unconstrained deficit', 'RQ2: Constraint increment',
              'RQ3: Social vulnerability', 'RQ3: Natural-hazard screen']
    labels = ['Grid impact (unitless)', 'HHI (unitless)', 'Equivalent deficit hours',
              'Five-policy mean increment (h)', 'SOVI score (0-100)', 'NCV14 screening index (unitless)']
    limits = [(0,1), (0,1), (19,44), (0,20), (0,100), (.3,1)]
    points, medians = [], []
    for j, feature in enumerate(A_FEATURES):
        row, col = divmod(j, 3)
        x, top, w, h = 17 + col * 59, 28 + row * 37, 42, 23
        ax = fig.add_axes([x/width, 1-(top+h)/height, w/width, h/height])
        lo, hi = limits[j]
        for c, color, line in zip([1,2,3], COLORS, STYLES):
            values = f.loc[f['class'].eq(c), feature].to_numpy()
            assert values.min() >= lo-1e-12 and values.max() <= hi+1e-12
            unique, counts = np.unique(values, return_counts=True)
            cumulative = np.cumsum(counts) / len(values)
            points.extend({'variable': feature, 'class': 'C'+str(c), 'class_n': len(values),
                'value': float(v), 'value_count': int(n), 'cumulative_fraction': float(cf)}
                for v,n,cf in zip(unique, counts, cumulative))
            medians.append({'variable': feature, 'class': 'C'+str(c), 'median': float(np.median(values)),
                            'marker_y': .5, 'n': len(values), 'zero_count': int((values == 0).sum())})
            ax.step(np.r_[lo,unique,hi], np.r_[0,cumulative,1], where='post', color=color, ls=line, lw=1.1)
            ax.plot(np.median(values), .5, 'o', color=color, ms=3)
        ax.axhline(.5, color='#a9a9a9', lw=.5, zorder=0)
        ax.set_xlim(lo,hi); ax.set_ylim(0,1.03)
        ax.set_yticks([0,.5,1]); ax.locator_params(axis='x', nbins=3)
        ax.set_title(titles[j], fontsize=8.5, pad=3)
        ax.set_xlabel(labels[j], fontsize=7.5, labelpad=2)
        if col == 0:
            ax.set_ylabel('Cumulative fraction', fontsize=7.5, labelpad=2)
        ax.tick_params(length=2.2, pad=1.5)
    ft(5,97,'Exact empirical CDFs; dots locate class medians on the 50% guide. No smoothing or trimming.',fontsize=7.5)
    ft(5,103,'B. Standardized eight-coordinate class profiles',fontsize=9.5,weight='bold')
    ft(5,108,'Unweighted z means; zero = 2,299-tract mean.',fontsize=7.5)
    ax = fig.add_axes([74/width,1-139/height,66/width,28/height])
    maximum = np.ceil(abs(means).max()*10)/10
    im = ax.pcolormesh(np.arange(4)-.5, np.arange(9)-.5, means.T,
                      cmap='RdBu_r', vmin=-maximum, vmax=maximum, shading='flat', rasterized=False)
    ax.set_xlim(-.5,2.5); ax.set_ylim(7.5,-.5)
    ax.set_xticks([0,1,2],['C1','C2','C3']); ax.xaxis.tick_top()
    for label,color in zip(ax.get_xticklabels(),COLORS):
        label.set_color(color); label.set_weight('bold'); label.set_fontsize(8)
    ax.set_yticks(range(8), ['Initial service','Spectral grid impact','Dependency HHI','Unconstrained deficit',
                'Constraint increment','SOVI score','log1p(Population)','NCV14 screening index'])
    ax.tick_params(axis='y',labelsize=7.5,length=0,pad=4); ax.tick_params(axis='x',length=0,pad=2)
    for split in [2.5,4.5]:
        ax.axhline(split,color='white',lw=1)
    for j in range(8):
        for c in range(3):
            ax.text(c,j,f'{means[c,j]:+.2f}',ha='center',va='center',fontsize=7.5,
                    color='white' if abs(means[c,j])>.8*maximum else '#202020')
    for top,bottom,label in [(111,121.5,'RQ1'),(121.5,128.5,'RQ2'),(128.5,139,'RQ3')]:
        ft(7,(top+bottom)/2+.8,label,fontsize=8,weight='bold')
    cb=fig.colorbar(im,cax=fig.add_axes([151/width,1-139/height,3/width,28/height]))
    cb.solids.set_rasterized(False); cb.set_ticks([-1,0,1])
    cb.ax.tick_params(labelsize=7.5,length=2,pad=2)
    cb.set_label('Class-mean z-score',fontsize=7.5,labelpad=3)
    out=io.BytesIO()
    fig.savefig(out,format='pdf',metadata={'CreationDate':None,'ModDate':None,
        'Subject':'Author-approved Candidate A; frozen NCV14/H2/K3, no model fit',
        'Creator':'build_current_suite_k3.py / approved Candidate A'})
    plt.close(fig)
    u.write_csv(qa/'ECDF_POINTS.csv',points)
    u.write_csv(qa/'ECDF_MEDIANS.csv',medians)
    u.write_csv(qa/'PROFILE_CELLS.csv',[{'class':'C'+str(c+1),'variable':field,
        'ordinary_z_mean':float(means[c,j]),'printed_value':f'{means[c,j]:+.2f}'}
        for j,field in enumerate(features) for c in range(3)])
    return fitz.open(stream=out.getvalue(),filetype='pdf')


def render(f, means, features, current_bytes, qa):
    doc=approved_top(f,means,features,qa)
    old=fitz.open(stream=current_bytes,filetype='pdf')
    current=fitz.open(stream=current_bytes,filetype='pdf')
    paint=paint_na(current)
    clip=fitz.Rect(0,132*MM,current[0].rect.width,current[0].rect.height)
    target=clip+(0,8*MM,0,8*MM)
    doc[0].show_pdf_page(target,current,0,clip=clip,keep_proportion=False)
    assert abs(target.width/clip.width-1)<1e-12 and abs(target.height/clip.height-1)<1e-12
    u.dump(qa/'NA_VECTOR_PAINT_QA.json',paint)
    u.dump(qa/'CD_TRANSLATION_QA.json',{'source_clip_pt':list(clip),'target_rect_pt':list(target),
        'translation_mm':[0,8],'scale':1,'geometry_regenerated':False,'map_source_SHA256':u.digest(current_bytes),
        'original_stream_bytes_exact_after_removing_authorized_local_style_overrides':True})
    old.close();current.close()
    return doc
