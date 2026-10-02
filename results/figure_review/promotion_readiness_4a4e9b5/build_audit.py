"""Read-only source audit; native PDF embedding, no scientific execution."""
from pathlib import Path
import fitz, pandas as pd, json, hashlib, subprocess
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
MM=72/25.4
PUB=ROOT/'results/figures'
LAY=ROOT/'results/figure_review/candidate_v2.1_layout'
NEW=ROOT/'results/figure_review/fig06_resource_redesign_20261002'
BASELINE='4a4e9b5fc026cfb86cfcbc25a11268db0fe1bb4d'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def captions_md(p):
    result={}
    for b in p.read_text(encoding='utf-8').split('## ')[1:]:
        k,v=b.split('\n\n',1);result[k.strip()]=v.strip()
    return result

def inventory():
    layout=pd.read_csv(LAY/'FIGURE_V2_1_LAYOUT_INDEX.csv').set_index('figure_stem')
    newcaps=captions_md(NEW/'CAPTIONS.md')
    pub=pd.read_csv(PUB/'FIGURE_INDEX.csv');pub=pub[pub.format.eq('pdf')]
    pub=pub.set_index('figure_number')
    rows=[]
    def add(i,p,role,caption='',source='',kind='preferred'):
        rows.append(dict(figure=i,path=str(p.relative_to(ROOT)).replace('\\','/'),role=role,caption=caption,source=source,kind=kind))
    for i,stem in [('Fig01','Fig01_Revised_Analytical_Framework'),('Fig02','Fig02_System_Network_Mapping_and_Public_Site_Check'),('Fig03','Fig03_Hazard_Service_Loss_and_Unconstrained_Baseline')]:
        add(i,LAY/(stem+'.pdf'),'Main candidate',str(layout.loc[stem,'caption']),str(layout.loc[stem,'source_authority']))
    for i,stem in [('Fig04','Fig04_Readable_All_Policy_Comparison'),('Fig05','Fig05_Separated_Quartile_Intervals'),('Fig06','Fig06_Preferred_Resource_Policy_Contrasts'),('Fig07','Fig07_Native_Panel_Reflow')]:
        add(i,NEW/(stem+'.pdf'),'Main candidate',newcaps[stem], 'See latest review captions and accepted source indices.')
    choices=[('FigS01',PUB/'FigS01_Damage_Severity.pdf'),('FigS02',PUB/'FigS02_Initial_Service.pdf'),('FigS03',NEW/'FigS03_Clear_Input_Labels.pdf'),('FigS04',PUB/'FigS04_Network_Criticality_and_Percolation.pdf'),('FigS05',LAY/'FigS05_GA_Reproducibility.pdf'),('FigS06',PUB/'FigS06_Mapping_Robustness.pdf'),('FigS07',PUB/'FigS07_Source_Redundancy.pdf'),('FigS08',NEW/'FigS08_Clear_Planning_Labels.pdf'),('FigS09',NEW/'FigS09_Cluster_Visibility.pdf')]
    for i,p in choices:
        cap=newcaps.get(p.stem)
        if cap is None and p.stem in layout.index:cap=str(layout.loc[p.stem,'caption'])
        if cap is None:cap=str(pub.loc[i,'notes'])
        add(i,p,'Supplement candidate',cap,str(pub.loc[i,'source_authority']) if i in pub.index else str(layout.loc[p.stem,'source_authority']))
    add('FigS10',PUB/'Fig05_Hospital_Priority_and_Critical_Service.pdf','Supplement policy-definition candidate',str(pub.loc['Fig05','notes']),str(pub.loc['Fig05','source_authority']))
    stem='Candidate_Supplement_Cross_Hazard_Policy_Robustness'
    add('FigS11',LAY/(stem+'.pdf'),'Supplement cross-hazard candidate',str(layout.loc[stem,'caption']),str(layout.loc[stem,'source_authority']))
    for i,stem,ls in [('FigS12','Full_Crew_Absolute_Outcomes','Candidate_Supplement_Crew_Resource_Contrasts'),('FigS13','Full_Duration_Absolute_Outcomes','Candidate_Supplement_Repair_Duration_Contrasts')]:
        add(i,NEW/(stem+'.pdf'),'Supplement complete OFAT candidate',str(layout.loc[ls,'caption']),str(layout.loc[ls,'source_authority']))
    add('FigS14',ROOT/'results/revised_suite/LA_Grid_Revised_Suite_20260925/Sensitivity Output_clean/vis_gate_robustness_2pc50_hospital_first.pdf','Supplement gate/threshold candidate','','Existing accepted gate sensitivity summaries.')
    add('FigS15',ROOT/'results/revised_suite/LA_Grid_Revised_Suite_20260925/Stage 3 Output_expanded/vis_source_reliability_full_vs_best_path_2pc50.pdf','Optional Supplement source-path diagnostic','','Existing accepted station operational-reliability table.')
    add('FigS16',NEW/'Fig06_Separation_Detail_Review.pdf','Review / optional Supplement aid',newcaps['Fig06_Separation_Detail_Review'],'Same four saved panel-C points; no substitute main scales.')
    seen={x['path'] for x in rows}
    for i,x in pub.iterrows():
        p=PUB/str(x['file'])
        if not p.exists():p=ROOT/str(x['source_path'])
        rel=str(p.relative_to(ROOT)).replace('\\','/')
        if rel not in seen:
            add('Old-'+i,p,'Old publication alternative',str(x['notes']),str(x['source_authority']),'alternate');seen.add(rel)
    for i,stem in [('Old-two-level-Fig06','Fig06_Two_Level_Crew_Resource_Contrast'),('Old-layout-Fig04','Fig04_All_Policy_Recovery_and_Outcomes'),('Old-layout-Fig05','Fig05_Distributional_Outcomes_and_Reference_Sensitivity'),('Old-layout-Fig07','Fig07_Community_Typology_and_Hotspots')]:
        add(i,LAY/(stem+'.pdf'),'Earlier review alternative',str(layout.loc[stem,'caption']),str(layout.loc[stem,'source_authority']),'alternate')
    return rows

def prepare():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASELINE
    rows=inventory()
    (OUT/'native_views').mkdir(exist_ok=True);(OUT/'page_views').mkdir(exist_ok=True)
    for row in rows:
        p=ROOT/row['path']; assert p.read_bytes().startswith(b'%PDF'),p
        with fitz.open(p) as d:
            page=d[0];spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
            row.update(sha256=sha(p),width_mm=page.rect.width/MM,height_mm=page.rect.height/MM,min_font=min(s['size'] for s in spans),fonts=';'.join(sorted({s['font'] for s in spans})),pages=len(d),off_page_text=[s['text'] for s in spans if not page.rect.contains(fitz.Rect(s['bbox']))])
            row['lfs_matches_baseline']=False
            try:
                blob=subprocess.check_output(['git','show',BASELINE+':'+row['path']],cwd=ROOT,stderr=subprocess.DEVNULL)
                if blob.startswith(b'version https://git-lfs'):
                    oid=next(x.decode().split(':',1)[1] for x in blob.splitlines() if x.startswith(b'oid sha256:'))
                    assert oid==row['sha256'],p
                    row['lfs_matches_baseline']=True
            except subprocess.CalledProcessError:row['not_in_baseline']=True
            page.get_pixmap(matrix=fitz.Matrix(1.9,1.9),alpha=False).save(str(OUT/'native_views'/(row['figure']+'.png')))
            # No shrink: review sheet uses an extended page if native height exceeds A4 body.
            sheet=fitz.open();q=sheet.new_page(width=210*MM,height=max(297*MM,(row['height_mm']+35)*MM))
            q.insert_font(fontname='Arial',fontfile='C:/Windows/Fonts/arial.ttf')
            q.insert_text((12.5*MM,10*MM),row['figure']+' | Native 185-mm review; not promotion',fontsize=8,fontname='Arial')
            width=185*MM; height=page.rect.height*(width/page.rect.width)
            q.show_pdf_page(fitz.Rect(12.5*MM,18*MM,197.5*MM,18*MM+height),d,0)
            q.get_pixmap(matrix=fitz.Matrix(1.45,1.45),alpha=False).save(str(OUT/'page_views'/(row['figure']+'.png')));sheet.close()
    (OUT/'INVENTORY.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    pd.DataFrame(rows).to_csv(OUT/'ACTUAL_FILE_MEASUREMENTS.csv',index=False)
    before=json.loads((NEW/'BEFORE_STATE.json').read_text());before['source_artwork_hashes']={x['path']:x['sha256'] for x in rows};before['index_before_hex']=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).hex()
    (OUT/'READ_ONLY_GUARD.json').write_text(json.dumps(before,indent=2))
    print('Prepared',len(rows),'actual native PDFs and corresponding unshrunk page previews.')

if __name__=='__main__':prepare()
