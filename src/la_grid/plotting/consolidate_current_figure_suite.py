"""Integrate exact reviewed artwork; never evaluate or redraw scientific results.

Run from this checkout with Python. Source commits and selected paths are pinned.
The shared Git LFS store supplies verified payloads; no source directory is an
author-facing dependency. A future clone may fetch the two pinned source commits
and their LFS objects before reproducing this presentation-only integration.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys

import fitz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[3]
BASE = '031d2c675f8e7d58035d27448be040b809ced086'
REVIEW = '5f099e651de751f91553d2df920dca9cbc02eea6'
REVIEW_DIR = 'results/figure_review/author_review_targeted_20261011'
ORIGINAL = Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
DEST = ROOT / 'results/figure_review'
QA = ROOT / 'docs/reproducibility/figure_suite_integration_20261011'
MM = 72 / 25.4
SELECTED = {
    'Main/Fig01': ('Fig01_Author_Review', 'Smaller framework markers; clearer Stage 5 outcomes and schematic Q1-Q4 differences.'),
    'Main/Fig03': ('Fig03_Low_End_Palette', 'Only the light end of the E sequential palette is strengthened; T80 definition is explicit.'),
    'Main/Fig05': ('Fig05_Q4_Context_Candidate', 'Thin outer Q4-area outlines provide geographic context on all three reference-effect maps.'),
    'Main/Fig07': ('Fig07_Cluster_Color_Candidate', 'C4 cyan is replaced by restrained slate; formal five-class membership is retained.'),
    'Supplement/FigS03': ('Supplement_Followup/FigS03_Candidate', 'Transparent origin/task points; matrix station IDs omitted; directed matrix retained.'),
    'Supplement/FigS06': ('Supplement_Followup/FigS06_Candidate', 'B identifies joint removal of both gates; separate threshold panels disclose the available controls.'),
    'Supplement/FigS07': ('Supplement_Followup/FigS07_Candidate', 'Four focal and two other policies separated in A/B; keys show only plotted curves; conditional source access explained.'),
    'Supplement/FigS09': ('FigS09_Palette_Synchronization', 'C4 palette synchronized with Figure 7.'),
    'Supplement/FigS10': ('Supplement_Followup/FigS10_Candidate', 'Only C population shading changes to neutral gray; exact scale and map geometry retained.'),
    'Supplement/FigS11': ('Supplement_Followup/FigS11_Candidate', 'Common signed-log colors expose small effects; actual hour labels and original limits retained across all four scenarios.'),
}
FIGURES = [f'Main/Fig{i:02d}' for i in range(1, 8)] + [f'Supplement/FigS{i:02d}' for i in [1, *range(3, 14)]]


def lp(p):
    p = str(Path(p).resolve())
    return p if p.startswith('\\\\?\\') else '\\\\?\\' + p


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(p):
    h = hashlib.sha256()
    with open(lp(p), 'rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def git(*args, root=ROOT):
    env = os.environ.copy()
    env['GIT_OPTIONAL_LOCKS'] = '0'
    return subprocess.check_output(['git', '-C', str(root), *args], env=env)


def payload(commit, rel):
    blob = git('show', f'{commit}:{rel}')
    m = re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)', blob)
    if not m:
        return blob
    expected, size = m.group(1).decode(), int(m.group(2))
    common = Path(git('rev-parse', '--path-format=absolute', '--git-common-dir').decode().strip())
    paths = [common / 'lfs/objects' / expected[:2] / expected[2:4] / expected,
             ROOT.parent / '_fr11' / rel, ORIGINAL / rel, ROOT / rel]
    for p in paths:
        try:
            if os.path.getsize(lp(p)) == size and sha(p) == expected:
                return open(lp(p), 'rb').read()
        except (FileNotFoundError, OSError):
            pass
    raise FileNotFoundError(f'Missing actual LFS bytes: {commit}:{rel} ({expected})')


def write(path, data):
    Path(lp(path.parent)).mkdir(parents=True, exist_ok=True)
    with open(lp(path), 'wb') as f:
        f.write(data.encode('utf-8') if isinstance(data, str) else data)


def dump(path, data):
    write(path, json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def csv_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))


def write_csv(path, rows, fields=None):
    out = io.StringIO(newline='')
    w = csv.DictWriter(out, fieldnames=fields or list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    write(path, out.getvalue())


def captions(text):
    text = text.replace('\r\n', '\n')
    return {h: b.strip() for h, b in re.findall(r'^## (.+?)\n\n(.*?)(?=^## |\Z)', text, re.M | re.S)}


def protected_snapshot(reference):
    paths = reference['protected_files']
    actual = {rel: sha(ORIGINAL / rel) for rel in paths}
    index = git('rev-parse', '--path-format=absolute', '--git-path', 'index', root=ORIGINAL).decode().strip()
    status = git('status', '--porcelain=v1', '-z', root=ORIGINAL)
    staged = git('diff', '--cached', '--name-only', '-z', root=ORIGINAL)
    return {'original_HEAD': git('rev-parse', 'HEAD', root=ORIGINAL).decode().strip(),
            'protected_files': actual, 'protected_count': len(actual),
            'index_sha256': sha(index), 'status_sha256': digest(status),
            'staged_names_sha256': digest(staged),
            'staged_count': len([p for p in staged.split(b'\0') if p])}


def caption_pdf(heading, body):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    title = Paragraph(escape(heading), ParagraphStyle('title', fontName='SuiteBold', fontSize=11, leading=14))
    p = Paragraph(escape(body).replace('\n', '<br/>'), ParagraphStyle('body', fontName='SuiteArial', fontSize=10, leading=13))
    width, height = A4
    usable = 185 * MM
    th = title.wrap(usable, height)[1]
    ph = p.wrap(usable, height)[1]
    if ph + th + 12 > height - 32 * MM:
        raise ValueError(f'Caption does not fit without shrinking text: {heading}')
    x = (width - usable) / 2
    y = height - 18 * MM
    title.drawOn(c, x, y - th)
    p.drawOn(c, x, y - th - 12 - ph)
    c.showPage()
    c.save()
    return fitz.open(stream=buf.getvalue(), filetype='pdf')


def main():
    reference = json.loads(payload(REVIEW, REVIEW_DIR + '/PRESERVATION_BEFORE.json'))
    before = protected_snapshot(reference)
    assert before['protected_files'] == reference['protected_files'], 'Original protected bytes changed before integration'
    dump(QA / 'PRESERVATION_BEFORE.json', before)
    evidence = [
        'ARTWORK_EDIT_RECORDS.json', 'NUMERICAL_INVARIANCE_QA.json', 'QUARTILE_AND_DEGREE_PROVENANCE.json',
        'Supplement_Followup/NUMERICAL_INVARIANCE_QA.json', 'Supplement_Followup/SOURCE_HASHES.json',
    ]
    evidence_hashes = {}
    for rel in evidence:
        data = payload(REVIEW, REVIEW_DIR + '/' + rel)
        evidence_hashes[rel] = digest(data)
        write(QA / 'reviewed_source_qa' / rel, data)

    original_caps = captions(payload(BASE, 'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    merged = dict(original_caps)
    for rel in ['PROPOSED_CAPTIONS.md', 'Supplement_Followup/PROPOSED_CAPTIONS.md']:
        revised = captions(payload(REVIEW, REVIEW_DIR + '/' + rel).decode())
        assert len(revised) == (5 if rel.startswith('Supplement_Followup/') else 6), rel
        merged.update(revised)
    assert len(merged) == len(original_caps) == 19
    f1 = next(k for k in merged if k.startswith('Figure 1.'))
    merged[f1] = re.sub(r' The community-outcome stage separates cumulative service loss,.*?Community typology and hotspot scores describe spatial patterns\.', '', merged[f1])
    # Remove review-only wording; preserve the scientific distinction itself.
    f5 = next(k for k in merged if k.startswith('Figure 5.'))
    merged[f5] = merged[f5].replace('and is retained in the companion review evidence', '')
    merged[f5] = merged[f5].replace('preserves which quartile has more loss ;', 'preserves which quartile has more loss;')
    merged[f5] = merged[f5].replace('at 57 crews and', 'at reference crew availability and')
    write(DEST / 'MANUSCRIPT_FACING_CAPTIONS.md', '# Manuscript-facing figure captions\n\n' +
          '\n\n'.join('## ' + h + '\n\n' + merged[h] for h in original_caps) + '\n')

    manifest_old = csv_rows(payload(BASE, 'results/figure_review/FIGURE_MANIFEST.csv'))
    index = csv_rows(payload(BASE, 'results/figures/FIGURE_INDEX.csv'))
    manifest = []
    source_records = []
    figure_info = {}
    mirror_by_current = {r['source_path']: r for r in index}
    for stem in FIGURES:
        changed = stem in SELECTED
        commit = REVIEW if changed else BASE
        selected = REVIEW_DIR + '/' + SELECTED[stem][0] if changed else 'results/figure_review/' + stem
        for ext in ['pdf', 'png']:
            rel = stem + '.' + ext
            source_rel = selected + '.' + ext
            data = payload(commit, source_rel)
            write(DEST / rel, data)
            assert sha(DEST / rel) == digest(data)
            if ext == 'pdf':
                doc = fitz.open(stream=data, filetype='pdf')
                assert len(doc) == 1
                p = doc[0]
                spans = [s for b in p.get_text('dict')['blocks'] for l in b.get('lines', []) for s in l['spans']]
                info = {'size_mm': [p.rect.width / MM, p.rect.height / MM],
                        'min_font_pt': min(s['size'] for s in spans),
                        'page_count': len(doc), 'image_count': len(p.get_images())}
                assert abs(info['size_mm'][0] - 185) < .05
                figure_info[stem] = info
                pix = p.get_pixmap(matrix=fitz.Matrix(160/72, 160/72), alpha=False)
                pix.set_dpi(160, 160)
                Path(lp(DEST / 'Page_Previews')).mkdir(parents=True, exist_ok=True)
                pix.save(lp(DEST / 'Page_Previews' / (Path(stem).name + '.png')))
                doc.close()
            row = next(r for r in manifest_old if r['final_name'] == rel).copy()
            row.update(source_file=source_rel, source_commit=commit, sha256=digest(data),
                       size_mm=' x '.join(f'{v:.3f}' for v in figure_info[stem]['size_mm']),
                       min_font_pt=f"{figure_info[stem]['min_font_pt']:.3f}",
                       status='CURRENT_AUTHOR_REVIEW_SET', current_source_file='results/figure_review/' + rel)
            row['change_in_this_update'] = 'UPDATED' if changed else 'RETAINED'
            idx = mirror_by_current['results/figure_review/' + rel]
            mirror_rel = 'results/figures/' + idx['file']
            write(ROOT / mirror_rel, data)
            assert sha(ROOT / mirror_rel) == digest(data)
            row['mirror_file'] = mirror_rel
            manifest.append(row)
            source_records.append({'current_file': 'results/figure_review/' + rel, 'source_file': source_rel,
                                   'source_commit': commit, 'sha256': digest(data), 'bytes': len(data),
                                   'mirror_file': mirror_rel, 'change': row['change_in_this_update']})
            idx.update(sha256_or_lfs_oid=digest(data), current_status='CURRENT_AUTHOR_REVIEW_SET',
                       submission_status='Current integrated author-review set',
                       notes=SELECTED[stem][1] if changed else 'Retained current numbered artwork; included in the unified packet.')
    write_csv(DEST / 'FIGURE_MANIFEST.csv', manifest)
    for row in index:
        if '/FigS05.' in row['source_path']:
            row.update(scientific_question='What do the finite GA search budgets and exploratory evaluation establish?',
                       main_message='Separate retained-incumbent behavior, expanded planning search and exploratory outcome comparisons.',
                       scientific_content='Original and expanded finite search budgets and exploratory evaluation; formal strategy results unchanged.')
        if '/FigS11.' in row['source_path']:
            row.update(scientific_question='How do the six selected policy-outcome contrasts vary across four earthquake scenarios?',
                       main_message='Actual mean hour contrasts relative to Unconstrained across four scenarios; signed-log colors retain original limits.',
                       scientific_content='Cross-hazard selected-policy mean contrasts; historical and 2pc50 fragility parameterizations differ.')
    write_csv(ROOT / 'results/figures/FIGURE_INDEX.csv', index)

    pdfmetrics.registerFont(TTFont('SuiteArial', 'C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('SuiteBold', 'C:/Windows/Fonts/arialbd.ttf'))
    main_doc, supp_doc, full_doc = fitz.open(), fitz.open(), fitz.open()
    for stem, heading in zip(FIGURES, original_caps):
        figure = fitz.open(lp(DEST / (stem + '.pdf')))
        (main_doc if stem.startswith('Main/') else supp_doc).insert_pdf(figure)
        full_doc.insert_pdf(figure)
        cap = caption_pdf(heading, merged[heading])
        full_doc.insert_pdf(cap)
        cap.close()
        figure.close()
    # Preserve the two pre-existing complementary evidence pages and captions.
    previous = fitz.open(stream=payload(BASE, 'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'), filetype='pdf')
    assert len(previous) == 42
    full_doc.insert_pdf(previous, from_page=38, to_page=41)
    for name, doc in [('ALL_MAIN_FIGURES', main_doc), ('ALL_SUPPLEMENT_FIGURES', supp_doc), ('ALL_FIGURES_WITH_CAPTIONS', full_doc)]:
        doc.save(lp(DEST / (name + '.pdf')), garbage=4, deflate=True)
        doc.close()
    previous.close()

    first = 'This is the single author-review source for the current submission figure set. Do not retrieve submission figures from older review folders.'
    write(DEST / 'README.md', first + '\n\n' + '''# Current complete figure suite

Use this directory on `revision/reviewer-driven-core-rebuild-v2` for every review.

- [Complete figures and captions](ALL_FIGURES_WITH_CAPTIONS.pdf): Main Fig01-07, then FigS01 and FigS03-13, each immediately followed by its caption. The two existing complementary evidence figures follow the numbered set.
- [Main](Main/): seven current figures, vector PDF and exact 600-dpi PNG.
- [Supplement](Supplement/): twelve current figures, vector PDF and exact 600-dpi PNG. S02 initial-service content is integrated into S01; there is no missing S02 file.
- [Captions](MANUSCRIPT_FACING_CAPTIONS.md): current scientific definitions, intervals, references and interpretation boundaries.
- [What changed](UPDATE_LOG.md): every numbered figure, including retained files.
- [Manifest](FIGURE_MANIFEST.csv): exact source commit, payload hash, native size and minimum font for every PDF/PNG.
- [Publication-size previews](Page_Previews/): all nineteen numbered PDFs rendered at their native 185-mm width.
- [Main-only packet](ALL_MAIN_FIGURES.pdf) and [Supplement-only packet](ALL_SUPPLEMENT_FIGURES.pdf).

The same current artwork is synchronized byte-for-byte into `results/figures/`; it is not an alternative version. No author needs to switch to an analysis/review branch or retrieve a numbered figure from a historical directory. Historical evidence remains in Git and provenance records.

The six scheduled manuscript policies are Degree-first, Betweenness-first, Impact-first, Hospital-first, Vulnerability-first and Random, plus Unconstrained. The formal five-cluster Figure 7 is retained; exploratory CORE3/W1 classifications are not substituted. S05 separates original incumbent-preserving search, expanded finite budgets and exploratory evaluation; it does not replace formal strategies. S06 concerns dependency and service-model assumptions. S11 shows all four earthquake scenarios, with actual mean hour labels and a disclosed signed-log color scale.

The integration changes presentation and explanations only. Scientific numerical tables, vulnerability quartiles, five-cluster memberships, trajectories, simulations, mapping, scheduler, GA results and manuscripts remain unchanged. S14/S15 are internal evidence; S16 remains a review aid. None is added to the numbered submission set.
''')
    lines = ['# Complete-suite update log', '', f'Scientific and artwork baseline: `{BASE}`.',
             f'Reviewed presentation source: `{REVIEW}`.', '',
             'The entire current numbered set is in Main/ and Supplement/ on the revision branch. Exact reviewed PDF/PNG bytes are copied; no scientific result is recalculated.', '',
             '| Figure | Action | Change | Current PDF |', '|---|---|---|---|']
    for stem in FIGURES:
        action = 'UPDATED' if stem in SELECTED else 'RETAINED'
        reason = SELECTED[stem][1] if stem in SELECTED else ('FIGURE 4: RETAIN CURRENT DESIGN. Distributional gap detail remains in Figure 5.' if stem == 'Main/Fig04' else 'Current numbered artwork retained exactly.')
        lines.append(f'| {Path(stem).name} | {action} | {reason} | [{Path(stem).name}]({stem}.pdf) |')
    lines += ['', 'All captions are collected in MANUSCRIPT_FACING_CAPTIONS.md. Figure 4 artwork is unchanged; its clarified reviewed caption is integrated. S05/S11 index text is reconciled with their actual current panels. The complete packet keeps native 185-mm artwork pages and ten-point caption text, without scaling figures down.', '',
              'Source numerical-invariance and protected-file checks are retained in docs/reproducibility/figure_suite_integration_20261011. The manifest is the payload authority, not a claim that every prior presentation issue was independently solved in this integration. No formal Stage 7 or GA replacement is performed.']
    write(DEST / 'UPDATE_LOG.md', '\n'.join(lines) + '\n')
    # Fix stale descriptions without changing additional evidence or index data.
    rel = 'results/figure_review/Additional_Evidence/README.md'
    text = payload(BASE, rel).decode().replace('The 20 numbered figures', 'The 19 numbered figures')
    text = text.replace('retains the complete four-scenario policy evidence formerly shown in S11. The numbered S11 provides a compact 2pc50 view; no historical-scenario result was deleted.',
                        'retains the complete experimental four-scenario policy evidence. The numbered S11 displays all four scenarios for the six selected manuscript policies; the larger experimental record remains available here.')
    write(ROOT / rel, text)
    write(ROOT / 'results/figures/README.md', '# Synchronized current artwork\n\nThe author-review entry is [results/figure_review](../figure_review/README.md), including the [complete packet](../figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf) and [all changes](../figure_review/UPDATE_LOG.md).\n\nThese nineteen PDF/PNG pairs are byte-identical mirrors of the current numbered files in that directory. FIGURE_INDEX.csv records their mapping and exact hashes. There is one current artwork version, on the revision branch. S02 is integrated into S01. Formal scientific results are unchanged.\n')
    gallery = ['<!doctype html><html><head><meta charset="utf-8"><title>Current figure suite</title>',
               '<style>body{font:16px Arial;max-width:900px;margin:32px auto}img{width:100%;height:auto}section{margin:36px 0}</style></head><body>',
               '<h1>Current figure suite</h1><p><a href="../figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf">Complete figures and captions</a> | <a href="../figure_review/UPDATE_LOG.md">Every change</a></p>']
    for stem in FIGURES:
        gallery += [f'<section><h2>{Path(stem).name}</h2><a href="../figure_review/{stem}.pdf">Vector PDF</a>',
                    f'<img loading="lazy" src="../figure_review/Page_Previews/{Path(stem).name}.png" alt="{Path(stem).name}"></section>']
    write(ROOT / 'results/figures/FIGURE_REVIEW_GALLERY.html', '\n'.join(gallery) + '</body></html>\n')
    after = protected_snapshot(reference)
    assert before == after, 'Original worktree/index/protected science changed'
    dump(QA / 'PRESERVATION_AFTER.json', after)
    audit = {'baseline_commit': BASE, 'reviewed_source_commit': REVIEW, 'figures': source_records,
             'native_pdf_metrics': figure_info, 'reviewed_numerical_qa_sha256': evidence_hashes,
             'protected_file_count': before['protected_count'], 'staged_item_count': before['staged_count'],
             'original_worktree_unchanged': before == after, 'scientific_results_recomputed': False,
             'packet_pages': {'main': 7, 'supplement': 12, 'with_captions': 42},
             'captions': list(original_caps), 's02': 'Merged into S01 in baseline; not recreated',
             'updated_figures': list(SELECTED), 'retained_figures': [s for s in FIGURES if s not in SELECTED]}
    dump(QA / 'INTEGRATION_QA.json', audit)
    print(json.dumps({'numbered_figures': len(FIGURES), 'updated': len(SELECTED), 'protected': before['protected_count'],
                      'staged_preserved': before['staged_count'], 'packet_pages': 42}))


if __name__ == '__main__':
    if '--historical' in sys.argv:
        main()
    else:
        from build_current_suite_k3 import main as current_main
        current_main()
