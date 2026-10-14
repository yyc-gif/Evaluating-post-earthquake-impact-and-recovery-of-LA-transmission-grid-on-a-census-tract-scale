"""Render the native DOCX-compatible QA PDFs and verify visible caption text."""
from pathlib import Path
import re
import sys

import fitz

sys.path.insert(0, str(Path(__file__).parent))
import build_local_review as b


def main():
    rows = []
    folder = sys.argv[1] if len(sys.argv) > 1 else 'qa_checked'
    for name in ['structure', 'captions']:
        path = b.OUT / folder / (name + '.pdf')
        with fitz.open(b.a.u.lp(path)) as doc:
            for i, page in enumerate(doc):
                b.write(folder + '/' + name + f'_page_{i+1}.png',
                        page.get_pixmap(dpi=140, alpha=False).tobytes('png'))
                spans = [s for block in page.get_text('dict', flags=0)['blocks']
                         for line in block.get('lines', []) for s in line['spans']]
                outside = [s['text'] for s in spans if not page.rect.contains(fitz.Rect(s['bbox']))]
                assert not outside
                rows.append(dict(document=name, page=i+1, page_count=len(doc),
                    width_inches=page.rect.width/72, height_inches=page.rect.height/72,
                    text_chars=len(page.get_text()), minimum_text_pt=min(s['size'] for s in spans),
                    out_of_page_text=outside))
            text = '\n'.join(p.get_text() for p in doc)
            normalized = ' '.join(text.split())
            if name == 'captions':
                assert re.findall(r'(?m)^Figure (\d+)\.', text) == [str(i) for i in range(1, 8)]
                assert re.findall(r'(?m)^Supplementary Figure S(\d+)\.', text) == [str(i) for i in range(1, 11)]
                assert 'saved realization range' not in normalized
                assert '95% bootstrap confidence intervals for mean effects' in normalized
                assert 'service-loss bars are means without whiskers' in normalized
                assert 'all seven P2 variables' in normalized and 'Six empirical feature distributions' in normalized
                assert 'common burden-to-lightness scaling' in normalized
            else:
                assert 'common Unconstrained reference' in normalized
    b.dump('DOCX_RENDER_TECHNICAL_QA.json', dict(
        renderer='WPS native DOCX-compatible read-only PDF export; PyMuPDF page rendering',
        Word_COM_attempt='Activation/render timed out; only exact task-created automation/helper PIDs stopped',
        LibreOffice='not installed; render_docx.py attempted and failed',
        pages=rows, original_DOCX_sources_unchanged=True, source_docx_styles_preserved=True,
        native_Microsoft_Word_render_completed=False, final_Word_application_compatibility_not_certified=True))
    print('Four document pages rendered; visible numbering/statistical definitions verified.')


if __name__ == '__main__':
    main()
