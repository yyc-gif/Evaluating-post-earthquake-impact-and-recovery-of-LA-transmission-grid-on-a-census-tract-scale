"""Compare actual unified PDF renders with inspected native figure previews."""
from pathlib import Path
import hashlib, json
import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / 'results/figure_review'

def lp(p):
    return '\\\\?\\' + str(p.resolve())

if __name__ == '__main__':
    names = [f'Fig{i:02d}' for i in range(1,8)] + [f'FigS{i:02d}' for i in [1,*range(3,14)]]
    changed = ['Fig07','FigS05','FigS09','FigS10','FigS11','FigS13']
    packet = fitz.open(lp(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    assert len(packet)==42
    records = []
    for name in changed:
        p = packet[2*names.index(name)]
        pix = p.get_pixmap(matrix=fitz.Matrix(160/72,160/72),alpha=False)
        with Image.open(lp(SUITE/'Page_Previews'/(name+'.png'))) as im:
            expected = im.convert('RGB').tobytes()
            assert pix.samples==expected, name
        records.append({'figure':name,'native_width_mm':p.rect.width*25.4/72,
            'actual_packet_page':2*names.index(name)+1,'render_dpi':160,
            'inspected_preview_and_actual_packet_pixels_identical':True,
            'render_rgb_sha256':hashlib.sha256(pix.samples).hexdigest()})
        print(name,'actual packet render identical',flush=True)
    report = {'actual_vector_PDF_preview_inspection': changed,'records':records,'scientific_results_changed':False,'notes': 'White N/A boundaries, synchronized C4, unchanged approved S05, true tract-population scale, linear 2pc50 S11 and refreshed S13 labels visually inspected at native 185-mm width.'}
    Path(lp(Path(__file__).parent/'VISUAL_AND_PACKET_QA.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
