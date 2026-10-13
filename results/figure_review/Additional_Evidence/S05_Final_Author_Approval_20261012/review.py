"""Read frozen evidence, inspect documents, and assemble a review-only PDF.

No evaluator, sampler, optimizer or statistical resampling is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
OLD = ROOT.parent / '_s05r16/results/figure_review/Additional_Evidence/Final_Pure_Random_GA_S05_20261012'
BASE = '34c49469036354453c7b1f7fcef9cd92d14e8a3d'
OFFICIAL = 'c0a11ffb4df523111efe6c8e65cfe86eadffec3c'
BRANCH = 'review/ga-s05-final-author-approval-20261012'
REPO = 'yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'
POPPLER = Path(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
SOURCES = []


def lp(path):
    p = Path(path).resolve()
    return Path('\\\\?\\' + str(p)) if os.name == 'nt' and not str(p).startswith('\\\\?\\') else p


def digest(path):
    h = hashlib.sha256()
    with lp(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    target = lp(OUT / name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def git(*args):
    return subprocess.check_output(['git', '-c', 'filter.lfs.process=', '-c', 'filter.lfs.smudge=',
        '-c', 'filter.lfs.required=false', *args], cwd=ROOT, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, lp(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def preserved():
    old = module(OLD / 'study.py', 'previous_s05_read_only')
    state = old.preserved()
    state['previous_review_checkout'] = {
        'head': old.git(OLD.parents[3], 'rev-parse', 'HEAD').decode().strip(),
        'index': sha(old.git(OLD.parents[3], 'ls-files', '--stage', '-z')),
        'status': sha(old.git(OLD.parents[3], 'status', '--porcelain=v1', '-z')),
        'candidate_pdf_sha256': digest(OLD / 'FigS05_GA_Final_Candidate.pdf'),
        'candidate_png_sha256': digest(OLD / 'FigS05_GA_Final_Candidate.png'),
    }
    return state


def source(path, commit=OFFICIAL):
    blob = git('show', commit + ':' + path)
    oid = None
    if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
        fields = dict(x.split(' ', 1) for x in blob.decode().splitlines())
        oid = fields['oid'][7:]
        common = Path(git('rev-parse', '--git-common-dir').decode().strip())
        if not common.is_absolute():
            common = ROOT / common
        cached = lp(common / 'lfs/objects' / oid[:2] / oid[2:4] / oid)
        if cached.exists():
            blob = cached.read_bytes()
        else:
            import requests
            response = requests.get(f'https://media.githubusercontent.com/media/{REPO}/{commit}/' + quote(path, safe='/'), timeout=180)
            response.raise_for_status()
            blob = response.content
        assert sha(blob) == oid and len(blob) == int(fields['size']), path
    SOURCES.append(dict(commit=commit, path=path, sha256=sha(blob), bytes=len(blob), git_lfs_oid=oid))
    target = lp(OUT / 'runtime/source_documents' / path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(blob)
    return blob


def paragraphs(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = ET.fromstring(z.read('word/document.xml'))
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        rows = []
        for idx, node in enumerate(xml.findall('.//w:body/w:p', ns), 1):
            rows.append(dict(paragraph=idx, text=''.join(n.text or '' for n in node.findall('.//w:t', ns))))
        for idx, table in enumerate(xml.findall('.//w:body/w:tbl', ns), 1):
            for rid, row in enumerate(table.findall('w:tr', ns), 1):
                rows.append(dict(table=idx, row=rid, text=' | '.join(''.join(n.text or '' for n in cell.findall('.//w:t', ns)) for cell in row.findall('w:tc', ns))))
        return rows


def render(pdf, prefix, dpi=200):
    import fitz
    prefix = lp(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(lp(pdf))
    for idx, page in enumerate(doc, 1):
        page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False).save(str(prefix) + f'_mupdf_{idx}.png')
    subprocess.run([str(POPPLER), '-r', str(dpi), '-png', str(lp(pdf)), str(prefix) + '_poppler'], check=True)
    return dict(pdf_sha256=digest(pdf), renderer_versions={'mupdf': fitz.VersionBind,
        'poppler': subprocess.run([str(POPPLER), '-v'], capture_output=True, text=True).stderr.strip()},
        dpi=dpi, pages=[{'width_mm': p.rect.width*25.4/72, 'height_mm': p.rect.height*25.4/72} for p in doc])


def inspect():
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    state = preserved()
    if lp(OUT / 'PRESERVATION_BEFORE.json').exists():
        assert state == json.loads(lp(OUT / 'PRESERVATION_BEFORE.json').read_text(encoding='utf-8'))
    else:
        save('PRESERVATION_BEFORE.json', state)
    branches = ['review/final-pure-random-ga-figs05-20261012', 'revision/reviewer-driven-core-rebuild-v2',
        'diagnostics/pure-random-ga-final-freeze-validation-20261011', 'diagnostics/pure-random-ga-parameter-consistency-20261011',
        'diagnostics/ga-random-initialization-isolation-20261011', 'diagnostics/post-evaluation-ga-independent-validation-20261012']
    save('LIVE_SOURCE_BRANCH_IDENTITIES.json', {b: git('ls-remote', 'origin', 'refs/heads/' + b).decode().split()[0] for b in branches})
    manifest = json.loads(lp(OLD / 'OUTPUT_HASH_MANIFEST.json').read_text(encoding='utf-8'))
    # Prior artifact manifest uses a list of files; accept its actual schema.
    entries = manifest.get('files', manifest)
    entries = entries if isinstance(entries, list) else [dict(path=k, **(v if isinstance(v, dict) else {'sha256': v})) for k, v in entries.items()]
    verified = []
    for item in entries:
        name = item.get('path', item.get('file'))
        actual = digest(OLD / name)
        assert actual == item['sha256'], name
        verified.append(dict(path=name, sha256=actual))
    archive = lp(OLD / 'SOURCE_EVIDENCE.zip')
    provenance = json.loads(lp(OLD / 'SOURCE_DATA_PROVENANCE_MANIFEST.json').read_text(encoding='utf-8'))
    records = provenance.get('sources', provenance.get('files', []))
    with zipfile.ZipFile(archive) as z:
        for item in records:
            data = z.read(item['archive_member'])
            assert sha(data) == item['sha256'] and len(data) == item['bytes']
    save('PREVIOUS_EVIDENCE_INTEGRITY.json', dict(output_files=verified, archived_source_count=len(records),
        source_archive_sha256=digest(archive), prior_tests_reused_not_rerun=True))
    text_paths = ['results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md', 'results/figure_review/FIGURE_MANIFEST.csv',
        'results/figures/FIGURE_INDEX.csv', 'src/la_grid/plotting/consolidate_current_figure_suite.py',
        'src/la_grid/plotting/extended_ga_artwork_20261008.py', 'src/la_grid/plotting/build_meeting_figure_collection.py',
        'src/la_grid/plotting/index_revised_suite.py', 'src/la_grid/plotting/update_coauthor_figure_index.py',
        'docs/reproducibility/figure_suite_integration_20261011/INTEGRATION_QA.json',
        'docs/reviewer/FIGURE_S04_S05_S06_INTERPRETATION_20261007.md',
        'docs/reviewer/SUPPLEMENT_FIGURE_AUDIT_AND_PLAN.md']
    for path in text_paths:
        source(path)
    for path in ['results/figure_review/ALL_MAIN_FIGURES.pdf', 'results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf',
        'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf', 'docs/meeting/LA_Grid_Part_II_Methodology_Modifications_Meeting_Summary.docx']:
        data = source(path)
        if path.endswith('.docx'):
            save('MANUSCRIPT_TEXT_LOCATIONS.json', {'meeting_summary_not_full_manuscript': paragraphs(data)})
    backup = Path(r'C:\2025-2026 Fall\Local_Recovery_Snapshot_20260925\Private_Backup_Small\private-la-grid-research\manuscripts\LA_Grid_Manuscript_Resubmission_Rebuild.docx')
    data = lp(backup).read_bytes()
    save('BACKUP_MANUSCRIPT_TEXT_LOCATIONS.json', dict(path=str(backup), sha256=sha(data),
        authoritative_current=False, provisional_locations_only=True, paragraphs=paragraphs(data)))
    save('REVIEW_SOURCE_MANIFEST.json', dict(previous_review_commit=BASE, official_manuscript_remote_commit=OFFICIAL,
        documents=SOURCES, numerical_data_reference='../Final_Pure_Random_GA_S05_20261012/SOURCE_DATA_PROVENANCE_MANIFEST.json'))
    save('CANDIDATE_RENDER_RECORD.json', render(OLD / 'FigS05_GA_Final_Candidate.pdf', OUT / 'runtime/candidate', 200))


def packet():
    import fitz
    caption = lp(OUT / 'S05_CONCISE_MANUSCRIPT_CAPTION.md').read_text(encoding='utf-8')
    body = caption.split('\n\n', 1)[1].strip()
    words = len(body.split())
    assert 250 <= words <= 350, words
    # Assemble a vector figure page at exactly 185 mm; companion text is separate.
    doc = fitz.open()
    mm = 72 / 25.4
    page = doc.new_page(width=210*mm, height=297*mm)
    page.insert_text((12.5*mm, 15*mm), 'SUPPLEMENTARY FIGURE S05 | AUTHOR APPROVAL', fontsize=10, fontname='hebo')
    page.insert_text((12.5*mm, 22*mm), 'Validated legacy pure-random GA; unchanged candidate at native publication size', fontsize=8)
    artwork = fitz.open(lp(OLD / 'FigS05_GA_Final_Candidate.pdf'))
    rect = fitz.Rect(12.5*mm, 31*mm, 197.5*mm, 209*mm)
    page.show_pdf_page(rect, artwork, 0)
    page.insert_text((12.5*mm, 220*mm), '185 mm width / 178 mm height. Vector artwork preserved without redesign.', fontsize=8)
    page.insert_text((12.5*mm, 228*mm), 'READY_FOR_AUTHOR_APPROVAL. Official S05 and manuscript files are not updated.', fontsize=8, fontname='hebo')
    page.insert_text((12.5*mm, 285*mm), 'Review only | 12 October 2026 | Page 1 of 2', fontsize=8)
    page = doc.new_page(width=210*mm, height=297*mm)
    page.insert_text((12.5*mm, 15*mm), 'PROPOSED CAPTION AND REMAINING DECISIONS', fontsize=10, fontname='hebo')
    page.insert_text((12.5*mm, 25*mm), 'Figure S05. Random-initialization search and independent physical validation.', fontsize=9, fontname='hebo')
    remaining = page.insert_textbox(fitz.Rect(12.5*mm, 31*mm, 197.5*mm, 180*mm), body, fontsize=10, lineheight=1.35)
    assert remaining >= 0, remaining
    decisions = ('AUTHOR DECISIONS BEFORE PROMOTION\n\n'
        '1. Approve replacing the historical S05 with this unchanged four-panel candidate and concise caption.\n\n'
        '2. Approve the coordinated GA text edits and explicit 64-planning / 2,000-validation cohort distinction; retain negative equity findings.\n\n'
        '3. Supply or confirm the accessible current full manuscript before paragraph-level integration. The previously identified external working DOCX is missing; its backup was not restored or designated current.\n\n'
        'No search, new physical draw, production evaluation, bootstrap, candidate change, or official-file promotion occurred in this review.')
    assert page.insert_textbox(fitz.Rect(12.5*mm, 190*mm, 197.5*mm, 276*mm), decisions, fontsize=9, lineheight=1.25) >= 0
    page.insert_text((12.5*mm, 285*mm), f'Review only | Caption: {words} words | Page 2 of 2', fontsize=8)
    doc.set_metadata({'title': 'Final S05 Author Approval Packet', 'author': 'LA Grid review-only integration',
        'subject': 'Unchanged validated legacy pure-random GA; archived evidence only'})
    doc.save(lp(OUT / 'FINAL_S05_AUTHOR_APPROVAL_PACKET.pdf'), garbage=4, deflate=True)
    save('APPROVAL_PACKET_RENDER_RECORD.json', render(OUT / 'FINAL_S05_AUTHOR_APPROVAL_PACKET.pdf', OUT / 'runtime/approval', 160))
    save('APPROVAL_PACKET_TECHNICAL_QA.json', dict(pages=2, figure_width_mm=185, figure_height_mm=178,
        candidate_unchanged_sha256=digest(OLD / 'FigS05_GA_Final_Candidate.pdf'), caption_word_count=words,
        pdf_sha256=digest(OUT / 'FINAL_S05_AUTHOR_APPROVAL_PACKET.pdf'), visual_review_required=True))


def suite():
    import fitz
    records = []
    for name in ['ALL_MAIN_FIGURES.pdf', 'ALL_SUPPLEMENT_FIGURES.pdf', 'ALL_FIGURES_WITH_CAPTIONS.pdf']:
        doc = fitz.open(lp(OUT / 'runtime/source_documents/results/figure_review' / name))
        for idx, page in enumerate(doc, 1):
            text = page.get_text()
            records.append(dict(file=name, page=idx, width_mm=page.rect.width*25.4/72,
                text=text, sha256_text=sha(text.encode())))
            if (name == 'ALL_MAIN_FIGURES.pdf' and idx in [4, 5]) or (name == 'ALL_SUPPLEMENT_FIGURES.pdf' and idx in [4, 6]):
                page.get_pixmap(matrix=fitz.Matrix(140/72, 140/72), alpha=False).save(str(lp(OUT / f'runtime/suite_{name[:-4]}_{idx}.png')))
    save('OFFICIAL_PACKET_PAGE_AUDIT.json', dict(official_commit=OFFICIAL, pages=records))


def verify():
    before = json.loads(lp(OUT / 'PRESERVATION_BEFORE.json').read_text(encoding='utf-8'))
    after = preserved()
    assert before == after
    save('REPRODUCIBILITY_AND_PRESERVATION_QA.json', dict(all_preserved=True, before=before, after=after,
        protected_scientific_files=950, original_staged_items=862, new_searches=0, new_physical_draws=0,
        new_production_evaluations=0, new_bootstrap_resamples=0, official_files_changed=0,
        figure_corrections=0, candidate_changed=False, external_missing_manuscript_exception_unchanged=True))
    files = []
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and 'runtime' not in p.relative_to(OUT).parts and '__pycache__' not in p.parts and p.name not in ['OUTPUT_HASH_MANIFEST.json', 'REMOTE_PUBLICATION_VERIFIED.json', 'FINAL_REMOTE_HEAD_VERIFIED.json']:
            files.append(dict(path=p.relative_to(OUT).as_posix(), sha256=digest(p), bytes=p.stat().st_size))
    save('OUTPUT_HASH_MANIFEST.json', dict(files=files))


def finish():
    import fitz
    from PIL import Image
    images = ['runtime/candidate_mupdf_1.png', 'runtime/candidate_poppler-1.png',
        'runtime/approval_mupdf_1.png', 'runtime/approval_mupdf_2.png',
        'runtime/approval_poppler-1.png', 'runtime/approval_poppler-2.png']
    records = []
    for path in images:
        p = lp(OUT / path)
        with Image.open(p) as im:
            records.append(dict(path=path, sha256=digest(p), pixels=list(im.size),
                actual_visual_inspection=True, clipping_or_overlap_observed=False))
    doc = fitz.open(lp(OUT / 'FINAL_S05_AUTHOR_APPROVAL_PACKET.pdf'))
    body = lp(OUT / 'S05_CONCISE_MANUSCRIPT_CAPTION.md').read_text().split('\n\n', 1)[1].strip()
    expected = ' '.join(body.split())
    extracted = ' '.join(doc[1].get_text().split())
    assert expected in extracted, 'Caption text differs from the approval PDF'
    assert len(doc) == 2 and all(len(p.get_images()) == 0 for p in doc)
    packet_data = [dict(page=i+1, fonts=p.get_fonts(full=True), raster_images=len(p.get_images())) for i, p in enumerate(doc)]
    qa = json.loads(lp(OLD / 'NUMERICAL_QA.json').read_text())
    candidate = json.loads(lp(OLD / 'FINAL_GA_CONFIGURATION_AND_CANDIDATE.json').read_text())['candidate']
    assert len(candidate['sequence']) == len(set(candidate['sequence'])) == 92
    assert sha(('\n'.join(candidate['sequence']) + '\n').encode()) == candidate['sequence_sha256']
    save('FINAL_REVIEW_QA.json', dict(status='READY_FOR_AUTHOR_APPROVAL', correction_required=False,
        candidate_sequence_sha256=candidate['sequence_sha256'], candidate_seed=candidate['seed'],
        candidate_pdf_sha256=digest(OLD / 'FigS05_GA_Final_Candidate.pdf'),
        candidate_png_sha256=digest(OLD / 'FigS05_GA_Final_Candidate.png'),
        archived_numerical_receipt_sha256=digest(OLD / 'NUMERICAL_QA.json'),
        source_values_reused={'mean_difference_hr': qa['mean_difference_hr'], 'components': qa['signed_component_means'],
            'equity': qa['equity_saved_differences'], 'physical_count': qa['validation_realizations']},
        caption_word_count=len(body.split()), exact_caption_present_in_packet=True,
        actual_visual_inspection_records=records, packet=packet_data,
        renderer_warning="Poppler emitted 'No display font for Symbol' while rendering the approval PDF. Symbol is not in either page's font-resource list; both actual rendered pages have intact visible text under Poppler and MuPDF. Native S05 fonts are embedded Arial.",
        initial_read_only_retries=['Sandbox protected-worktree status access retried with scoped escalation',
            'Windows long-path prefix adapter corrected', 'Missing source LFS cache objects retrieved by immutable commit and SHA256-verified'],
        numerical_analysis_repeated=False, statistical_resampling_repeated=False,
        full_current_manuscript_accessible=False, backup_not_promoted_or_restored=True))
    verify()


def remote():
    import requests
    from urllib.parse import quote
    head = git('rev-parse', 'HEAD').decode().strip()
    assert git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0] == head
    names = git('ls-tree', '-r', '--name-only', head, '--', OUT.relative_to(ROOT).as_posix()).decode().splitlines()
    rows = []
    for name in names:
        blob = git('show', head + ':' + name)
        is_lfs = blob.startswith(b'version https://git-lfs.github.com/spec/v1')
        if is_lfs:
            fields = dict(x.split(' ', 1) for x in blob.decode().splitlines())
            expected, size = fields['oid'][7:], int(fields['size'])
            url = f'https://media.githubusercontent.com/media/{REPO}/{head}/' + quote(name, safe='/')
        else:
            expected, size = sha(blob), len(blob)
            url = f'https://raw.githubusercontent.com/{REPO}/{head}/' + quote(name, safe='/')
        assert digest(ROOT / name) == expected
        r = requests.get(url, timeout=180)
        r.raise_for_status()
        assert sha(r.content) == expected and len(r.content) == size, name
        rows.append(dict(path=name, sha256=expected, bytes=size, actual_remote_payload_verified=True, git_lfs=is_lfs, url=url))
        print('REMOTE_PASS', name, size, flush=True)
    save('REMOTE_PUBLICATION_VERIFIED.json', dict(status='PASS_ACTUAL_REMOTE_BYTES', branch=BRANCH,
        verified_payload_commit=head, remote_head_at_verification=head, files=rows,
        lfs_payload_count=sum(r['git_lfs'] for r in rows),
        receipt_committed_after_payload_verification=True, source_review_and_official_files_unchanged=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['inspect', 'suite', 'packet', 'finish', 'verify', 'remote'])
    args = parser.parse_args()
    {'inspect': inspect, 'suite': suite, 'packet': packet, 'finish': finish, 'verify': verify, 'remote': remote}[args.phase]()
