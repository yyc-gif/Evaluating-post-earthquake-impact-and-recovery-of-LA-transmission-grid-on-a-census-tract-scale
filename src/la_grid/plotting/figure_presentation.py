"""Presentation-only changes to existing vector artwork, without redrawing data."""
import hashlib
import io
import json
import re
from pathlib import Path
from collections import Counter

import fitz

_HEADING_OFFSETS={}


def spans(page):
    return [s for b in page.get_text('dict')['blocks'] for line in b.get('lines', []) for s in line['spans']]


def vector_signature(page):
    drawings=[{k:repr(v) for k,v in d.items() if k not in ['seqno','layer']} for d in page.get_drawings()]
    return hashlib.sha256(json.dumps(drawings,sort_keys=True).encode()).hexdigest()


def fonts(doc, bold, required):
    candidates=[]
    for row in doc[0].get_fonts():
        if ('Bold' in row[3])!=bold:
            continue
        raw=doc.extract_font(row[0])[3]
        if not raw:
            continue
        font=fitz.Font(fontbuffer=raw)
        if all(font.has_glyph(ord(c)) for c in required if not c.isspace()):
            candidates.append((hashlib.sha256(raw).hexdigest(),raw,font))
    if not candidates:
        path=Path('C:/Windows/Fonts')/('arialbd.ttf' if bold else 'arial.ttf')
        raw=path.read_bytes()
        font=fitz.Font(fontbuffer=raw)
        assert all(font.has_glyph(ord(c)) for c in required if not c.isspace())
        return raw,font
    return sorted(candidates,key=lambda v:v[0])[0][1:]


def remove(page, selected):
    before=vector_signature(page)
    key=lambda s:(s['text'].replace('\u00a0',' '),tuple(round(x,3) for x in s['origin']))
    excluded={key(s) for s in selected}
    expected=[s for s in spans(page) if key(s) not in excluded]
    expected_keys=Counter(key(s) for s in expected)
    for s in selected:
        page.add_redact_annot(fitz.Rect(s['bbox'])+(-.03,-.03,.03,.03),fill=None)
    page.apply_redactions(images=0,graphics=0)
    # Compound source PDFs can share text runs across clipping forms. Restore
    # any untouched legend displaced by redaction at its exact original origin.
    extra=Counter(key(s) for s in spans(page))-expected_keys
    for s in spans(page):
        if extra[key(s)]:
            page.add_redact_annot(fitz.Rect(s['bbox']),fill=None)
            extra[key(s)]-=1
    if sum(extra.values())==0:
        page.apply_redactions(images=0,graphics=0)
    actual=Counter(key(s) for s in spans(page))
    for s in expected:
        k=key(s)
        if actual[k]:
            actual[k]-=1
            continue
        bold='Bold' in s['font'];name='RestoredBold' if bold else 'RestoredBody'
        path=Path('C:/Windows/Fonts')/('arialbd.ttf' if bold else 'arial.ttf')
        page.insert_font(fontname=name,fontfile=str(path))
        page.insert_text(s['origin'],s['text'],fontname=name,fontsize=s['size'],
                         color=fitz.sRGB_to_pdf(s['color']))
    missing=expected_keys-Counter(key(s) for s in spans(page))
    assert not missing, ('An untouched label was lost',missing)
    assert vector_signature(page)==before, 'A text correction changed a scientific vector'
    return before


def title(page, text, x, top, font, center=False):
    # Use one complete, explicitly embedded face. Reusing a subset extracted
    # from nested historical forms can give CID-coded gibberish after grafting.
    raw=Path('C:/Windows/Fonts/arialbd.ttf').read_bytes()
    metrics=fitz.Font(fontbuffer=raw)
    page.insert_font(fontname='CurrentPanelHeading14',fontbuffer=raw)
    if center:
        if text not in _HEADING_OFFSETS:
            with fitz.open() as probe:
                p=probe.new_page(width=1000,height=40)
                p.insert_font(fontname='CurrentPanelHeading14',fontbuffer=raw)
                p.insert_text((10,20),text,fontname='CurrentPanelHeading14',fontsize=9.5)
                boxes=[s['bbox'] for s in spans(p)]
                _HEADING_OFFSETS[text]=(min(b[0] for b in boxes)+max(b[2] for b in boxes))/2-10
        x-=_HEADING_OFFSETS[text]
    page.insert_text((x,top+metrics.ascender*9.5),text,fontname='CurrentPanelHeading14',fontsize=9.5,color=(0,0,0))


def tile(page, doc, rect, dy=0):
    rect=fitz.Rect(rect)
    page.show_pdf_page(rect+(0,dy,0,dy),doc,0,clip=rect,keep_proportion=False)


def finish(doc):
    return doc.tobytes(garbage=4,deflate=True,no_new_id=True)


def figure5(raw):
    with fitz.open(stream=raw,filetype='pdf') as source:
        p=source[0];w,h=p.rect.width,p.rect.height
        old=[s for s in spans(p) if s['text'][:3] in [f'{c}. ' for c in 'ABCDE']
             or s['text'][:3] in [f'{c}.\u00a0' for c in 'ABCDE']]
        assert len(old)==5
        labels={s['text'][0]:s['text'].replace('\u00a0',' ').replace('\u00ad','-') for s in old}
        font=fonts(source,True,''.join(labels.values()))
        signature=remove(p,old)
        out=fitz.open();page=out.new_page(width=w,height=h)
        tile(page,source,(0,0,w,55),6)
        tile(page,source,(0,70,w,254),-8)
        tile(page,source,(0,281,w,451))
        tile(page,source,(0,484,w,502),8.5)
        tile(page,source,(0,511,w,h))
        positions={'A':64.,'B':64.,'C':268.1,'D':268.1,'E':471.0}
        for s in old:
            code=s['text'][0]
            title(page,labels[code],(s['bbox'][0]+s['bbox'][2])/2,positions[code],font,center=True)
        result=finish(out);out.close()
        return result,dict(scientific_vectors_unchanged=signature,
            translations_pt=dict(top_legend=6,AB=-8,CD=0,E_maps=0,E_legend=8.5),
            title_top_pt=positions,AB_to_CD_gap_pt=268.1-(252.1-8),CD_to_E_gap_pt=471.0-446.8752,
            font_pt=9.5,width_pt=w,height_pt=h)


def figure7(raw):
    with fitz.open(stream=raw,filetype='pdf') as source:
        p=source[0];w,h=p.rect.width,p.rect.height
        texts=spans(p)
        removed=[s for s in texts if s['text'].startswith((
            'A. Feature distributions','B. Seven-coordinate','C. Saved seven-variable',
            'D. Recovery burden','Exact empirical CDFs;','Ordinary feature z means,',
            '2,299 tracts;','P2 model IDs;','Finite five-policy comparison.',
            'Descriptive co-occurrence;','Frozen SOVI','Q4 and deficit >= frozen P75'))]
        assert len(removed)==12,len(removed)
        labels=['A. Feature distributions','B. Profiles','C. Community types',
                'D. Recovery burden and social vulnerability']
        font=fonts(source,True,''.join(labels))
        body,metrics=fonts(source,False,'SOVI quartileQ4 and deficit >= P75')
        signature=remove(p,removed)
        p.insert_font(fontname='MapLegend',fontbuffer=body)
        for original,new,rotation in [('Frozen SOVI','SOVI quartile',90),
                                      ('Q4 and deficit >= frozen P75','Q4 and deficit >= P75',0)]:
            s=next(s for s in removed if s['text']==original)
            p.insert_text(s['origin'],new,fontname='MapLegend',fontsize=7.5,rotate=rotation)
        out=fitz.open();page=out.new_page(width=w,height=h)
        tile(page,source,(0,30,w,265),-8)
        tile(page,source,(0,302,w,408),-14)
        tile(page,source,(0,416,w,641),7)
        positions=[(12.96,10.4),(12.96,276.5),(23.328,412.7),(277.344,412.7)]
        for text,(x,y) in zip(labels,positions):title(page,text,x,y,font)
        result=finish(out);out.close()
        return result,dict(scientific_vectors_unchanged=signature,
            translations_pt=dict(A=-8,B=-14,CD=7),titles=labels,
            A_to_B_gap_pt=276.5-(264.4724-8),B_to_CD_gap_pt=412.7-(406.6855-14),
            embedded_explanatory_notes_removed=6,font_pt=9.5,width_pt=w,height_pt=h,
            scientific_arrays_and_classification_reused=True)


def figure8_shared_map_legend(raw, class_colors):
    """Give the K3 map and bivariate map their own aligned legends."""
    import numpy as np

    d_label='Outlined: Q4 + deficit ≥38.4 h'
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        width,height=page.rect.width,page.rect.height
        assert abs(width-518.4)<.01 and abs(height-684.0)<.01
        source_text=' '.join(s['text'].replace('\u00a0',' ').replace('\u00ad','-')
                             for s in spans(page))
        assert source_text.count('N/A (16)')==2
        assert source_text.count('Q4 + burden >= P75')==1
        body,_=fonts(doc,False,d_label)
        old_labels=[]
        for span in spans(page):
            text=span['text'].replace('\u00a0',' ').replace('\u00ad','-')
            top_row=580<=span['bbox'][1] and span['bbox'][3]<=605
            bottom_row=627<=span['bbox'][1] and span['bbox'][3]<=645
            if (top_row and text in {'C1','C2','C3','N/A (16)'}) or (
                    bottom_row and text in {'Q4 + burden >= P75','N/A (16)'}):
                old_labels.append(span)
        assert Counter(s['text'].replace('\u00a0',' ').replace('\u00ad','-')
                       for s in old_labels)==Counter(
                           {'C1':1,'C2':1,'C3':1,'N/A (16)':2,'Q4 + burden >= P75':1})
        for span in old_labels:
            page.add_redact_annot(fitz.Rect(span['bbox'])+(-.03,-.03,.03,.03),fill=None)
        page.apply_redactions(images=0,graphics=0)
        # These bands contain only the two old legend rows; the bivariate
        # gradient and its axis labels remain outside the masked regions.
        old_legend_bands=[fitz.Rect(35,580,248,605),fitz.Rect(15,627,210,645)]
        for band in old_legend_bands:
            page.draw_rect(band,color=None,fill=(1,1,1),overlay=True)

        page.insert_font(fontname='Figure8SharedLegend',fontbuffer=body)
        metrics=fitz.Font(fontbuffer=body)
        fontsize=7.5
        baseline=height-26.0
        c_items=[('fill','C1',class_colors['1'],8.0),
                 ('fill','C2',class_colors['2'],8.0),
                 ('fill','C3',class_colors['3'],8.0),
                 ('na','N/A (16)','#333333',12.0)]
        c_gap=9.0
        c_widths=[symbol+4.0+metrics.text_length(text,fontsize)
                  for _,text,_,symbol in c_items]
        c_total=sum(c_widths)+c_gap*(len(c_items)-1)
        cursor=(254.0-c_total)/2
        c_positions=[]
        for (kind,text,color,symbol_width),item_width in zip(c_items,c_widths):
            text_x=cursor+symbol_width+4.0
            if kind=='fill':
                page.draw_rect(fitz.Rect(cursor,baseline-7.2,cursor+symbol_width,baseline+0.3),
                               color=None,fill=tuple(int(color[i:i+2],16)/255 for i in (1,3,5)),
                               overlay=True)
            else:
                page.draw_rect(fitz.Rect(cursor,baseline-7.2,cursor+symbol_width,baseline+0.3),
                               color=(51/255,51/255,51/255),fill=(1,1,1),width=.45,overlay=True)
            page.insert_text((text_x,baseline),text,fontname='Figure8SharedLegend',
                             fontsize=fontsize,color=(.08,.08,.08),overlay=True)
            c_positions.append({'label':text,'x0':cursor,'x1':cursor+item_width,
                                'baseline':baseline,'group':'C'})
            cursor+=item_width+c_gap

        d_width=14.0+5.0+metrics.text_length(d_label,fontsize)
        cursor=264.0+(width-264.0-d_width)/2
        page.draw_line(fitz.Point(cursor,baseline-3.5),
                       fitz.Point(cursor+14.0,baseline-3.5),
                       color=(85/255,85/255,85/255),width=.8,overlay=True)
        page.insert_text((cursor+19.0,baseline),d_label,
                         fontname='Figure8SharedLegend',fontsize=fontsize,
                         color=(.08,.08,.08),overlay=True)
        d_positions=[{'label':d_label,'x0':cursor,'x1':cursor+d_width,
                      'baseline':baseline,'group':'D'}]
        positions=c_positions+d_positions

        after_text=' '.join(s['text'].replace('\u00a0',' ').replace('\u00ad','-')
                            for s in spans(page))
        assert after_text.count('N/A (16)')==1
        assert 'P75' not in after_text
        assert d_label in after_text
        assert max(item['x1'] for item in c_positions)<254
        assert min(item['x0'] for item in d_positions)>264
        assert all(item['baseline']==baseline for item in positions)

        with fitz.open(stream=raw,filetype='pdf') as before:
            before_pix=before[0].get_pixmap(dpi=120,alpha=False)
        after_pix=page.get_pixmap(dpi=120,alpha=False)
        before_rgb=np.frombuffer(before_pix.samples,dtype=np.uint8).reshape(
            before_pix.height,before_pix.width,3)
        after_rgb=np.frombuffer(after_pix.samples,dtype=np.uint8).reshape(
            after_pix.height,after_pix.width,3)
        assert before_rgb.shape==after_rgb.shape
        scale=120/72
        allowed=[*old_legend_bands,fitz.Rect(0,644,width,height)]
        outside=np.ones(before_rgb.shape[:2],dtype=bool)
        for band in allowed:
            x0=max(0,round(band.x0*scale)-2);x1=min(outside.shape[1],round(band.x1*scale)+2)
            y0=max(0,round(band.y0*scale)-2);y1=min(outside.shape[0],round(band.y1*scale)+2)
            outside[y0:y1,x0:x1]=False
        unchanged=bool(np.array_equal(before_rgb[outside],after_rgb[outside]))
        assert unchanged
        result=finish(doc)
    with fitz.open(stream=result,filetype='pdf') as output:
        figure_png=output[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
        preview_png=output[0].get_pixmap(dpi=150,alpha=False).tobytes('png')
    return result,figure_png,preview_png,{
            'legend_entries':{'C':['C1','C2','C3','N/A (16)'],
                              'D':[d_label]},
        'old_NA_entries':2,'new_NA_entries':1,'P75_shorthand_removed':True,
            'screening_rule_text':d_label,'screening_symbol':'thin gray line',
        'class_colors':class_colors,'font_size_pt':fontsize,
        'shared_baseline_pt_from_bottom':26.0,
            'C_and_D_legends_separate_and_aligned':True,
            'all_legend_entries_share_baseline':True,
        'bivariate_colorbar_and_tract_geometry_unchanged':unchanged,
        'whiteout_bands_pt':[[r.x0,r.y0,r.x1,r.y1] for r in old_legend_bands],
        'shared_legend_positions':positions,
    }


def supplementary8(raw):
    output, palette_audit = priority_geography(raw)
    return output,dict(population_color_audit=palette_audit,
        text_and_nonpopulation_content_unchanged=True)


def supplementary5_four_policy(plot_data_bytes):
    """Plot the saved four-policy mapping, source-gate and threshold contrasts."""
    import json
    import matplotlib
    matplotlib.use('Agg', force=True)
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.lines import Line2D

    data=json.loads(plot_data_bytes)
    assert data['schema']=='S5_FOUR_POLICY_SENSITIVITY_V1'
    assert data['realizations']==1000
    policies=[item['id'] for item in data['policies']]
    assert policies==['impact-first','hospital-first','degree-first','vulnerability-first']
    names=[item['name'] for item in data['policies']]
    records=data['series']

    font_manager.fontManager.addfont('C:/Windows/Fonts/arial.ttf')
    font_manager.fontManager.addfont('C:/Windows/Fonts/arialbd.ttf')
    with matplotlib.rc_context({
        'font.family':'Arial','font.size':7.2,'pdf.fonttype':42,
        'ps.fonttype':42,'axes.linewidth':0.45,
        'xtick.major.width':0.45,'ytick.major.width':0.45,
    }):
        fig=plt.figure(figsize=(185/25.4,210/25.4),facecolor='white')
        axes=[fig.add_axes([.305,.705,.66,.195]),
              fig.add_axes([.305,.395,.66,.195]),
              fig.add_axes([.305,.085,.66,.195])]
        y_positions={policy:3-i for i,policy in enumerate(policies)}
        neutral='#405a72'
        secondary='#8a6380'

        def format_axis(ax,title,xlabel,xlim,xticks):
            ax.set_title(title,loc='left',fontsize=9.2,fontweight='bold',pad=5.0)
            ax.set_xlim(*xlim);ax.set_xticks(xticks)
            ax.set_ylim(-.45,3.45)
            ax.set_yticks([3,2,1,0]);ax.set_yticklabels(names,fontsize=7.2)
            ax.set_xlabel(xlabel,fontsize=7.5,labelpad=2.6)
            ax.tick_params(axis='x',labelsize=7.0,length=2.3,pad=1.8)
            ax.tick_params(axis='y',length=0,pad=5.0)
            ax.grid(axis='x',color='#e0e4e7',linewidth=.45)
            ax.set_axisbelow(True)
            ax.axvline(0,color='#777777',linewidth=.65,linestyle=(0,(3,2)),zorder=0)
            ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#68737a');ax.spines['bottom'].set_color('#68737a')

        def draw_range(ax,row,y,marker,color,offset=0.0):
            mean=row['mean_gap_h'];low=row['p05_gap_h'];high=row['p95_gap_h']
            assert low<=mean<=high
            ax.errorbar(mean,y+offset,
                xerr=[[mean-low],[high-mean]],fmt=marker,color=color,ecolor=color,
                markersize=3.6,elinewidth=.75,capsize=2.0,capthick=.7,zorder=3)

        ax=axes[0]
        format_axis(ax,'A. Mapping-weight cutoff',
                    'Burden change from 3% cutoff (h)',(-.25,1.35),[-.2,0,.4,.8,1.2])
        for policy in policies:
            rows=[r for r in records if r['panel']=='A' and r['policy']==policy]
            assert len(rows)==2
            for row in rows:
                if row['control']=='M1_UTILITY_NO_CUTOFF':
                    draw_range(ax,row,y_positions[policy], 'o',neutral,.13)
                elif row['control']=='M1_UTILITY_001':
                    draw_range(ax,row,y_positions[policy], 's',secondary,-.13)
                else:
                    raise AssertionError(row['control'])
        ax.legend(handles=[
            Line2D([],[],marker='o',linestyle='none',color=neutral,markersize=3.7,label='0% cutoff'),
            Line2D([],[],marker='s',linestyle='none',color=secondary,markersize=3.7,label='1% cutoff')],
            loc='upper right',bbox_to_anchor=(1,-.18),ncol=2,frameon=False,
            fontsize=6.6,handletextpad=.35,columnspacing=.8,borderaxespad=.25)

        ax=axes[1]
        format_axis(ax,'B. Source-connectivity gate',
                    'Gate off minus baseline burden (h)',(-7.4,.5),[-6,-4,-2,0])
        for policy in policies:
            row=next(r for r in records if r['panel']=='B' and r['policy']==policy)
            draw_range(ax,row,y_positions[policy],'o',neutral)

        ax=axes[2]
        format_axis(ax,'C. Functionality threshold',
                    'Burden change from 0.50 threshold (h)',(-.20,.06),[-.2,-.15,-.1,-.05,0,.05])
        for policy in policies:
            rows=[r for r in records if r['panel']=='C' and r['policy']==policy]
            assert len(rows)==2
            for row in rows:
                if row['threshold']==.05:
                    draw_range(ax,row,y_positions[policy],'o',neutral,.13)
                elif row['threshold']==.75:
                    draw_range(ax,row,y_positions[policy],'s',secondary,-.13)
                else:
                    raise AssertionError(row['threshold'])
        ax.legend(handles=[
            Line2D([],[],marker='o',linestyle='none',color=neutral,markersize=3.7,label='0.05'),
            Line2D([],[],marker='s',linestyle='none',color=secondary,markersize=3.7,label='0.75')],
            loc='upper right',bbox_to_anchor=(1,-.20),ncol=2,frameon=False,
            fontsize=6.6,handletextpad=.35,columnspacing=.8,borderaxespad=.25)

        out=io.BytesIO()
        fig.savefig(out,format='pdf',bbox_inches=None,
                    metadata={'CreationDate':None,'ModDate':None,
                              'Creator':'Frozen four-policy sensitivity post-processing'})
        plt.close(fig)
    with fitz.open(stream=out.getvalue(),filetype='pdf') as doc:
        pdf=finish(doc)
        with fitz.open(stream=pdf,filetype='pdf') as final:
            png=final[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
            preview=final[0].get_pixmap(dpi=150,alpha=False).tobytes('png')
            assert abs(final[0].rect.width-524.40945)<.02
            assert abs(final[0].rect.height-595.2756)<.02
            text=' '.join(final[0].get_text().split())
            for value in ('Impact-first','Hospital-first','Degree-first','Vulnerability-first',
                          '0% cutoff','1% cutoff','0.05','0.75',
                          'A. Mapping-weight cutoff','B. Source-connectivity gate',
                          'C. Functionality threshold'):
                assert value in text,value
            assert '5th' not in text and 'confidence interval' not in text.lower()
    return pdf,png,preview,{
        'source_plot_data_sha256':hashlib.sha256(plot_data_bytes).hexdigest(),
        'four_policies_in_all_three_panels':True,
        'policy_labels':names,
        'all_ranges_are_paired_5th_95th_percentiles':True,
        'range_is_not_a_confidence_interval':True,
        'source_off_keeps_functionality_threshold_050':True,
        'threshold_panels_reevaluate_source_connectivity':True,
        'width_mm':185.0,'height_mm':210.0,
        'axes_count':3,'no_recovery_model_or_schedule_rerun':True,
    }


def restoration_workflow(raw):
    """Replace Figure 1 Stage 4 with the repair-completion update process."""
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        w,h=page.rect.width,page.rect.height
        all_spans=spans(page)
        title_text='Restoration Strategies and Execution'
        assert any(' '.join(s['text'].replace('\u00a0',' ').split())==title_text
                   for s in all_spans)
        old=[s for s in all_spans
             if 9.5<s['bbox'][0]<258 and 481<s['bbox'][1]<614]
        old_text={' '.join(s['text'].replace('\u00a0',' ').replace('\u00ad','-')
                            .replace('\u037e',';').split()) for s in old}
        assert {'Unconstrained reference',
                'Repairs proceed in parallel using sampled durations.',
                'Constrained restoration','Priority strategy sets repair order.',
                'Finite crews; dispatch includes directed travel and repairs.',
                'Repair completion: station functionality = 1',
                'Source gate + tract weights','Modeled service availability curves'}.issubset(old_text),old_text
        # Text-only redaction keeps the surrounding scientific artwork intact.
        for span in old:
            page.add_redact_annot(fitz.Rect(span['bbox']),fill=None)
        page.apply_redactions(images=0,graphics=0)
        white=(1.,1.,1.)
        ink=(32/255,40/255,43/255)
        page.draw_rect(fitz.Rect(9.5,481.7,256.3,614.7),color=None,fill=white,overlay=True)
        page.insert_font(fontname='Fig1RestorationBold',fontfile='C:/Windows/Fonts/arialbd.ttf')
        page.insert_font(fontname='Fig1RestorationBody',fontfile='C:/Windows/Fonts/arial.ttf')

        def label(text,x,y,size=7.5,bold=False,color=ink):
            page.insert_text((x,y),text,
                fontname='Fig1RestorationBold' if bold else 'Fig1RestorationBody',
                fontsize=size,color=color,overlay=True)

        label('Unconstrained restoration',17.0,495.0,6.7,True)
        label('Repairs proceed in parallel.',17.0,505.2,7.0)
        label('No finite-crew or travel limits.',17.0,514.0,7.0)
        label('Constrained restoration strategies',140.0,495.0,7.0,True)
        label('Priority order with finite crews.',140.0,505.2,7.0)
        label('Dispatch includes directed travel.',140.0,514.0,7.0)
        page.draw_line(fitz.Point(132.0,487.8),fitz.Point(132.0,519.0),
                       color=(0.82,0.85,0.86),width=0.45,overlay=True)
        page.draw_line(fitz.Point(15.5,522.0),fitz.Point(250.0,522.0),
                       color=(0.82,0.85,0.86),width=0.45,overlay=True)
        label('At each repair-completion event',15.5,532.0,7.0,True)

        boxes=[(15.5,'Repair\ncompletes'),(75.0,'Station\nfunction set\nto 1'),
               (134.5,'Re-evaluate\nsource\nconnectivity'),(194.0,'Update tract\nservice\nthrough W')]
        box_width=53.0; top=539.0; bottom=581.0
        for x,text in boxes:
            page.draw_rect(fitz.Rect(x,top,x+box_width,bottom),
                           color=(.56,.62,.65),fill=(.98,.99,.99),
                           width=.55,overlay=True)
            lines=text.split('\n')
            line_y=top+(bottom-top-(len(lines)-1)*8.4)/2+2.2
            for line_text in lines:
                text_width=fitz.Font(fontfile='C:/Windows/Fonts/arial.ttf').text_length(
                    line_text,fontsize=7.0)
                label(line_text,x+(box_width-text_width)/2,line_y,7.0)
                line_y+=8.4
        for x1,x2 in ((68.5,75.0),(128.0,134.5),(187.5,194.0)):
            y=560.0
            page.draw_line(fitz.Point(x1,y),fitz.Point(x2-1.5,y),
                           color=(.30,.37,.40),width=.7,overlay=True)
            page.draw_polyline([fitz.Point(x2-3.4,y-1.8),fitz.Point(x2-1.5,y),
                                fitz.Point(x2-3.4,y+1.8)],
                               color=(.30,.37,.40),width=.7,overlay=True)
        label('Repeat the update after every repair completion.',15.5,596.0,7.0)

        result=finish(doc)
        return result,dict(
            panel='4',title=title_text,
            execution_modes=['Unconstrained reference','Constrained restoration'],
            old_internal_labels_visually_replaced=sorted(old_text),
            output='Repair completion updates functionality, source connectivity and mapped tract service.',
            no_threshold_or_T80_in_panel=True,
            unconstrained='Repairs proceed in parallel; no finite-crew or travel limits.',
            constrained='Priority order; finite crews; dispatch includes directed travel.',
            panel_bounds_preserved=True,other_panels_and_stage_5_content_unchanged=True,
            body_font='Arial',body_font_size_pt=7.0,
            illustrative_curves_removed=True,completion_event_recovery=True,
            process_steps=['Repair completes','Station function set to 1',
                           'Re-evaluate source connectivity','Update tract service through W'],
            original_panel_graphics_covered_by_opaque_vector_replacement=True,
            source_vector_signature='outside authorized panel verified by native-render pixel test',
            width_pt=w,height_pt=h)


def restoration_workflow_with_results(raw, recovery_curves_csv):
    """Show a frozen Unconstrained/Impact-first recovery comparison in Stage 4."""
    import csv
    import numpy as np
    import matplotlib
    matplotlib.use('Agg', force=True)
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    rows=list(csv.DictReader(io.StringIO(recovery_curves_csv.decode('utf-8-sig'))))
    time=np.asarray([float(row['time_hr']) for row in rows],dtype=float)
    columns={
        'Unconstrained':'2pc50 | S3_Mean | Population',
        'Impact-first':'2pc50 | Impact population first | Population',
    }
    values={name:np.asarray([float(row[column]) for row in rows],dtype=float)
            for name,column in columns.items()}
    assert len(time)>1 and np.all(np.isfinite(time)) and np.all(np.diff(time)>0)
    assert time[0]==0 and time[-1]>=100 and np.any(np.isclose(time,100))
    for series in values.values():
        assert len(series)==len(time) and np.all(np.isfinite(series))
        assert np.all((series>=0)&(series<=1))
    keep=time<=100
    curve_sha=hashlib.sha256(recovery_curves_csv).hexdigest()

    font_manager.fontManager.addfont('C:/Windows/Fonts/arial.ttf')
    font_manager.fontManager.addfont('C:/Windows/Fonts/arialbd.ttf')
    with matplotlib.rc_context({
        'font.family':'Arial','font.size':6.0,'pdf.fonttype':42,
        'ps.fonttype':42,'axes.linewidth':0.45,
    }):
        fig=plt.figure(figsize=(234.5/72,80.0/72),facecolor='white')
        ax=fig.add_axes([0.13,0.24,0.85,0.56])
        ax.step(time[keep],values['Unconstrained'][keep],where='post',color='#111111',
                linewidth=1.05,label='Unconstrained')
        ax.step(time[keep],values['Impact-first'][keep],where='post',color='#ff7f0e',
                linewidth=1.05,label='Impact-first')
        ax.set_xlim(0,100);ax.set_ylim(0,1.02)
        ax.set_xticks([0,25,50,75,100]);ax.set_yticks([0,0.5,1.0])
        ax.set_xlabel('Time after earthquake (h)',fontsize=6.0,labelpad=1.0)
        ax.set_ylabel('Service availability',fontsize=6.0,labelpad=1.0)
        ax.tick_params(axis='both',labelsize=5.5,length=2,pad=1.2,width=0.4)
        ax.grid(axis='both',color='#d8dde0',linewidth=0.35)
        ax.set_axisbelow(True)
        ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#59636f');ax.spines['bottom'].set_color('#59636f')
        ax.legend(loc='lower left',bbox_to_anchor=(0.0,1.02),ncol=2,
                  frameon=False,fontsize=5.5,handlelength=1.5,
                  columnspacing=1.3,borderaxespad=0.0,handletextpad=0.4)
        plot=io.BytesIO()
        fig.savefig(plot,format='pdf',bbox_inches=None,
                    metadata={'CreationDate':None,'ModDate':None,
                              'Creator':'Figure 1 Stage 4 frozen-results inset'})
        plt.close(fig)

    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0];w,h=page.rect.width,page.rect.height
        stage_text=[s for s in spans(page) if 9.5<s['bbox'][0]<258 and
                    481<s['bbox'][1] and s['bbox'][3]<615]
        text=' '.join(s['text'].replace('\u00a0',' ').replace('\u00ad','-')
                      for s in stage_text)
        assert 'Unconstrained' in text and 'Priority strategy' in text
        assert 'directed' in text and 'availability curves' in text
        page.add_redact_annot(fitz.Rect(9.5,481.7,256.3,614.7),fill=None)
        page.apply_redactions(images=0,graphics=0)
        page.draw_rect(fitz.Rect(9.5,481.7,256.3,614.7),color=None,
                       fill=(1,1,1),overlay=True)
        page.insert_font(fontname='Fig1Stage4Bold',fontfile='C:/Windows/Fonts/arialbd.ttf')
        page.insert_font(fontname='Fig1Stage4Body',fontfile='C:/Windows/Fonts/arial.ttf')
        ink=(32/255,40/255,43/255)
        def label(value,x,y,size=6.0,bold=False):
            page.insert_text((x,y),value,
                fontname='Fig1Stage4Bold' if bold else 'Fig1Stage4Body',
                fontsize=size,color=ink,overlay=True)
        label('Unconstrained',15.5,493.8,7.0,True)
        label('Parallel repairs; no crew or travel limits.',15.5,503.2,5.8)
        label('Constrained strategies',135.0,493.8,7.0,True)
        label('Priority order; finite crews and directed travel.',135.0,503.2,5.5)
        label('Mean population-weighted service availability | 2%-in-50-year scenario',15.5,515.5,5.8,True)
        with fitz.open(stream=plot.getvalue(),filetype='pdf') as chart:
            page.show_pdf_page(fitz.Rect(15.5,518.0,250.0,603.0),chart,0,
                               keep_proportion=False)
        result=finish(doc)
    return result,{
        'panel':'4','plot_type':'frozen population-weighted mean service-availability curves',
        'scenario':'2pc50','time_window_hours':[0,100],
        'source_file':'provenance/legacy_outputs/stage6/recovery_curves_all_system.csv',
        'source_sha256':curve_sha,'source_rows':len(rows),
        'series_columns':columns,
        'points_plotted_per_series':int(keep.sum()),
        'endpoint_at_100h':{name:float(series[np.flatnonzero(np.isclose(time,100))[0]])
                            for name,series in values.items()},
        'curves_are_observed_frozen_model_outputs_not_averaged_policy_schedules':True,
        'no_new_simulation_or_metric_calculation':True,
        'figure_dimensions_pt':[w,h],
    }


def apply(stem,raw):
    return {'Main/Fig01':restoration_workflow,'Main/Fig05':figure5,'Main/Fig07':figure7,'Supplement/FigS03':functional_network_recovery,
            'Supplement/FigS08':supplementary8}[stem](raw)


def relabel(raw, replacements):
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        selected=[s for s in spans(page) if s['text'] in replacements]
        assert len(selected)==len(replacements),(len(selected),list(replacements))
        out=cut_text(doc,selected);page=out[0]
        for s in selected:
            text=replacements[s['text']]
            if not text:continue
            raw_font,metrics=fonts(doc,'Bold' in s['font'],text)
            page.insert_font(fontname='NewLabel'+str(selected.index(s)),fontbuffer=raw_font)
            x=(s['bbox'][0]+s['bbox'][2]-metrics.text_length(text,fontsize=s['size']))/2
            page.insert_text((x,s['origin'][1]),text,fontsize=s['size'],
                             fontname='NewLabel'+str(selected.index(s)))
        result=finish(out);out.close();return result


def cut_text(doc, selected):
    """Omit only label rectangles; leave the underlying vector streams intact."""
    rect=doc[0].rect
    holes=[fitz.Rect(s['bbox'])+(-.2,-.2,.2,.2) for s in selected]
    ys=sorted({0.,rect.height,*[max(0.,h.y0) for h in holes],*[min(rect.height,h.y1) for h in holes]})
    out=fitz.open();p=out.new_page(width=rect.width,height=rect.height)
    for lo,hi in zip(ys,ys[1:]):
        ranges=sorted((max(0.,h.x0),min(rect.width,h.x1)) for h in holes if h.y0<hi-1e-5 and h.y1>lo+1e-5)
        x=0.
        for left,right in ranges:
            if left>x:tile(p,doc,(x,lo,left,hi))
            x=max(x,right)
        if x<rect.width:tile(p,doc,(x,lo,rect.width,hi))
    return out


def functional_network_recovery(raw):
    """Keep only the two original time-dependent recovery panels and shared legend."""
    with fitz.open(stream=raw,filetype='pdf') as doc:
        p=doc[0];w=p.rect.width
        old=[s for s in spans(p) if re.match(r'^[ABC]\. ',
            s['text'].replace('\u00a0',' ').replace('\u00ad','-'))]
        assert len(old)==3
        names=['A. Recovery of largest-component fraction',
               'B. Recovery of mean degree in the largest component']
        signature=vector_signature(p)
        out=fitz.open();page=out.new_page(width=w,height=432)
        first=fitz.Rect(0,220,w,375)
        second=fitz.Rect(0,416,w,570)
        legend=fitz.Rect(0,576,w,628)
        tile(page,doc,first,-195)
        tile(page,doc,second,-205)
        tile(page,doc,legend,-201)
        heading_file='C:/Windows/Fonts/arialbd.ttf'
        heading=fitz.Font(fontfile=heading_file)
        for name,y in zip(names,[5,184]):
            x=(w-heading.text_length(name,fontsize=9.5))/2
            page.insert_text((x,y+heading.ascender*9.5),name,fontname='S3PanelHeading',
                             fontfile=heading_file,fontsize=9.5,color=(0,0,0))
        result=finish(out);out.close()
        with fitz.open(stream=result,filetype='pdf') as check:
            visible=' '.join(check[0].get_text().replace('\u00a0',' ').replace('\u00ad','-').split())
            assert all(name in visible for name in names),visible[-300:]
        return result,dict(source_vector_signature=signature,
            selected_source_regions_pt={'largest_component_recovery':list(first),
                'mean_degree_recovery':list(second),'shared_policy_legend':list(legend)},
            translations_pt={'largest_component_recovery':-195,
                'mean_degree_recovery':-205,'shared_policy_legend':-201},
            panel_titles=names,title_top_pt=[5,184],page_points=[w,432],
            source_plots_retained_as_vector_clips=True,static_percolation_excluded=True,
            recovery_column_headers_repeated=True)


def mapping_cutoff_labels(raw):
    """Replace workflow jargon in the active cutoff plot, without redrawing it."""
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        selected=[s for s in spans(page) if 'production' in s['text'].lower()]
        assert len(selected)==2,selected
        for span in selected:
            span['original_label_bbox']=span['bbox']
            if span['bbox'][3]-span['bbox'][1]>span['bbox'][2]-span['bbox'][0]:
                # A clipped historical text run leaves its closing parenthesis
                # just beyond the extracted span.
                span['bbox']=tuple(fitz.Rect(span['bbox'])+(0,-5,0,1))
        out=cut_text(doc,selected)
        page=out[0]
        page.insert_font(fontname='CutoffPublicationLabel',fontfile='C:/Windows/Fonts/arial.ttf')
        font=fitz.Font(fontfile='C:/Windows/Fonts/arial.ttf')
        changes=[]
        for span in selected:
            rotated=span['bbox'][3]-span['bbox'][1]>span['bbox'][2]-span['bbox'][0]
            text='Change from 3% cutoff (h)' if rotated else '3% cutoff'
            length=font.text_length(text,fontsize=span['size'])
            original_box=span['original_label_bbox']
            origin=(span['origin'][0],(original_box[1]+original_box[3]+length)/2) if rotated else (
                (original_box[0]+original_box[2]-length)/2,span['origin'][1])
            page.insert_text(origin,text,fontname='CutoffPublicationLabel',fontsize=span['size'],
                             rotate=90 if rotated else 0,color=fitz.sRGB_to_pdf(span['color']))
            changes.append(dict(before=span['text'],after=text,old_bbox=list(span['bbox']),
                                font='Arial',font_size_pt=span['size']))
        result=finish(out)
        out.close()
        return result,dict(label_changes=changes,data_and_plot_geometry_unchanged=True)


def gate_sensitivity(raw, values):
    """Use saved means/ranges; combine both threshold tests on one common axis."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8.5,
        'xtick.labelsize':7.5,'ytick.labelsize':8,'pdf.fonttype':42,'ps.fonttype':42})
    names=['Impact-first','Hospital-first','Degree-first']
    keys=['impact-first','hospital-first','degree-first']
    records=[]
    fig=plt.figure(figsize=(185/25.4,210/25.4))
    height=210*72/25.4
    ax=fig.add_axes([.23,(height-340)/height,.70,108/height])
    tx=fig.add_axes([.23,(height-558)/height,.70,108/height])
    for i,(key,color,marker) in enumerate(zip(keys,['#d98200','#595959','#45a437'],['s','o','^'])):
        r=values.loc[values.policy.eq(key)&values.threshold.eq(.5)].iloc[0]
        ax.errorbar(r.mean_gap_h,2-i,xerr=[[r.mean_gap_h-r.p05_gap_h],[r.p95_gap_h-r.mean_gap_h]],
                    color=color,marker=marker,markersize=4,lw=1)
        records.append(r.to_dict())
    for threshold,color,marker,dy in [(.05,'#147f98','o',.14),(.75,'#7a5899','s',-.14)]:
        for i,key in enumerate(keys):
            r=values.loc[values.policy.eq(key)&values.threshold.eq(threshold)].iloc[0]
            tx.errorbar(r.mean_gap_h,2-i+dy,
                xerr=[[r.mean_gap_h-r.p05_gap_h],[r.p95_gap_h-r.mean_gap_h]],
                color=color,marker=marker,markersize=4,lw=1,
                label=f'Threshold {threshold:.2f}' if i==0 else None)
            records.append(r.to_dict())
    tx.legend(loc='lower left',bbox_to_anchor=(0,1.12),ncol=2,frameon=False,fontsize=8,
              borderaxespad=0,handletextpad=.4,columnspacing=1.8)
    for a in [ax,tx]:
        a.set_yticks([2,1,0],names);a.set_ylim(-.5,2.5)
        a.axvline(0,color='#777777',lw=.6,zorder=0)
        a.grid(axis='x',color='#dddddd',lw=.4);a.set_axisbelow(True)
        a.set_xlabel('Service-loss gap (h)')
        for side in ['top','right']:a.spines[side].set_visible(False)
        for side in ['bottom','left']:a.spines[side].set_color('#aaaaaa')
        a.tick_params(length=2,width=.5)
    ax.set_xlim(-7.3,.3);tx.set_xlim(-.17,.06)
    tx.set_xticks([-.15,-.10,-.05,0,.05])
    buf=io.BytesIO();fig.savefig(buf,format='pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
    with fitz.open(stream=raw,filetype='pdf') as source,fitz.open(stream=buf.getvalue(),filetype='pdf') as out:
        p=source[0];old=[s for s in spans(p) if s['text'].startswith('A. Effect')]
        assert len(old)==1
        page=out[0];w=page.rect.width
        clean_a=cut_text(source,[dict(old[0],bbox=(180,8,380,26))])
        tile(page,clean_a,(145,19,385,162),12);clean_a.close()
        names=['A. Mapping-weight cutoff','B. Removing source connectivity (threshold 0.50)',
               'C. Functionality threshold (reference 0.50)']
        font=fonts(source,True,''.join(names))
        for name,y in zip(names,[12,198,393]):title(page,name,w/2,y,font,center=True)
        # The clipped legacy A source carries unused Base-14 resources from
        # hidden historical panels. Embed compatible faces for PDF portability.
        visible={s['font'] for s in spans(page)}
        for row in page.get_fonts():
            if out.extract_font(row[0])[3]:continue
            assert row[3] in ['Helvetica','Helvetica-Bold'] and row[3] not in visible
            bold=row[3].endswith('Bold');name='Arial-BoldMT' if bold else 'ArialMT'
            data=Path('C:/Windows/Fonts', 'arialbd.ttf' if bold else 'arial.ttf').read_bytes()
            metric=fitz.Font(fontbuffer=data)
            stream=out.get_new_xref();out.update_object(stream,'<<>>');out.update_stream(stream,data)
            desc=out.get_new_xref()
            bbox=' '.join(str(round(v*1000)) for v in fitz.Rect(metric.bbox))
            out.update_object(desc,f'<< /Type /FontDescriptor /FontName /{name} /Flags 32 /FontBBox [{bbox}] '
                f'/ItalicAngle 0 /Ascent {round(metric.ascender*1000)} /Descent {round(metric.descender*1000)} '
                f'/CapHeight 716 /StemV 80 /FontFile2 {stream} 0 R >>')
            widths=' '.join(str(round(metric.text_length(bytes([i]).decode('cp1252',errors='replace'),fontsize=1000))) for i in range(256))
            out.update_object(row[0],f'<< /Type /Font /Subtype /TrueType /BaseFont /{name} '
                f'/FirstChar 0 /LastChar 255 /Widths [{widths}] /Encoding /WinAnsiEncoding /FontDescriptor {desc} 0 R >>')
        result=finish(out)
    return result,dict(saved_display_records=records,thresholds=[.05,.75],reference_threshold=.5,
        source_control_threshold=.5,source_control_separate=True,no_simulation_or_new_statistics=True)


def priority_geography(raw):
    """Recolor only the population-context map and colorbar in white-purple."""
    from matplotlib import colormaps
    from matplotlib.colors import LinearSegmentedColormap
    import numpy as np
    stops=['#FFFFFF','#E0D6E9','#B69ACB','#8B63AC','#613A80']
    population_palette=LinearSegmentedColormap.from_list('PopulationWhitePurple',stops,N=256)
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        samples=colormaps['Greys'](np.linspace(0,1,256))[:,:3]
        image_xrefs=sorted({image[0] for image in page.get_images()})
        source_indices=[]
        for xref in image_xrefs:
            pix=fitz.Pixmap(doc,xref)
            assert pix.n==3,'Unexpected population colorbar image format'
            colors=np.unique(np.frombuffer(pix.samples,np.uint8).reshape(-1,3),axis=0)
            source_indices.extend(np.argmin(np.sum((colors[:,None,:]/255-samples[None,:,:])**2,axis=2),axis=1))
        low,high=int(min(source_indices)),int(max(source_indices))
        assert high>low
        # Expand the old truncated color ramp to white-purple; the existing
        # logarithmic population normalization and tick positions are retained.
        population_samples=population_palette(np.clip((np.arange(256)-low)/(high-low),0,1))[:,:3]
        before=page.get_drawings()
        fills={d['fill'] for d in before if d['fill'] and d['rect'].y0>525}
        fills={rgb for rgb in fills if max(rgb)-min(rgb)<2e-5
               and low<=np.argmin(np.linalg.norm(samples-np.array(rgb),axis=1))<=high
               and np.min(np.linalg.norm(samples-np.array(rgb),axis=1))<2e-5}
        assert len(fills)>20
        mapping={}
        for rgb in fills:
            idx=np.argmin(np.linalg.norm(samples-np.array(rgb),axis=1))
            mapping[rgb]=tuple(float(v) for v in population_samples[idx])
        number=rb'([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)'
        rgb_at_end=re.compile(number+rb'\s+'+number+rb'\s+'+number+rb'\s*$')
        def fill_operator_signature(stream):
            pieces=[];cursor=0;pos=0
            while True:
                operator=stream.find(b' rg',pos)
                if operator<0:break
                window=max(0,operator-96)
                match=rgb_at_end.search(stream[window:operator])
                if match:
                    start=window+match.start();end=window+match.end()
                    pieces.extend((stream[cursor:start],b'<fill-rgb>'))
                    cursor=end
                pos=operator+3
            pieces.append(stream[cursor:])
            return __import__('hashlib').sha256(b''.join(pieces)).hexdigest()
        def recolor_stream(stream):
            pieces=[];cursor=0;pos=0;changed=0
            while True:
                operator=stream.find(b' rg',pos)
                if operator<0:break
                window=max(0,operator-96)
                match=rgb_at_end.search(stream[window:operator])
                if match:
                    rgb=tuple(float(match[i]) for i in (1,2,3))
                    if max(rgb)-min(rgb)<2e-5:
                        candidate=min(mapping,key=lambda color:sum((a-b)**2 for a,b in zip(color,rgb)))
                        if max(abs(a-b) for a,b in zip(candidate,rgb))<2e-6:
                            start=window+match.start();end=window+match.end()
                            pieces.extend((stream[cursor:start],
                                ' '.join(f'{v:.9f}' for v in mapping[candidate]).encode()))
                            cursor=end;changed+=1
                pos=operator+3
            if not changed:return stream,0
            pieces.append(stream[cursor:])
            return b''.join(pieces),changed
        count=0;stream_geometry_hashes=[]
        for xref in range(1,doc.xref_length()):
            if not doc.xref_is_stream(xref):continue
            stream=doc.xref_stream(xref)
            if b' rg' not in stream:continue
            changed,n=recolor_stream(stream)
            if n:
                original_signature=fill_operator_signature(stream)
                changed_signature=fill_operator_signature(changed)
                assert original_signature==changed_signature
                stream_geometry_hashes.append(original_signature)
                doc.update_stream(xref,changed);count+=1
        # The original population colorbar is a raster strip; preserve its
        # support and resolution while applying the identical ordinal palette.
        image_rects={xref:page.get_image_rects(xref) for xref in image_xrefs}
        for xref in image_xrefs:
            pix=fitz.Pixmap(doc,xref)
            if pix.n!=3:pix=fitz.Pixmap(fitz.csRGB,pix)
            pixels=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3)
            unique,inverse=np.unique(pixels.reshape(-1,3),axis=0,return_inverse=True)
            indices=np.argmin(np.sum((unique[:,None,:]/255-samples[None,:,:])**2,axis=2),axis=1)
            colors=np.round(population_samples[indices]*255).astype(np.uint8)
            rgb=colors[inverse].reshape(pixels.shape)
            from PIL import Image
            image_bytes=io.BytesIO();Image.fromarray(rgb).save(image_bytes,format='PNG')
            page.replace_image(xref,stream=image_bytes.getvalue())
        assert image_rects=={xref:page.get_image_rects(xref) for xref in image_xrefs}
        return finish(doc),dict(source_palette='Greys',population_palette='white_purple',
             palette_stops=stops,source_palette_index_range=[low,high],
             logarithmic_population_normalization_unchanged=True,
             paint_colors_changed=len(fills),
             streams_changed=count,colorbar_resolution_preserved=True,
             fill_operator_geometry_sha256=stream_geometry_hashes,
             image_rects_unchanged=True,
             all_geometry_and_nonfill_properties_unchanged=True)


def centered_titles(stem, raw):
    """Center each heading on its panel, retaining its row and dense-panel size."""
    centers={
        'Main/Fig02':[132,394,132,394], 'Main/Fig03':[154,408,262.2,148,384],
        'Main/Fig07':[259.2,259.2,145,394],
        'Supplement/FigS01':[262.2,262.2], 'Supplement/FigS02':[262.2,262.2],
        'Supplement/FigS04':[153,413,153,413],
        'Supplement/FigS06':[262.2,262.2,132.3,394.6],
        'Supplement/FigS07':[262.2,262.2],
        'Supplement/FigS08':[262.2,262.2,262.2],
    }
    if stem not in centers:return raw,dict(existing_centered_titles_retained=True)
    with fitz.open(stream=raw,filetype='pdf') as doc:
        p=doc[0]
        old=sorted([s for s in spans(p) if re.match(r'^[A-H]\. ',s['text'].replace('\u00a0',' '))],key=lambda s:s['text'][0])
        assert len(old)==len(centers[stem]),stem
        labels=[s['text'].replace('\u00a0',' ').replace('\u00ad','-') for s in old]
        if stem=='Supplement/FigS08':labels=[label+' repair priority' for label in labels]
        font=fonts(doc,True,''.join(labels))
        if stem=='Main/Fig03':
            # Its rotated damage-state label reaches into the heading row.
            # Omit heading rectangles, never a full-width horizontal strip.
            out=cut_text(doc,[dict(s,bbox=tuple(fitz.Rect(s['bbox'])+(-1.5,-1.5,1.5,1.5))) for s in old])
            p=out[0]
            for s,label,x in zip(old,labels,centers[stem]):title(p,label,x,s['bbox'][1],font,center=True)
            result=finish(out);out.close()
            return result,dict(title_centers_pt=centers[stem],font_pt=9.5,
                original_vector_streams_reused=True,rotated_y_label_preserved=True)
        # Headings occupy empty horizontal bands. Clip those bands rather than
        # editing shared PDF text operators, which can displace unrelated text.
        bands=[]
        for s in sorted(old,key=lambda s:s['bbox'][1]):
            lo,hi=s['bbox'][1]-.2,s['bbox'][3]+.2
            if bands and lo<bands[-1][1]+1:bands[-1][1]=max(bands[-1][1],hi)
            else:bands.append([lo,hi])
        out=fitz.open();p=out.new_page(width=doc[0].rect.width,height=doc[0].rect.height)
        lo=0.
        for a,b in bands:
            if a>lo:tile(p,doc,(0,lo,p.rect.width,a))
            lo=b
        if lo<p.rect.height:tile(p,doc,(0,lo,p.rect.width,p.rect.height))
        for s,label,x in zip(old,labels,centers[stem]):title(p,label,x,s['bbox'][1],font,center=True)
        result=finish(out);out.close()
        return result,dict(title_centers_pt=centers[stem],font_pt=9.5,
                          omitted_label_rectangles=[s['bbox'] for s in old],
                          original_vector_streams_reused=True)
