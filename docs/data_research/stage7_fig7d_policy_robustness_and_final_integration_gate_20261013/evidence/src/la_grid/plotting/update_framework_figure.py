"""Update Figure 1 wording and spacing, preserving its illustrated five stages.

Reads only the archived Figure 1 artwork. No scientific data or execution
module is imported. The output replaces Figure 1 in the complete current set.
"""
from pathlib import Path
import hashlib
import json
import shutil
import csv
import re
import fitz

from la_grid.paths import REPO_ROOT

ROOT = REPO_ROOT
REVIEW = ROOT / 'results/figure_review'
ARCHIVE = ROOT / 'provenance/figure_review_history/fig01_before_wording_update_20261006'
MM = 72 / 25.4
REGULAR = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'
INK = (.125, .145, .169)
OUTLINE = (.53, .58, .62)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for rel in ['Main/Fig01.pdf', 'Main/Fig01.png', 'MANUSCRIPT_FACING_CAPTIONS.md']:
        saved = ARCHIVE / Path(rel).name
        if not saved.exists():
            shutil.copy2(REVIEW / rel, saved)
    source = fitz.open(ARCHIVE / 'Fig01.pdf')
    document = fitz.open()
    page = document.new_page(width=source[0].rect.width, height=source[0].rect.height)
    page.show_pdf_page(page.rect, source, 0)
    # Replace reader-facing text only; retain all original illustrated objects.
    old_spans = [s for b in page.get_text('dict')['blocks'] for l in b.get('lines', [])
                 for s in l['spans']]
    for span in old_spans:
        page.add_redact_annot(fitz.Rect(span['bbox']), fill=False)
    page.apply_redactions(images=0, graphics=0)
    page.insert_font(fontname='FrameworkArial', fontfile=REGULAR)
    page.insert_font(fontname='FrameworkArialBold', fontfile=BOLD)
    fonts = {False: fitz.Font(fontfile=REGULAR), True: fitz.Font(fontfile=BOLD)}

    def text(x, y, label, size=7.5, bold=False, center=False, color=INK):
        if center:
            x -= fonts[bold].text_length(label, fontsize=size) / (2 * MM)
        page.insert_text((x * MM, y * MM), label,
                         fontname='FrameworkArialBold' if bold else 'FrameworkArial',
                         fontsize=size, color=color)

    def cover(x0, y0, x1, y1, fill=(1, 1, 1)):
        page.draw_rect(fitz.Rect(x0*MM, y0*MM, x1*MM, y1*MM),
                       color=None, fill=fill)

    # Five input groups without a tiny composite map or competing symbol legend.
    cover(3.3, 7.2, 181.7, 19.7)
    text(5, 6, 'Data Inputs', 9.5, True)
    inputs = [
        ('Transmission system', ['Lines, substations', 'and Core sources']),
        ('Earthquake inputs', ['Ground motion', 'and fragility']),
        ('Restoration inputs', ['Roads, repair yards', 'and repair durations']),
        ('Community inputs', ['Tracts, population', 'and hospitals']),
        ('Social vulnerability', ['Vulnerability scores', 'and quartiles']),
    ]
    for i, (title, labels) in enumerate(inputs):
        x = 5 + 35.4*i
        if i:
            page.draw_line((x*MM-2*MM, 9*MM), (x*MM-2*MM, 18.3*MM),
                           color=(.83,.87,.9), width=.4)
        text(x, 10.5, title, 7.8, True)
        for y, label in zip([14, 17.3], labels):
            text(x, y, label)

    # Equal baseline and title hierarchy for both top-row stages.
    titles = [(3,27,'1','Topology and Dependency Construction'),
              (94.5,27,'2','Seismic Damage Simulation'),
              (3,94,'3','Damage-to-Service Translation'),
              (3,164,'4','Restoration Policies and Execution'),
              (94.5,164,'5','Community Outcomes and Robustness')]
    for x,y,num,title in titles:
        badge_colors=[(.18,.43,.62),(.72,.36,.29),(.48,.31,.56),(.137,.533,.475),(.30,.55,.37)]
        page.draw_circle(((x+2.5)*MM,(y+2.5)*MM),1.6*MM,
                         color=None,fill=badge_colors[int(num)-1])
        text(x+2.5, y+3.5, num, 9.5, True, True, (1,1,1))
        text(x+5, y+3.8, title, 9.5, True)
    for cx, labels in [(24.5,['Direct-Link Topology','and Source Substations']),
                       (65.5,['Tract–Substation','Dependency Weights'])]:
        for y, label in zip([71,75],labels): text(cx,y,label,center=True)
    for cx, labels, ys in [(110,['Scenario PGA at','substations'],[74,78]),
                           (131,['Fragility functions'],[75.5]),
                           (152.5,['Residual','functionality'],[38,42]),
                           (172,['Repair-duration','samples'],[38,42])]:
        for y,label in zip(ys,labels): text(cx,y,label,center=True)
    for i in range(5): text(140.4,49.6+i*4.1,'DS'+str(i),7)
    for i,ds in enumerate([4,3,2,1]): text(161.9,50.7+i*5.17,'DS'+str(ds),7)
    text(160,78,'Damage-conditioned outputs',center=True)
    text(8,105,'Network and tract dependency',7.5,True,color=(.18,.43,.62))
    text(104,105,'Damage states, functionality and repair times',7.5,True,color=(.72,.36,.29))
    for cx, ys, labels in [(18.5,[145],['Substation damage']),
        (52.5,[145],['Residual functionality']),
        (86,[142,146],['Source-connected','functional network']),
        (124,[142,146],['Utility-compatible','aggregation']),
        (163,[142,146],['Modeled tract','service availability'])]:
        for y,label in zip(ys,labels): text(cx,y,label,center=True)
    text(11,182,'T80',7,color=(.72,.36,.29))
    for cx, labels in [(19.5,['Unconstrained','reference']),
                       (49,['Crew dispatch','and directed travel']),
                       (75,['Priority-strategy','recovery'])]:
        for y,label in zip([208,212],labels): text(cx,y,label,center=True)

    # Keep the output stage in its original card. Replace obsolete weighted
    # recovery/sensitivity mini-panels with an explicit outcome comparison.
    cover(94.8,169.3,181.7,216.7)
    text(138.25,173,'Compare Vulnerability-first with other priorities',7.5,True,True)
    # Reuse the existing recovery and typology illustrations at readable scale.
    page.show_pdf_page(fitz.Rect(98*MM,176*MM,122*MM,190*MM),source,0,
                       clip=fitz.Rect(98*MM,175*MM,121*MM,201*MM))
    page.show_pdf_page(fitz.Rect(157*MM,176*MM,179*MM,190*MM),source,0,
                       clip=fitz.Rect(157*MM,175*MM,179*MM,202*MM))
    # A conceptual quartile key, not invented outcome values.
    for i,label in enumerate(['Q1','Q2','Q3','Q4']):
        xx=127+i*7
        page.draw_rect(fitz.Rect(xx*MM,179*MM,(xx+5)*MM,185*MM),
                       color=(.38,.49,.44),fill=(.92,.95,.93),width=.5)
        text(xx+2.5,188,label,7,center=True)
    for cx, labels in [(110,['Population-weighted','and hospital-linked','service loss']),
                       (140,['Q1–Q4 service loss','Signed / absolute Q4–Q1','Population-weighted Gini']),
                       (168,['Community typology','and hotspot score'])]:
        for y,label in zip([194,198,202],labels): text(cx,y,label,7,center=True)
    page.draw_line((98*MM,205*MM),(179*MM,205*MM),color=(.83,.87,.9),width=.4)
    text(138.25,209,'Resources: crew availability and repair duration',7,center=True)
    text(138.25,213,'Robustness: mapping, source gate and SCE planning limits',7,center=True)

    target=REVIEW/'Main/Fig01.pdf'
    document.save(target,garbage=4,deflate=True)
    document.close(); source.close()
    with fitz.open(target) as doc:
        p=doc[0]
        spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
        assert min(s['size'] for s in spans)>=6.99
        assert all(p.rect.contains(fitz.Rect(s['bbox'])) for s in spans)
        for suffix in ['proxy','SVI-weighted','CSRI','LA direct']:
            assert suffix.lower() not in p.get_text().lower()
        pix=p.get_pixmap(matrix=fitz.Matrix(600/72,600/72),alpha=False)
        pix.set_dpi(600,600);pix.save(target.with_suffix('.png'))
        pix=p.get_pixmap(matrix=fitz.Matrix(1.7,1.7),alpha=False)
        pix.save(Path('C:/ABAQUS/temp/AppData/Local/Temp/fig01_after.png'))
        audit={'size_mm':[p.rect.width/MM,p.rect.height/MM],
               'minimum_font_pt':min(s['size'] for s in spans),
               'fonts':sorted({s['font'] for s in spans}),
               'scientific_source_changes':0,'other_figure_changes':0,
               'source_artwork_sha256':sha(ARCHIVE/'Fig01.pdf'),
               'new_artwork_sha256':sha(target)}
    for ext in ['pdf','png']:
        shutil.copy2(REVIEW/f'Main/Fig01.{ext}',ROOT/f'results/figures/Fig01_Methodology_Workflow.{ext}')
    return audit


def integrate(audit):
    """Register Figure 1 and refresh the existing complete collection packets."""
    caption_file=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md'
    caption=(
        'The five stages link transmission-network construction, earthquake damage, '
        'modeled tract service, restoration policies and community outcomes. '
        'Transmission lines and substations define the direct-link network and Core sources; '
        'utility-compatible tract–substation weights define community dependency. '
        'Scenario ground motion and fragility determine substation damage, residual '
        'functionality and damage-specific repair durations. Modeled tract service combines '
        'substation functionality, the 0.5 functionality threshold, source connectivity and '
        'tract dependency weights. Unconstrained recovery provides a reference; priority '
        'strategies determine substation repair order under crew-dispatch and directed-travel '
        'constraints. Vulnerability-first is compared with the other restoration priorities '
        'using population-weighted and hospital-linked tract service loss, Q1–Q4 service loss, '
        'the signed Q4–Q1 difference, the absolute Q4–Q1 difference within each realization, '
        'and population-weighted Gini. Service loss is the time integral of one minus modeled '
        'service availability over the common 0–480 h horizon, reported in hours; T80 is the '
        'time to reach 80% modeled service. Q1 and Q4 denote the lowest and highest '
        'social-vulnerability quartiles. A Gini value of zero denotes equal tract service '
        'loss; larger values denote greater inequality. Community typology and hotspot '
        'scores describe spatial patterns rather than repair priorities. Crew availability '
        'and repair-duration contrasts examine resource dependence; mapping, source-gate '
        'and SCE planning-limit checks assess model assumptions. Source connectivity is '
        'a modeled service condition, not delivered power or electrical adequacy. '
        'The small illustrations depict analytical operations, not additional numerical results.'
    )
    content=caption_file.read_text(encoding='utf-8')
    content,count=re.subn(r'(## Figure 1\.[^\n]*\n\n).*?(?=\n\n## |\Z)',
                         lambda m:m.group(1)+caption,content,flags=re.S)
    assert count==1
    caption_file.write_text(content,encoding='utf-8')
    def update_csv(path,update):
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
        for row in rows: update(row)
        with path.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    def manifest(row):
        if row['final_name'] not in ['Main/Fig01.pdf','Main/Fig01.png']: return
        ext=Path(row['final_name']).suffix
        for c in ['source_file','source_commit','sha256','current_source_file']:
            row['parent_'+c]=row.get(c,'')
        row.update(source_file=(REVIEW/row['final_name']).relative_to(ROOT).as_posix(),
                   current_source_file=(REVIEW/row['final_name']).relative_to(ROOT).as_posix(),
                   source_commit='AUTHOR_REQUESTED_FRAMEWORK_UPDATE_20261006',
                   sha256=sha(REVIEW/row['final_name']),size_mm='185.000 x 220.000',
                   min_font_pt='7.000',status='AUTHOR_REQUESTED_CURRENT_FRAMEWORK')
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    def index(row):
        if row['file'] not in ['Fig01_Methodology_Workflow.pdf','Fig01_Methodology_Workflow.png']: return
        ext=Path(row['file']).suffix
        source=REVIEW/('Main/Fig01'+ext)
        row.update(source_authority=source.relative_to(ROOT).as_posix(),
                   source_path=source.relative_to(ROOT).as_posix(),
                   generator='src/la_grid/plotting/update_framework_figure.py',
                   sha256_or_lfs_oid='sha256:'+sha(source),
                   main_message='Five analytical stages link earthquake damage, source-connected tract service, restoration priorities and distributional outcomes.',
                   notes='Author-requested wording and spacing update; previous artwork retained as provenance.')
    update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    main=fitz.open()
    for i in range(1,8):
        with fitz.open(REVIEW/f'Main/Fig{i:02}.pdf') as doc: main.insert_pdf(doc)
    main.save(REVIEW/'ALL_MAIN_FIGURES.pdf',garbage=4,deflate=True);main.close()
    headings=list(re.finditer(r'(?m)^## (.+)\n\n',content)); lookup={}
    for i,m in enumerate(headings):
        title=m.group(1); body=content[m.end():headings[i+1].start() if i+1<len(headings) else len(content)].strip()
        if title.startswith('Figure '): key=f'Main/Fig{int(title.split(".")[0].replace("Figure ","")):02}.pdf'
        elif title.startswith('Supplementary Figure S'): key=f'Supplement/FigS{int(title.split(".")[0].replace("Supplementary Figure S","")):02}.pdf'
        else: continue
        lookup[key]=(title,body)
    book=fitz.open()
    for key in [f'Main/Fig{i:02}.pdf' for i in range(1,8)]+[f'Supplement/FigS{i:02}.pdf' for i in range(1,14)]:
        with fitz.open(REVIEW/key) as doc: book.insert_pdf(doc)
        title,body=lookup[key];p=book.new_page(width=185*MM,height=350*MM)
        p.insert_font(fontname='PacketArial',fontfile=REGULAR)
        p.insert_font(fontname='PacketArialBold',fontfile=BOLD)
        p.insert_text((14*MM,20*MM),title,fontname='PacketArialBold',fontsize=9.5)
        assert p.insert_textbox(fitz.Rect(14*MM,29*MM,171*MM,333*MM),body,
                               fontname='PacketArial',fontsize=9.2,lineheight=1.22)>=0
    assert len(book)==40
    book.save(REVIEW/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);book.close()
    audit['generator_sha256']=sha(Path(__file__))
    path=ROOT/'docs/reproducibility/FIG01_FRAMEWORK_UPDATE_20261006.json'
    path.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    audit=build()
    integrate(audit)
    print(json.dumps(audit,indent=2))
