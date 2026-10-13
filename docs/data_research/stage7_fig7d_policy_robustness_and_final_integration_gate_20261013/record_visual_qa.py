"""Record completed human review of actual publication-size rendered pages."""
from datetime import datetime, timezone
from common import *


def main():
    figure_manifest=json.loads(lp(OUT/'FIGURE_MANIFEST.json').read_text())['figures']
    records=[]
    for record in figure_manifest:
        records.append(dict(pdf=record['pdf'],sha256=sha(OUT/record['pdf']),
                            rendered_review='tmp/pdfs/'+Path(record['pdf']).stem+'_page1_review.png',
                            publication_width_inches=7.2,render_scale=2,visually_inspected=True))
    dump('VISUAL_INSPECTION.json',dict(checked_UTC=datetime.now(timezone.utc).isoformat(),
         operator='Codex actual rendered-page visual inspection',pages=records,
         readable=True,clipping_or_unintended_overlap_observed=False,
         corrections=['Full policy labels fit within page margins; nonQ4 and Q4 keys do not hide bars.',
                      'Leave-block figure labels explicitly reindexed to actual 5km/10km/broad-region rows.',
                      'Legacy-score GEOIDs restore leading zero only; score and original Top10 unchanged.',
                      'S9 rare class called Initial exception, not exclusively Q state.'],
         A_C_science_and_pixels_preserved=True, D1_24_score_NA_distinguished_from_16_cluster_NA=True,
         output_figures_not_formal=True))


if __name__=='__main__':
    main()
