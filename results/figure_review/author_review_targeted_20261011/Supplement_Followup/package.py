from pathlib import Path
import sys,re,json,datetime,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import common as c
P=Path(__file__).resolve().parent;c.PKG=P
ORDER=['FigS03','FigS06','FigS07','FigS10','FigS11']
original=c.git('show',c.BASE+':results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode('utf-8')
heads=list(re.finditer(r'(?m)^## (.+)\r?\n\r?\n',original));captions={}
for i,m in enumerate(heads):
    n=re.search(r'Supplementary Figure S(\d+)\.',m[1])
    if n:captions[f'FigS{int(n[1]):02}']=(m[1],original[m.end():heads[i+1].start() if i+1<len(heads) else len(original)].strip())
title,body=captions['FigS03']
body=body.replace('Lower-triangle display of directed task-to-task road-travel times','Directed task-to-task road-travel times')
body=re.sub(r'The opposite direction is not assumed equal:.*?model input\.',
    'Both travel directions are shown; the matrix is directed and the opposite direction is not assumed equal.',body)
body=body.replace('; a lower-triangle display would omit genuinely directed input.', '.')
body+=' Point transparency distinguishes overlapping origins and substations. The matrix uses the same station ordering on both axes; station identifiers are omitted from its display.'
captions['FigS03']=(title,body)
title,body=captions['FigS06']
body=body.replace('(B) Removal of both the station functionality threshold and source-connectivity requirement relative to the production service model.',
 '(B) Combined removal of the station functionality threshold and source-connectivity requirement relative to the production service model. This joint contrast does not isolate the effect of either requirement. Independent removal-only controls were not evaluated.')
captions['FigS06']=(title,body)
captions['FigS07']=(captions['FigS07'][0],
 'Results under 2pc50, reference crew availability and repair-duration multiplier 1.00. '
 '(A/B) Dynamic means over 1,000 recovery realizations, shown over 0-120 h. Each row separates the four focal policies '
 '(Impact-first, Hospital-first, Degree-first and Vulnerability-first) from the other selected policies (Betweenness-first and Random). '
 'The same Unconstrained reference appears in both views. '
 '(A) Solid lines show the full network; dashed lines show the fixed precomputed most-reliable path. '
 'The quantity is the population-dependency-weighted joint probability that a station is functional and connected to an active Core source, '
 'not a product of marginal probabilities. (B) The full-network joint probability minus the fixed-path joint probability shows the contribution of alternate routes. '
 'The fixed path is selected from 2pc50 fragility before recovery and is not reoptimized at each time. '
 '(C) Static probability of reaching at least one active Core source, conditional on the target station being functional. '
 'This excludes the target station\'s own failure probability; it does not assume that all other stations or sources are functional. '
 '(D) Additional conditional connection probability beyond the fixed most-reliable path. '
 'The static estimates combine the analytical fixed-path probability with a same-state Monte Carlo estimate of connection outside that path, '
 'using 100,000 independently sampled station states; they differ from the dynamic joint quantity in A/B. '
 'Zero estimated additional-route gain does not establish absence of a true gain. Core sources are triangles with their own operational probabilities; '
 'edges have no independent failure probability in this station-failure model. Both static station color scales remain linear from zero to the largest displayed value. '
 'These connectivity probabilities do not measure delivered MW, generation adequacy or electrical capacity.')
title,body=captions['FigS10'];body=body.replace('Tract population provides continuous geographic context on a logarithmic scale;',
 'The neutral-gray tract population shading provides continuous geographic context on the same logarithmic scale;')
captions['FigS10']=(title,body)
title,body=captions['FigS11'];body=body.replace('Printed values and a shared zero-centered scale show actual hour differences without metric-specific rescaling.',
 'Printed values give the actual hour differences. A common zero-centered signed-log color scale is used across all four scenarios and metrics: it is linear within +/-0.10 h and logarithmic beyond that interval. The original hour limits are retained, with no clipping or scenario-specific or metric-specific rescaling. Color spacing is nonlinear; the printed values and colorbar ticks remain in hours.')
captions['FigS11']=(title,body)
with open(c.lp(P/'PROPOSED_CAPTIONS.md'),'w',encoding='utf-8') as f:
    f.write('# Proposed supplement captions\n\n')
    for name in ORDER:f.write('## '+captions[name][0]+'\n\n'+captions[name][1]+'\n\n')

def caption_page(book,title,body):
    p=book.new_page(width=210*c.MM,height=297*c.MM)
    for name,path in [('SupplementReviewArial','C:/Windows/Fonts/arial.ttf'),('SupplementReviewBold','C:/Windows/Fonts/arialbd.ttf')]:p.insert_font(fontname=name,fontfile=path)
    assert p.insert_textbox(c.fitz.Rect(16*c.MM,17*c.MM,194*c.MM,38*c.MM),title,fontname='SupplementReviewBold',fontsize=12,lineheight=1.15)>=0
    assert p.insert_textbox(c.fitz.Rect(16*c.MM,43*c.MM,194*c.MM,281*c.MM),body,fontname='SupplementReviewArial',fontsize=10,lineheight=1.22)>=0

book=c.fitz.open(c.lp(P.parent/'AUTHOR_REVIEW_FIGURES_AND_CAPTIONS.pdf'))
for name in ORDER:
    with c.fitz.open(c.lp(P/(name+'_Candidate.pdf'))) as d:book.insert_pdf(d)
    caption_page(book,*captions[name])
book.save(c.lp(P/'COMBINED_TARGETED_AUTHOR_REVIEW.pdf'),garbage=4,deflate=True)
for i,p in enumerate(book):
    if i<12:continue
    pix=p.get_pixmap(matrix=c.fitz.Matrix(160/72,160/72),alpha=False);pix.save(c.lp(P/'qa'/f'Review_{i+1:02}.png'))
book.close()
contact=c.fitz.open()
for name in ORDER:
    with c.fitz.open(c.lp(P/'before'/(name+'.pdf'))) as old,c.fitz.open(c.lp(P/(name+'_Candidate.pdf'))) as new:
        H=max(old[0].rect.height,new[0].rect.height)/c.MM+24;p=contact.new_page(width=410*c.MM,height=H*c.MM)
        c.text(p,102.5,9,name+': current',9.5,True,True,font_prefix='FollowupSheet')
        c.text(p,307.5,9,name+': proposed',9.5,True,True,font_prefix='FollowupSheet')
        for x,d in [(10,old),(215,new)]:
            p.show_pdf_page(c.fitz.Rect(x*c.MM,16*c.MM,(x+185)*c.MM,16*c.MM+d[0].rect.height),d,0)
        c.text(p,10,H-3,'Each complete figure is 185 mm wide. Print at 100%.',8,font_prefix='FollowupSheet')
contact.save(c.lp(P/'NATIVE_SUPPLEMENT_BEFORE_AFTER.pdf'),garbage=4,deflate=True)
for i,p in enumerate(contact):p.get_pixmap(matrix=c.fitz.Matrix(160/72,160/72),alpha=False).save(c.lp(P/'qa'/f'Contact_{i+1:02}.png'))
contact.close()
print('Built combined 22-page targeted review and five native comparison pages.')
