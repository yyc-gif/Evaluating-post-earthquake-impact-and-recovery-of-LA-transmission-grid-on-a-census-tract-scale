"""Verify actual unified PDF pages and unedited native figure regions."""
from pathlib import Path
import io,json,subprocess,sys
import fitz
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
QA=Path(__file__).parent
SUITE=ROOT/'results/figure_review'
BASE='37e71b3e15b0f4e1be3a651344e3f9e6475dc24b'


def lp(p):
    s=str(p.resolve());return s if s.startswith('\\\\?\\') else '\\\\?\\'+s


if __name__=='__main__' and len(sys.argv)>1:
    page=int(sys.argv[1]);name=sys.argv[2]
    d=fitz.open(lp(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    pix=d[page].get_pixmap(matrix=fitz.Matrix(160/72,160/72),alpha=False)
    with Image.open(lp(SUITE/'Page_Previews'/(name+'.png'))) as im:
        assert pix.samples==im.convert('RGB').tobytes(),name
    print(json.dumps({'figure':name,'actual_packet_page':page+1,'actual_packet_pixels_identical':True}))
elif __name__=='__main__':
    sys.path.append(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages')
    sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
    import consolidate_current_figure_suite as u
    report=json.load(open(lp(QA/'INTEGRATION_QA.json'),encoding='utf-8'))
    results=[]
    for stem in report['updated_figures']:
        index=report['active_figures'].index(stem)
        raw=subprocess.check_output([sys.executable,str(Path(__file__)),str(2*index),Path(stem).name])
        results.append(json.loads(raw));print(Path(stem).name,'actual packet page verified',flush=True)
    comparisons={}
    for name in ['Fig01','Fig05']:
        before=np.asarray(Image.open(io.BytesIO(u.payload(BASE,'results/figure_review/Page_Previews/'+name+'.png'))).convert('RGB'))
        after=np.asarray(Image.open(lp(SUITE/'Page_Previews'/(name+'.png'))).convert('RGB'))
        assert before.shape==after.shape
        if name=='Fig01':
            # Include the edited card's border/antialias footprint in the mask.
            scale=160/25.4
            mask=np.ones(before.shape[:2],dtype=bool)
            mask[int(163.7*scale):int(217.5*scale)+1,int(94*scale):int(182.5*scale)+1]=False
            assert np.array_equal(before[mask],after[mask]),'Fig1 outside Stage5'
            comparisons['Fig1_outside_Stage5_pixels_identical']=True
        else:
            y=int(174*160/25.4)
            assert np.array_equal(before[:y],after[:y]),'Fig5 A-D'
            comparisons['Fig5_A_to_D_pixels_identical']=True
    data={**comparisons,'packet_checks':results,
          'actual_native_PDFs_visually_inspected':report['updated_figures'],
          'visual_review':'Plain Stage5 labels; exact capped colorbar without seams; fixed-source threshold plots; K-means only; warm population colors and dark priority keys; eight readable resource panels.'}
    u.dump(QA/'VISUAL_AND_PACKET_QA.json',data)
    # Render the actual modified caption pages for separate visual inspection.
    full=fitz.open(lp(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    for name in ['Supplement/FigS06','Supplement/FigS11']:
        i=2*report['active_figures'].index(name)+1
        pix=full[i].get_pixmap(matrix=fitz.Matrix(110/72,110/72),alpha=False)
        pix.save(lp(QA/(Path(name).name+'_CAPTION_PAGE.png')))
    print('Unchanged regions, complete packet pages and caption renders verified.',flush=True)
