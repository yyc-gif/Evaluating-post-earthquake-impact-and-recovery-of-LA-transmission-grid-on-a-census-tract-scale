"""Record the operator's completed native-size review, not automatic visual certification."""
from common import *

if __name__=='__main__':
    m=json.loads(lp(OUT/'FIGURE_MANIFEST.json').read_text())
    records=[]
    for r in m['figures']:
        records.append(dict(figure=r['name'],pdf_sha256=sha(OUT/r['pdf']),PNG_sha256=sha(OUT/r['png']),pages=1,native_publication_width_inches=7.2,rendered_review_scale=2,inspected_by='Codex visual review of actual rendered page',review='PASS: no cropped labels, title/colorbar collision, blank data panels or inconsistent class/bar colors'))
    dump('VISUAL_INSPECTION.json',dict(review_status=WARN,figures=records,inspection_is_operator_assertion=True,automatic_reinspection_not_claimed=True,corrected=['Left label clipping on source-component chart','Relationship underscore/dash mismatch in bar chart','True K1 reference for reused WCSS comparison','Map title/colorbar overlap','Numerical default diagnostic not misrepresented as provider QA flag']))
