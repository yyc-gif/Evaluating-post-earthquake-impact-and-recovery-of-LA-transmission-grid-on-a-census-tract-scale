#!/usr/bin/env python3
"""Read-only preflight and optional non-destructive export of Path B Figure 7 proofs.

Run in the local project checkout, where the Git LFS payloads actually exist.
No clustering/simulation is performed; no tracked or original figure is modified.

Example:
  python local_figure7_elsevier_preflight.py --repo 'C:/your/project/_pb13'
  python local_figure7_elsevier_preflight.py --repo 'C:/your/project/_pb13' --export
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError as exc:
    raise SystemExit('Install PyMuPDF into the project Python environment: pip install pymupdf') from exc

REL = Path('docs/reproducibility/path_b_pre_migration_publication_gate_20261014')
PROOFS = {
    'B_COLOR': ('FIGURE7_PATH_B_B_PRINT_FIT_7p2x9p0.pdf',
                '74e21fe27e974da18fcfa33b4700f1452b5cd87c1955624c830c1faf33bc02f8'),
    'A_TEXTURE': ('FIGURE7_PATH_B_A_PRINT_FIT_7p2x9p0.pdf',
                  '38a20d4190719a1781f090add6bbaed7400f75c835bb491841c8a61d45d9fa61'),
}
BANNER = 'PATH B AUTHOR REVIEW - NOT FORMAL STAGE 7'


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):
            h.update(b)
    return h.hexdigest()


def spans(page):
    return [s for b in page.get_text('dict', flags=0)['blocks']
            for line in b.get('lines',[]) for s in line['spans']]


def pdf_audit(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f'Figure PDF missing (Git LFS payload not materialized?): {path}')
    with fitz.open(path) as doc:
        if len(doc)!=1:
            raise ValueError(f'Expected single-page Figure 7: {path}')
        page=doc[0]
        txt=spans(page)
        widths=[]
        for d in page.get_drawings():
            w=d.get('width')
            if isinstance(w,(int,float)) and w>0:
                widths.append(float(w))
        resources=[]
        for font in page.get_fonts(full=True):
            xref=font[0]
            try:
                base, ext, typ, binary=doc.extract_font(xref)
                embedded=bool(binary)
                size=len(binary or b'')
            except Exception:
                embedded=False;size=0
            resources.append(dict(basefont=str(font[3]), subtype=str(font[2]),
                                  embedded=embedded, embedded_bytes=size))
        page_rect=page.rect
        offpage=[{'text':s['text'][:50],'bbox':list(s['bbox'])} for s in txt
                 if not page_rect.contains(fitz.Rect(s['bbox']))]
        banner=page.search_for(BANNER)
        data={
          'source':str(path), 'sha256':sha256(path),
          'page_inches':[round(page_rect.width/72,5),round(page_rect.height/72,5)],
          'normal_text_min_pt':round(min((float(s['size']) for s in txt),default=0),3),
          'font_resources':resources,
          'font_all_embedded':bool(resources) and all(f['embedded'] for f in resources),
          'raster_image_objects':len(page.get_images(full=True)),
          'vector_drawing_objects':len(page.get_drawings()),
          'min_stroke_pt':round(min(widths),3) if widths else None,
          'strokes_below_0p10':sum(w<0.099 for w in widths),
          'strokes_below_recommended_0p25':sum(w<0.249 for w in widths),
          'text_outside_page':offpage,
          'review_banner_occurrences':len(banner),
          'figure_7_dimensions_working_size_not_journal_certified':True,
          'color_quartiles_not_distinguishable_in_grayscale':path.name.startswith('FIGURE7_PATH_B_B_'),
        }
        errs=[]
        if abs(page_rect.width/72-7.2)>.01 or abs(page_rect.height/72-9.0)>.01:
            errs.append('Unexpected figure dimensions: expected 7.2 x 9.0 inches.')
        if data['normal_text_min_pt']<7.48:
            errs.append('Some text is below the working 7.5-point floor.')
        if data['raster_image_objects']!=0:
            errs.append('Raster objects found; expected purely vector figure.')
        if data['strokes_below_0p10']:
            errs.append('Stroke width below Elsevier 0.10 pt absolute minimum.')
        if not data['font_all_embedded']:
            errs.append('One or more fonts not embedded in PDF.')
        if offpage: errs.append('Text extends beyond page bounds.')
        if len(banner)!=1:
            errs.append('Expected exactly one removable review-status banner; do not export automatically.')
        data['hard_preflight_failures']=errs
        data['warnings']=[
            'Elsevier 0.25 pt is a recommended ordinary line weight, 0.10 pt an absolute minimum. Fine tract outlines require printed visual QA.',
            'The 7.2 x 9.0 inch size is a review dimension, not a confirmed journal maximum including caption space.',
            'B hue families merge in grayscale/color-deficiency simulations. Supply A and a separate accessibility explanation; neither alone is a universal accessibility certification.',
            'Keep all captions outside the submitted figure file, in an accompanying caption manuscript or the journal-designated field.'
        ]
        return data


def copy_without_review_banner(src:Path,dst:Path) -> None:
    """Remove only the upper-margin review banner in a NEW PDF; untouched source."""
    if dst.exists():
        raise FileExistsError(f'Refusing to overwrite existing export: {dst}')
    with fitz.open(src) as doc:
        page=doc[0]
        matches=page.search_for(BANNER)
        if len(matches)!=1:
            raise AssertionError(f'Expected one banner in {src}, found {len(matches)}')
        area=matches[0]+(-1,-1,1,1)
        if area.y1 >= page.rect.height*0.085:
            raise AssertionError('Banner too low; cannot safely remove without manual layout review.')
        others=[s for s in spans(page) if BANNER not in s['text']]
        if any(fitz.Rect(s['bbox']).intersects(area) for s in others):
            raise AssertionError('Scientific text intersects the review banner redaction; aborting.')
        page.add_redact_annot(area,fill=(1,1,1))
        # Keep vector graphics/images untouched; remove only intersecting text.
        page.apply_redactions(images=0,graphics=0,text=0)
        if BANNER in page.get_text():
            raise AssertionError('Banner text remains; export aborted')
        dst.parent.mkdir(parents=True,exist_ok=True)
        doc.save(dst,garbage=4,deflate=True)


def main():
    ap=argparse.ArgumentParser(description='Elsevier Path B Figure 7 working-size PDF preflight')
    ap.add_argument('--repo',required=True,type=Path,help='Local Git worktree with materialized LFS payloads')
    ap.add_argument('--export',action='store_true',help='Create non-destructive submission-style PDF copies after strict preflight')
    ap.add_argument('--accept-new-input-hashes',action='store_true',help='Allow verification of new proof revisions (report remains non-certified)')
    args=ap.parse_args()
    root=args.repo.resolve()
    src_dir=root/REL
    audit_dir=src_dir/'local_elsevier_review_outputs'
    audit_dir.mkdir(parents=True,exist_ok=True)
    audits={}
    for key,(fn,expected) in PROOFS.items():
        path=src_dir/fn
        result=pdf_audit(path)
        result['frozen_expected_sha256']=expected
        result['expected_input_hash_matches']=result['sha256']==expected
        if not result['expected_input_hash_matches']:
            result['warnings'].append('Input differs from the 2026-10-14 frozen proof; review the diff before promotion.')
            if not args.accept_new_input_hashes:
                result['hard_preflight_failures'].append('Frozen input SHA mismatch; use --accept-new-input-hashes only after checking a later revision.')
        audits[key]=result
        if args.export and not result['hard_preflight_failures']:
            name='FIG07_P2_K3_'+('B_COLOR' if key=='B_COLOR' else 'A_TEXTURE_ALTERNATIVE')+'_NO_REVIEW_BANNER.pdf'
            dst=audit_dir/name
            copy_without_review_banner(path,dst)
            result['exported_candidate']=str(dst)
            result['export_sha256']=sha256(dst)
            after=pdf_audit(dst)
            # After export only banner count changes; all geometry, data and layout must be manually reviewed.
            result['export_page_size_same']=after['page_inches']==result['page_inches']
            result['export_min_font_same']=after['normal_text_min_pt']>=result['normal_text_min_pt']-.03
            result['export_raster_objects_same']=after['raster_image_objects']==0
            if not all([result['export_page_size_same'],result['export_min_font_same'],result['export_raster_objects_same']]):
                raise AssertionError(f'Post-export preflight changed figure properties: {key}')
    audit=(audit_dir/'ELSEVIER_ARTWORK_PREFLIGHT.json')
    audit.write_text(json.dumps(audits,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    fail=sum(len(r['hard_preflight_failures']) for r in audits.values())
    print(json.dumps({'report':str(audit),'hard_failures':fail,'new_pdfs':[
        a.get('exported_candidate') for a in audits.values() if a.get('exported_candidate')],
        'message':'Proof preflight only. Color/accessibility and journal-specific acceptance require visual author review.'},indent=2))
    if fail:raise SystemExit(2)

if __name__=='__main__':
    main()
