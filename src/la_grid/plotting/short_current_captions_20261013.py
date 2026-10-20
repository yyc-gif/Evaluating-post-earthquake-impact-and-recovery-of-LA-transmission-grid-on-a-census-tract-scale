"""Concise captions and compact packet; all numbered artwork is immutable."""
from pathlib import Path
import io
import json
import re
import sys

import fitz
from reportlab import rl_config
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from xml.sax.saxutils import escape

import consolidate_current_figure_suite as u

ROOT = u.ROOT
DEST = ROOT / 'results/figure_review'
QA = ROOT / 'docs/reproducibility/figure_suite_concise_captions_20261013'
SOURCE = '5fbdf5a33cb8cee4790f81e896776b8b6fb4f9ae'
GEN = 'src/la_grid/plotting/short_current_captions_20261013.py'
MM = 72 / 25.4

CAPTIONS = [
    'Workflow linking the transmission network and tract dependencies to earthquake damage, modeled service, restoration and community outcomes. Service loss is the integral of the modeled service deficit; T80 is the time to 80% service availability. Q1-Q4 are frozen social-vulnerability quartiles. The vulnerability gap is the absolute Q4-Q1 service-loss difference. Spatial screening identifies co-occurrence, not a composite risk score.',
    '(A) CEC transmission lines and substations. (B) Derived substation connections. (C) Utility-compatible tract assignments. (D) Agreement between assigned substations and public SCE records, comparing all assignments, the highest-weight assignment and the three highest-weight assignments. Agreement assesses mapping correspondence, not feeder-level electricity delivery.',
    '(A) Substation damage distributions. (B) Initial modeled tract service. (C) Unconstrained service-loss components. (D) Population T80 distribution. (E) Conditional mean tract T80 among realizations reaching the threshold. T80 measures time to 80% service; loss integrates service deficit over 480 h. Historical scenarios and 2pc50 use different fragility parameterizations.',
    'Restoration-policy outcomes under 2pc50. (A) Population-weighted modeled service trajectories. (B) Mean service loss for all tracts, Q4 tracts and hospital-linked tracts, and population T80. Loss integrates service deficit over 480 h; T80 is time to 80% service. All displayed whiskers show 5th-95th realization ranges, not confidence intervals; service-loss bars show means without whiskers. Hospital-linked outcomes are tract proxies, not hospital electricity delivery.',
    '(A) Overall and Q4 mean service loss. (B) Loss across frozen vulnerability quartiles. (C, D) Vulnerability-first minus each reference policy: loss outcomes and Gini. (E) Tract-level loss differences; negative values favor Vulnerability-first. Q4 boundaries provide context. The high-low gap is the absolute Q4-Q1 loss difference within each realization. Whiskers in B-D show 5th-95th realization ranges, not confidence intervals; map colors do not indicate statistical significance.',
    'Vulnerability-first minus each reference policy as crew availability (left) or repair duration (right) changes. Rows show overall loss, Q4 loss, the absolute Q4-Q1 loss gap and hospital-linked loss. Negative values indicate lower loss under Vulnerability-first. Whiskers are 95% bootstrap confidence intervals for mean effects, not realization ranges; Degree-first hospital comparisons show means only. Crew and duration are separate one-factor comparisons.',
    '(A) Empirical feature distributions by class; markers locate medians on the 50% guide. (B) Ordinary cohort-z means of the eight fitted coordinates, not weighted-distance contributions. (C) Saved NCV14/H2/K3 geography. (D) Continuous five-policy mean total service deficit, with frozen Q4 outlines. White outlined tracts are N/A. NCV14 is a geographic hazard-screening measure, not FEMA risk or outage probability.',
    '(A) Distributions across substations of scenario-mean damage, with median and interquartile summaries. (B) Initial modeled tract service on a shared availability scale. Tract service includes functionality and source connectivity and is not delivered power. Historical scenarios and 2pc50 use different fragility parameterizations.',
    '(A) Crew origins and substation tasks. (B) Directed task-to-task travel times in hours, with origins in rows and destinations in columns. Reverse-direction times are not assumed equal. These are frozen dispatch inputs, not predictions of post-earthquake congestion.',
    '(A) Static network-removal comparisons. (B, C) Largest functional component size and internal degree during recovery. Functional stations meet the 0.50 cutoff. Spectral network impact differs from the population-impact restoration priority. Curves describe graph structure, not electrical feasibility or optimal repair order.',
    '(A) Minimum service loss as repair sequences are evaluated. (B) Initial and final minima for each GA run. (C) Service-loss gaps for independent validation realizations, with the mean marked. (D) Damage-, threshold- and source-path contributions to that mean gap. A gap is GA minus Impact-first; negative values indicate lower loss. Validation samples are separate from optimization samples.',
    '(A) Mapping-weight cutoff sensitivity. (B) Source connectivity disabled with functionality threshold fixed at 0.50. (C, D) Only the functionality threshold changes, to 0.05 or 0.75; source connectivity remains required. Gaps are control minus reference service loss. Points show means; lines show realization percentiles. The source-only control uses exact frozen loss components and does not represent physical power delivery.',
    '(A) Dynamic joint functionality and source connectivity, comparing all paths with a fixed reliable path. (B) Additional contribution of alternative routes. (C) Static source access conditional on target functionality. (D) Additional conditional connection beyond the fixed path. Static and dynamic probabilities have different conditioning; neither measures delivered power or generation adequacy.',
    '(A) Provider-defined facility planning loads and limits. (B) Modeled service-loss increments from the supported planning ceiling, over the evidence-supported domain and local binding domain. Points show population-weighted means; whiskers show realization percentiles. Unsupported contributions are unchanged. This is a planning-bound sensitivity, not post-earthquake load flow or a full-network capacity assessment.',
    '(A, B) Weighted-space inertia and full-cohort silhouette over K. (C) Initialization, geographic and policy-set sensitivity of the saved eight-variable K3 classification. (D) Within-class silhouette distributions. K3 is not the silhouette maximum. Stability and silhouette are internal diagnostics, not independent physical validation. Removing Init_Supply also redistributes the RQ1 distance budget.',
    '(A) Hospital-linked priority context. (B) Frozen Q4 vulnerability context. (C) Tract population on a logarithmic scale. Numbered substations identify the first repair priorities; population shading is not the Impact-first score. Outcome comparisons appear in Figures 4\u20136 and Supplementary Figure S10. Repair tasks are substations, not tracts.',
    'Absolute service-loss outcomes across crew availability (left) and repair duration (right). Rows show overall loss, Q4 loss, the absolute Q4-Q1 gap and hospital-linked loss. Points are means; whiskers are realization percentiles. Resource factors are varied separately. These absolute outcomes complement the policy differences in Figure 6; they are not independent experiments.',
]


def brief_caption_page(heading, body, width):
    styles = [ParagraphStyle('CaptionTitle',fontName='SuiteBold',fontSize=10,leading=12.5),
              ParagraphStyle('CaptionBody',fontName='SuiteArial',fontSize=10,leading=12.5)]
    paragraphs = [Paragraph(escape(heading),styles[0]),Paragraph(escape(body),styles[1])]
    heights = [p.wrap(width-16*MM,1000)[1] for p in paragraphs]
    height = 10*MM+sum(heights)+2*MM
    buffer = io.BytesIO()
    c = u.canvas.Canvas(buffer,pagesize=(width,height),invariant=1)
    y = height-5*MM
    for p,h in zip(paragraphs,heights):
        p.drawOn(c,8*MM,y-h);y-=h+2*MM
    c.save()
    return fitz.open(stream=buffer.getvalue(),filetype='pdf')


def main():
    checkpoint=QA/'BUILD_CHECKPOINT.json'
    routing='src/la_grid/plotting/build_current_figures.py'
    if checkpoint.exists() and '--rebuild' not in sys.argv:
        q=json.load(open(u.lp(checkpoint)))
        if q['generator_sha256']==u.sha(ROOT/GEN) and q['routing_sha256']==u.sha(ROOT/routing) and all(
            Path(u.lp(ROOT/p)).is_file() and u.sha(ROOT/p)==h for p,h in q['output_hashes'].items()):
            print('Concise caption packet: byte-identical replay.');return
    old=u.captions(u.payload(SOURCE,'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    assert len(old)==len(CAPTIONS)==17
    if not (QA/'PRESERVATION_BEFORE.json').exists():
        raise RuntimeError('Freeze the initial scientific/source worktree state first')
    # Hydrate only files already present in the sparse checkout, not unrelated archives.
    for rel in u.git('ls-files','-z').decode().split('\0'):
        p=ROOT/rel
        if rel and Path(u.lp(p)).is_file() and open(u.lp(p),'rb').read(44).startswith(b'version https://git-lfs'):
            u.write(p,u.payload(SOURCE,rel))
    manifest=u.csv_rows(u.payload(SOURCE,'results/figure_review/FIGURE_MANIFEST.csv'))
    for row in manifest:
        for field in ['current_source_file','mirror_file']:
            p=ROOT/row[field]
            if not Path(u.lp(p)).is_file() or u.sha(p)!=row['sha256']:
                u.write(p,u.payload(SOURCE,row[field]))
            assert u.sha(p)==row['sha256']
    u.pdfmetrics.registerFont(u.TTFont('SuiteArial','C:/Windows/Fonts/arial.ttf'))
    u.pdfmetrics.registerFont(u.TTFont('SuiteBold','C:/Windows/Fonts/arialbd.ttf'))
    rl_config.invariant=1
    book=fitz.open();word_counts=[];registry=[]
    for i,((heading,previous),body) in enumerate(zip(old.items(),CAPTIONS)):
        stem=manifest[2*i]['final_name'].rsplit('.',1)[0]
        with fitz.open(u.lp(DEST/(stem+'.pdf'))) as fig:
            with brief_caption_page(heading,body,fig[0].rect.width) as cap:
                w,h=fig[0].rect.width,fig[0].rect.height
                page=book.new_page(width=w,height=h+cap[0].rect.height)
                page.show_pdf_page(fitz.Rect(0,0,w,h),fig,0)
                page.show_pdf_page(fitz.Rect(0,h,w,page.rect.height),cap,0)
                capspans=[s for b in cap[0].get_text('dict',flags=0)['blocks'] for line in b.get('lines',[]) for s in line['spans']]
                assert min(s['size'] for s in capspans)>=9.99
                assert all(cap[0].rect.contains(fitz.Rect(s['bbox'])) for s in capspans)
                registry.append(dict(figure=stem,packet_page=i+1,figure_height_pt=h,caption_height_pt=cap[0].rect.height,
                    caption_stream_sha256=u.digest(cap[0].read_contents()),caption_min_font_pt=min(s['size'] for s in capspans),
                    caption_bounds_valid=True))
        word_counts.append(dict(figure=stem,old_words=len(previous.split()),new_words=len(body.split())))
    with fitz.open(stream=u.payload(SOURCE,'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),filetype='pdf') as prior:
        book.insert_pdf(prior,from_page=34,to_page=37)
    assert len(book)==21
    u.write(DEST/'ALL_FIGURES_WITH_CAPTIONS.pdf',book.tobytes(garbage=4,deflate=True,no_new_id=True));book.close()
    caps='# Manuscript-facing figure captions\n\n'+'\n\n'.join('## '+h+'\n\n'+b for h,b in zip(old,CAPTIONS))+'\n'
    u.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md',caps)
    u.write_csv(QA/'CAPTION_WORD_COUNTS.csv',word_counts)
    u.write_csv(QA/'COMPACT_PACKET_PAGE_REGISTRY.csv',registry)
    u.dump(QA/'CAPTION_QA.json',dict(source_commit=SOURCE,numbered_figures=17,packet_pages=21,
        evidence_pages=4,artwork_pairs_byte_identical=17,figure_rescaling=False,
        old_total_words=sum(r['old_words'] for r in word_counts),new_total_words=sum(r['new_words'] for r in word_counts),
        maximum_caption_words=max(r['new_words'] for r in word_counts),PathB_artwork_promoted=False))
    for rel in ['results/figure_review/README.md','results/figures/README.md']:
        previous=u.payload(SOURCE,rel).decode()
        # These are active counts, not historical provenance in UPDATE_LOG.
        previous=previous.replace('38 packet pages','21 compact packet pages')
        previous+='\n\n## Concise captions\n\nThe current packet has 17 native-size figures with short captions directly below them, plus four unchanged evidence pages (21 pages total). No numbered artwork or scientific value changes. The separate Path B review is not promoted here.\n'
        u.write(ROOT/rel,previous)
    log=u.payload(SOURCE,'results/figure_review/UPDATE_LOG.md').decode()
    u.write(DEST/'UPDATE_LOG.md',log+'\n\n## 2026-10-13 Concise captions\n\nRemoved results/discussion and production commentary from captions. Native figure artwork unchanged; captions placed beneath figures. Compact packet: 21 pages including four retained evidence pages. Path B remains a separate review package.\n\n## 2026-10-14 Statistical caption precision\n\nFigures 4/5 distinguish 5th-95th realization ranges from confidence intervals. Figure 4 service-loss bars have no whiskers. Figure 6 explicitly identifies 95% bootstrap confidence intervals for mean effects and its means-only exception. No artwork, numerical values or Path B classification is promoted.\n')
    outputs=['results/figure_review/'+p for p in ['MANUSCRIPT_FACING_CAPTIONS.md','ALL_FIGURES_WITH_CAPTIONS.pdf','README.md','UPDATE_LOG.md']]
    outputs+=['results/figures/README.md']+[r[f] for r in manifest for f in ['current_source_file','mirror_file']]
    u.dump(checkpoint,dict(generator_sha256=u.sha(ROOT/GEN),routing_sha256=u.sha(ROOT/routing),
        output_hashes={p:u.sha(ROOT/p) for p in outputs}))
    print('Captions:',sum(r['old_words'] for r in word_counts),'->',sum(r['new_words'] for r in word_counts),
          'words; compact packet 21 pages; all 17 artwork pairs unchanged.')


if __name__=='__main__':main()
