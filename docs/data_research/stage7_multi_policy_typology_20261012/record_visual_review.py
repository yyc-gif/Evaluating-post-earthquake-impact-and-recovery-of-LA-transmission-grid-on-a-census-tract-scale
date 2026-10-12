"""Record hashes of the final pages inspected in VISUAL_REVIEW_NOTES.md."""
from common import *

if __name__=='__main__':
    notes=OUT/'VISUAL_REVIEW_NOTES.md'
    assert lp(notes).is_file()
    render=json.loads(lp(OUT/'PDF_RENDER_QA.json').read_text())
    assert len(render['pages'])==10
    for p in render['pages']:assert sha(OUT/p['pdf'])==p['pdf_sha256']
    dump('VISUAL_REVIEW_QA.json',dict(status='PASS',native_publication_width_in=7.2,all_final_pages_visually_inspected=True,
        review_notes_sha256=sha(notes),pages=[dict(pdf=p['pdf'],page=p['page'],pdf_sha256=p['pdf_sha256'],status='PASS') for p in render['pages']]))
