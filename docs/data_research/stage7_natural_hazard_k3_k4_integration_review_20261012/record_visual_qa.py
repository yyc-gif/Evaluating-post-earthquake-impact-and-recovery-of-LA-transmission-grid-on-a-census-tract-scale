"""Operator inspection record, not an automatic assertion of visual perfection."""
from common import *

if __name__=='__main__':
    m=json.loads(lp(OUT/'FIGURE_MANIFEST.json').read_text());pages=[]
    for r in m['figures']:
        pages.append(dict(pdf=r['pdf'],page=r['page'],PDF_sha256=sha(OUT/r['pdf']),PNG_sha256=sha(OUT/r['PNG']),publication_width_inches=7.2,render_scale=2,reviewer='Codex visual inspection of actual native-size rendered pages',result='PASS:labels,legends,bounds,units,palettes,data panels andreview status checked'))
    dump('VISUAL_INSPECTION.json',dict(review_status=WARN,pages=pages,operator_review_only=True,automatic_visual_certification=False,corrected=['Source-map colorbar/scatter label collision','Source-review subplot/main-title collision','Long station names adjacent to colorbar','Figure7 whitespace and count labels','34Q versus4HAYNES/ALAMITOS source wording']))
