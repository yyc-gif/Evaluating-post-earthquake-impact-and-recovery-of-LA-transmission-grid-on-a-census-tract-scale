"""Package only the bounded artwork fixes; no scientific module is executed.

Run after the fresh actual-output inspection recorded in VISUAL_REVIEW.csv.
The existing READY artwork is embedded unchanged, not regenerated.
"""
from pathlib import Path
from collections import Counter
import importlib.util
import hashlib
import json
import subprocess

import fitz
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
OLD=ROOT/'results/figure_review/promotion_readiness_4a4e9b5'
MM=72/25.4
BASELINE='5e7884610c40e5f3a0ea75b4f563756a31d1ba7b'
READY='READY_FOR_AUTHOR_PROMOTION'
OPTIONAL='OPTIONAL INTERNAL EVIDENCE — NOT PROPOSED FOR SUBMISSION'
ORDER=['Fig01','Fig02','Fig03','Fig04','Fig05','Fig06','Fig07',*[f'FigS{i:02}' for i in range(1,14)]]
FIXED={'Fig01','Fig03','Fig05','FigS01','FigS02','FigS03','FigS04','FigS06','FigS07','FigS08','FigS10','FigS11'}


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    spec=importlib.util.spec_from_file_location('previous_review_helpers',p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def measure(path):
    with fitz.open(path) as d:
        p=d[0]
        ss=[s for b in p.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
        fonts=[]
        for f in d.get_page_fonts(0,full=True):
            name,ext,typ,data=d.extract_font(f[0]);fonts.append({'font':name,'embedded':len(data)>0})
        return {'width_mm':p.rect.width/MM,'height_mm':p.rect.height/MM,'minimum_font_pt':min(s['size'] for s in ss),
                'embedded_fonts':fonts,'sha256':sha(path)}


def verify_guards():
    before=json.loads((OUT/'BEFORE_STATE.json').read_text())
    changes={family:[p for p,h in hs.items() if sha(ROOT/p)!=h] for family,hs in before['hashes'].items()}
    assert all(not v for v in changes.values()),changes
    prefix=OUT.relative_to(ROOT).as_posix().encode()+b'/'
    def unrelated(raw):
        return b'\0'.join(e for e in raw.split(b'\0') if e and not e.split(b'\t',1)[1].startswith(prefix))
    assert unrelated(subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT))==unrelated(bytes.fromhex(before['index_hex'])),'unrelated staging changed'
    refs={'protected_july':subprocess.check_output(['git','rev-parse','archive/ijdrr-submission-20260722'],cwd=ROOT,text=True).strip()}
    assert refs['protected_july']=='182686868cffe962739804f6bc0ccecaed73d601'
    return {'baseline':BASELINE,'changes':changes,'guard_file_counts':{k:len(v) for k,v in before['hashes'].items()},
            'trajectory_note':'No trajectory, scheduling or scientific stage was executed. The existing registered scientific-file guards were rehashed; this is not a claim that every external trajectory was newly rehashed.',
            'unrelated_staging_preserved':True,**refs}


def main():
    checks=verify_guards()
    oldrows=json.loads((OLD/'INVENTORY.json').read_text())
    preferred={r['figure']:r for r in oldrows if r['kind']=='preferred'}
    captions=json.loads((OUT/'CAPTIONS.json').read_text())
    visual=pd.read_csv(OUT/'VISUAL_REVIEW.csv').set_index('figure')
    assert all(k in visual.index for k in FIXED)
    helpers=load(OLD/'complete_audit.py')
    rows=[]
    for key in ORDER+['FigS14','FigS15','FigS16']:
        old=preferred[key]
        name='Fig01_Submission_Layout_Candidate.pdf' if key=='Fig01' else key+'.pdf'
        p=OUT/name if key in FIXED else ROOT/old['path']
        m=measure(p)
        if key not in {'FigS14','FigS15'}:
            assert m['minimum_font_pt']>=6.99,(key,m)
            assert all(f['embedded'] and 'DejaVu' not in f['font'] for f in m['embedded_fonts'])
        if key not in FIXED:assert sha(p)==old['sha256'],key
        rows.append({'figure':key,'candidate_file':p.relative_to(ROOT).as_posix(),
            'original_source':old['path'],'original_sha256':old['sha256'],
            'intended_role':'Main candidate' if key.startswith('Fig0') else ('Supplement candidate' if key not in {'FigS14','FigS15','FigS16'} else 'Internal/review aid'),
            'status':OPTIONAL if key in {'FigS14','FigS15'} else READY,
            'caption':captions[key],
            'visual_observation':str(visual.loc[key,'observations']) if key in FIXED else 'Prior complete audit READY artwork retained byte-identically; no unrequested presentation edit.',
            'author_action':'Choose exact-original versus independent re-layout before promotion.' if key=='Fig01' else ('No inclusion proposed; author decision required to reopen.' if key in {'FigS14','FigS15'} else ('Review aid only; cannot replace Fig06 common scales.' if key=='FigS16' else 'Await author approval; no promotion.')),
            **m})
    (OUT/'REVIEW_INVENTORY.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    pd.DataFrame([{k:v for k,v in r.items() if k not in {'caption','embedded_fonts'}} for r in rows]).to_csv(OUT/'REVIEW_INVENTORY.csv',index=False)
    d=fitz.open()
    with helpers.paragraph_page('Complete Main and Supplement Figure Review — bounded fixes',[
        ('Baseline and scope','Based on complete audit at '+BASELINE+'. Twelve artwork/caption gates were addressed in an isolated review folder. The READY Fig02/Fig04/Fig06/Fig07/S05/S09/S12/S13 and optional S16 artwork remain unchanged. No scientific stage or bootstrap was run.'),
        ('Native size','Every artwork is shown at its native 185-mm width and native height, with a separate following caption page. Long figures are not reduced to fit. PNGs are 600-dpi previews; page previews show the same unshrunk physical artwork. S04 requires a full supplementary artwork page with caption separate.'),
        ('Author choice and paused evidence','Fig01 is an independent re-layout of the exact July wording, illustrations and arrow relations. The exact original is retained in the comparison file, not accepted as a 4.9-pt default submission version. S14/S15 are paused optional internal evidence and not proposed for submission. S16 appears only in the review-aid appendix.'),
        ('No promotion','Recommended readiness does not mean author acceptance. results/figures/ and every source artwork remain unchanged. The author decides the complete-set promotion.')
    ]) as q:d.insert_pdf(q)
    toc=[[1,'Main candidates',len(d)+1]]
    packet_rows=[r for r in rows if r['figure'] in ORDER]+[r for r in rows if r['figure']=='FigS16']
    for row in packet_rows:
        key=row['figure']
        if key=='FigS01':toc.append([1,'Supplement candidates',len(d)+1])
        if key=='FigS16':toc.append([1,'Review aid — not proposed as a submission figure',len(d)+1])
        row['packet_artwork_page']=len(d)+1;toc.append([2,key,len(d)+1])
        h=max(297,row['height_mm']+35)*MM
        p=d.new_page(width=210*MM,height=h);p.insert_font(fontname='Arial',fontfile='C:/Windows/Fonts/arial.ttf')
        p.insert_text((12.5*MM,10*MM),key+' | native 185-mm artwork | AUTHOR REVIEW ONLY',fontname='Arial',fontsize=8)
        with fitz.open(ROOT/row['candidate_file']) as src:p.show_pdf_page(fitz.Rect(12.5*MM,18*MM,197.5*MM,18*MM+src[0].rect.height),src,0)
        p.insert_text((12.5*MM,h-8*MM),f"Artwork {row['width_mm']:.1f} x {row['height_mm']:.1f} mm; minimum text {row['minimum_font_pt']:.2f} pt. Caption follows.",fontname='Arial',fontsize=8)
        row['packet_caption_page']=len(d)+1
        with helpers.paragraph_page(key+' — caption and bounded change record',[
            ('Caption',row['caption']),('Actual review / scope',row['visual_observation']),
            ('Author decision',row['author_action']),('Source and identity',row['candidate_file']+'\nSHA-256: '+row['sha256']+'\nOriginal authority: '+row['original_source'])
        ]) as q:d.insert_pdf(q)
    d.set_toc(toc);d.set_metadata({'title':'Complete Main and Supplement Figure Review — Bounded Presentation Fixes','subject':'Review-only, native-size; no scientific computation or promotion'})
    # Preserve the independent font resources from source and caption pages.
    packet=OUT/'COMPLETE_MAIN_AND_SUPPLEMENT_FIGURE_REVIEW.pdf';d.save(packet,garbage=2,deflate=True);pages=len(d);d.close()
    (OUT/'PACKET_PAGE_INDEX.json').write_text(json.dumps([{k:r[k] for k in ['figure','packet_artwork_page','packet_caption_page']} for r in packet_rows],indent=2))

    table=['# Complete figure promotion readiness — bounded fixes','',
        'Baseline: `'+BASELINE+'`. Only the expressly identified presentation gates were edited. Fresh native PDF renders and page previews of all twelve affected candidates were opened; the visual observations below describe those actual files. Existing READY figures were not regenerated.','',
        '**No promotion.** Twenty proposed review candidates (seven main and S01–S13) are ready for author review. This is not author approval. Fig01 still requires choosing between the reference and the independent re-layout; 4.9-pt lettering is not accepted as a default submission version. S14/S15 are paused, optional internal evidence. S16 remains a near-zero review aid, not a replacement for Fig06 common scales.','',
        '| Figure | Candidate | Role | Actual mm | Minimum pt | Actual presentation observation | Status / author action |','|---|---|---|---:|---:|---|---|']
    for r in rows:
        table.append(f"| {r['figure']} | `{r['candidate_file']}` | {r['intended_role']} | {r['width_mm']:.1f} × {r['height_mm']:.1f} | {r['minimum_font_pt']:.2f} | {r['visual_observation'].replace('|','/')} | {r['status']}; {r['author_action']} |")
    table += ['', '## Scientific wording gates closed', '',
        '- Fig03 D-right now explicitly means **mean of realization-specific tract T80 values conditional on that tract reaching T80**; the PDF itself is byte-identical.',
        '- Fig05 A has four policies; only B has the nine-policy key. The C/D key is reference-specific: primary Hospital-first gray circle, primary Impact-first orange square, additional Degree-first open green triangle. Gini remains unitless.',
        '- S01 and S10 boxes use 1.5-IQR whiskers plus points/fliers. Fig04/Fig05 ranges are 5th–95th realization ranges; Fig06 saved intervals are bootstrap CIs. They are not interchangeable statistical objects.',
        '- S02 is tract-level mean modeled service availability, using the unchanged production mapping; historical-versus-2pc50 differences are not pure PGA effects.',
        '- S04 static network λ2 attacks are distinct from Impact-first repair priority. Dynamic curves are means; D is the saved matched candidate-minus-Hospital source-loss range over 0–480 h.',
        '- S06 uses exactly 337 comparable tracts and positive retained candidates ranked by mapping weight. Agreement is not feeder accuracy. The 246 >1-h tract shifts describe mapping sensitivity.',
        '- S07 distinguishes dynamic unconditional joint source-connected mass from static conditional reliability. The path comparator is fixed before recovery. Neither means delivered MW or adequacy.',
        '- S08 distinguishes 34/28 planning rows/stations from 19 one-to-one bound-supported stations; planning vintage is 2026, not earthquake loading or full-network electrical validation.',
        '- S11 displays within-hazard mean matched effects versus Unconstrained under C57_D1. Saved ranges exist but are not drawn. Cell colors/scales and numbers are unchanged.', '',
        '## Paused S14/S15: need judgments','',
        '- **S14:** no unique submission-figure need is established for the current manuscript/reviewer response; gate robustness remains traceable in existing Methods/tables and the accepted sensitivity evidence. OPTIONAL INTERNAL EVIDENCE — NOT PROPOSED FOR SUBMISSION. This does not assert that mapping robustness and gate robustness are the same quantity. Register/caption/fix it only if the author explicitly requires its inclusion.',
        '- **S15:** S07 already supplies the proposed dynamic/full-versus-fixed and static route-gain evidence; no additional scatter is required for the present response. OPTIONAL INTERNAL EVIDENCE — NOT PROPOSED FOR SUBMISSION. Existing source files remain untouched.', '',
        '## Remaining allocation decisions','',
        'Fig01 re-layout is 220 mm high, Fig03 216 mm, Fig05 218 mm, Fig07 229 mm, and S04 244.4 mm. They are shown unshrunk; captions must be allocated separately where needed. These page-allocation choices and Fig01 adoption belong to the author. The earlier 293-mm Fig02 remains superseded, not silently restored. No small-font author exception is presumed.', '',
        f'Complete packet: {pages} pages. Exact July versus re-layout comparison: `FIG01_EXACT_ORIGINAL_VS_LAYOUT.pdf`.']
    (OUT/'COMPLETE_FIGURE_PROMOTION_READINESS.md').write_text('\n'.join(table)+'\n',encoding='utf-8')
    changes=pd.read_csv(OUT/'PRESENTATION_CHANGES.csv')
    lines=['# Final presentation fix log','', 'Baseline: `'+BASELINE+'`. Scientific content changed = **NO**. Promotion performed = **NO**.','',
        '| Figure | Bounded presentation/caption change |','|---|---|']
    lines += [f"| {r.figure} | {r.presentation_change} |" for r in changes.itertuples()]
    lines += ['', '## Identity and actual-output checks','',
        '- Fig01 wording multiset and twelve directed relationships retained; original maps/plots/matrices are native PDF clips. Minimum normal text: original 4.9 pt → candidate 7.0 pt. Headers 9.5 pt; new frame/connector widths 0.5–0.7 pt. Original illustration hairlines remain original, rather than pretending every inherited map stroke was restyled.',
        '- Reference-color/shape identity: Hospital-first gray circle, Impact-first orange square; Degree-first open green triangle for additional sensitivity. Fig03 hazard authority and Fig02 mapping authority are matched.',
        '- All twelve affected PDFs have native width 185 mm, minimum normal text at least 7 pt, embedded Arial/Arial Bold, no DejaVu resources and no off-page text. Fresh preview/page images were opened individually. S11 contrast is sampled from the actual unchanged background; darkest cells now use white lettering.',
        '- READY Fig02/Fig04/Fig06/Fig07/S05/S09/S12/S13/S16 artwork SHA-256 values remain identical; Fig03 artwork is also identical. Source/provenance PDFs and official publication artwork are unchanged.',
        '- Validation records enumerate the guarded scope: scientific results, publication set and original source artwork. No scientific stage, trajectory generation, scheduling or bootstrap is executed; external archive payloads are not claimed to have been freshly exhaustively rehashed.',
        '- No existing scientific implementation was modified. Presentation adapters, audit records and review artifacts are confined to this directory. Existing unrelated staging is preserved.', '',
        '## S14/S15','', 'Both remain **OPTIONAL INTERNAL EVIDENCE — NOT PROPOSED FOR SUBMISSION**; no provenance registration, font repair or promotion was performed.', '',
        '## Review files','', 'The complete PDF preserves actual physical dimensions and places the caption after each artwork. `ACTUAL_OUTPUT_QA.csv`, `VISUAL_REVIEW.csv`, `SOURCE_HASHES.json`, `PARITY.json`, `FIG01_WORDING_AND_EDGE_PARITY.json`, `S11_ANNOTATION_CONTRAST.json` and `READ_ONLY_VALIDATION.json` provide the file-specific evidence.']
    (OUT/'FINAL_PRESENTATION_FIX_LOG.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    checks['packet_pages']=pages;checks['proposed_main_and_supplement_candidates']=20;checks['packet_sha256']=sha(packet)
    checks['font_minimum_all_fixed_pt']=min(r['minimum_font_pt'] for r in rows if r['figure'] in FIXED)
    checks['ready_artwork_hash_changes']=0;checks['official_publication_artwork_hash_changes']=0
    (OUT/'READ_ONLY_VALIDATION.json').write_text(json.dumps(checks,indent=2))
    (OUT/'README.md').write_text('# Bounded final presentation fixes\n\nReview only; no promotion. Open `COMPLETE_MAIN_AND_SUPPLEMENT_FIGURE_REVIEW.pdf` for actual-size main and supplementary candidates and captions. Open `FIG01_EXACT_ORIGINAL_VS_LAYOUT.pdf` to compare the unchanged July reference against the independent 7-pt re-layout.\n\nAffected candidates have PDF, 600-dpi PNG, native preview and page-preview files here. Existing READY artwork is embedded from its unchanged registered source. S14/S15 remain optional internal evidence. See `FINAL_PRESENTATION_FIX_LOG.md` and `COMPLETE_FIGURE_PROMOTION_READINESS.md`.\n',encoding='utf-8')
    print(json.dumps({'packet_pages':pages,'science_hash_changes':0,'proposed_candidates':20,'promotion':False}))


if __name__=='__main__':main()
