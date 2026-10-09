"""Synchronize review figures, captions and publication mirrors."""
import hashlib,json,re,shutil,subprocess
import fitz
from pathlib import Path
from la_grid.plotting import selected_strategy_artwork as a
from la_grid.plotting.apply_outcome_display_feedback import update_csv,sha,fonts
from la_grid.plotting.apply_map_metric_identity_feedback import packets
R=a.ROOT;REVIEW=a.REVIEW

def captions():
    p=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';s=p.read_text(encoding='utf-8-sig')
    s=s.replace("Figures 1, 4 and 5 display corrections reflect the author's feedback on 2026-10-07","The current displays use the six-policy manuscript selection requested by the author on 2026-10-08")
    selection='The manuscript scheduled-policy set comprises Degree-first and Betweenness-first as infrastructure priorities; Impact-first, Hospital-first and Vulnerability-first as community-oriented priorities; and Random as a fixed random-order baseline. Unconstrained is an idealized reference. The original experiment contains additional policies, whose results remain available separately.'
    start=s.index('## Figure 1.');pos=s.index('\n\n',start)+2
    if selection not in s:s=s[:pos]+selection+' '+s[pos:]
    def replace(number,body):
        nonlocal s
        heading=('## Supplementary Figure S' if isinstance(number,str) else '## Figure ')+str(number)+'.';start=s.index(heading);end=s.find('\n## ',start+4);end=len(s) if end<0 else end;s=s[:start]+body.rstrip()+'\n\n'+s[end:].lstrip()
    replace(4,'''## Figure 4. Selected restoration-policy performance

Results under 2pc50, reference crew availability and repair-duration multiplier 1.00, using 1,000 realizations for each of the six scheduled policies and Unconstrained. The shared key groups infrastructure priorities (Degree-first, Betweenness-first), community-oriented priorities (Impact-first, Hospital-first, Vulnerability-first), and baselines (Random, Unconstrained). Random uses one fixed random station sequence. (A) Population-weighted modeled service availability over 0-100 h. The left view shows the four focal policies and the right shows Betweenness-first and Random; Unconstrained appears in both views as the same reference. All selected policies remain visible, with common scales. (B, left) Within-policy side-by-side mean service-loss bars for all tracts, Q4 tracts and hospital-linked tracts, with a common zero-based hour axis and no uncertainty whiskers. All-tract loss is population-weighted; Q4 loss uses population weights within the highest social-vulnerability quartile; hospital-tract loss is an equal-weight mean within hospital-linked tracts. All loss values integrate one minus modeled service availability over 0-480 h. (B, right) Mean population T80 with 5th-95th realization ranges, not confidence intervals. T80 is the first time population-weighted modeled service reaches 80%, a threshold time rather than a loss integral. Hospital-linked tract results do not measure electricity delivered to hospitals or clinical capacity. Direct-community uses the Impact-first sequence and is represented once.''')
    start=s.index('## Figure 5.');end=s.index('## Figure 6.',start);block=s[start:end].replace('The first key row contains the four emphasized scheduled policies and the Unconstrained reference. The second contains the four other scheduled policies. ','').replace('for the four emphasized scheduled policies in the first key row','for the four emphasized scheduled policies').replace('all nine','the seven displayed').replace('all eight scheduled policies','the six scheduled manuscript policies');pos=block.index('\n\n')+2
    clarification='The top grouped key serves Panel A (six scheduled policies plus Unconstrained); Panel B uses only Impact-first, Hospital-first, Degree-first and Vulnerability-first. The reference key between B and C/D serves C/D only. '
    if clarification not in block:block=block[:pos]+clarification+block[pos:]
    s=s[:start]+block+s[end:]
    replace('3','''## Supplementary Figure S3. Crew origins and directed travel inputs

(A) Crew-origin locations and substation tasks, with a downtown inset. (B) The complete directed task-to-task travel-time matrix, with origin stations in rows and destinations in columns. Each cell is the saved travel time in hours for that ordered origin-destination pair. The reverse direction is displayed separately and is not assumed identical; a lower-triangle display would omit genuinely directed input. These inputs define dispatch travel in the scheduling model, not an observed resource-response result or a forecast of congestion after an earthquake.''')
    replace('4','''## Supplementary Figure S4. Static network criticality and dynamic functional-network recovery

(A) Static targeted and random station-removal curves for the intact undirected station graph. Network lambda2-impact ranks the loss of algebraic connectivity caused by removing a station; it is different from the population-impact ranking used by the restoration policy Impact-first. These removal curves describe structural criticality/percolation, not repair optimality. The static Closeness attack is retained as a structural diagnostic and is not an additional scheduled manuscript policy. (B/C) Dynamic structure read from the same 1,000 saved 2pc50 recovery trajectories per policy, using the reference crew and duration conditions. A station enters the functional graph when its raw functionality is at least 0.50; edges are the original connections between functional stations. In B, each realization's largest connected component node count is divided by the full study graph's 92 stations, then averaged. In C, its mean internal degree is twice the number of edges in that component divided by its number of nodes, then averaged; an empty component has zero and a singleton has degree zero. These are mean curves, without confidence intervals, displayed over 0-120 h. The left views emphasize Impact-first, Hospital-first, Degree-first and Vulnerability-first; the right retain Betweenness-first and Random. Unconstrained is repeated as a common reference. Differences demonstrate how repair priorities alter functional network structure; they do not establish globally optimal repair orders, community-loss minimization, or delivered electrical power. Supplementary Figure S7 instead requires connection to an active Core source and separates full-network from precomputed fixed-path connectivity; a large functional component need not itself be source-connected. Figure S4 shows how targeted removals fragment the network and how the largest functional component and its internal degree recover under the evaluated priorities.''')
    start=s.index('## Supplementary Figure S7.');end=s.index('## Supplementary Figure S8.',start);block=s[start:end].replace('all eight scheduled policies','the six scheduled manuscript policies plus Unconstrained').replace('all four other scheduled policies remain visible','Betweenness-first and Random remain visible');s=s[:start]+block+s[end:]
    replace('11','''## Supplementary Figure S11. Policy-outcome contrasts across earthquake scenarios

Panels A-D show Long Beach, San Fernando, Northridge and 2pc50 under the reference crew and repair-duration conditions. Each cell is the mean realization-level difference between the named scheduled policy and Unconstrained, using the same 1,000 physical realizations within that scenario. Rows include the six selected manuscript policies. Columns show all-tract population-weighted service loss, Q4 population-weighted service loss, hospital-linked equal-tract mean service loss and population T80. Loss integrates one minus modeled service availability over 0-480 h; T80 is the first crossing of 80% population-weighted modeled service, a distinct time outcome. The divider separates T80 from the loss integrals. Printed values and a shared zero-centered scale show actual hour differences without metric-specific rescaling. The source table also records 5th-95th realization-difference ranges; uncertainty is not drawn in this mean heatmap. Hospital-linked loss is not electricity delivered to hospitals or clinical capacity. Historical scenarios and 2pc50 use different fragility parameterizations, so cross-scenario contrasts are not pure ground-motion-intensity sensitivity. Direct-community is represented by Impact-first once.''')
    for number in [12,13]:
        start=s.index(f'## Supplementary Figure S{number}.');end=s.find('\n## ',start+4);end=len(s) if end<0 else end;block=s[start:end].replace('all eight scheduled policies','all six selected scheduled policies').replace('include the four other scheduled policies not used as its references','include Betweenness-first and Random alongside the four focal policies');s=s[:start]+block+s[end:]
    assert 'burden' not in s.lower() and 'matched' not in s.lower()
    p.write_text(s,encoding='utf-8');return s

def append_evidence():
    path=REVIEW/'ALL_FIGURES_WITH_CAPTIONS.pdf';book=fitz.open(path)
    for name,title in [('Degree_and_Betweenness','Degree and betweenness: supplementary evidence candidate'),('Network_Station_Community_Tradeoffs','Network, station and community restoration trade-offs')]:
        with fitz.open(REVIEW/'Additional_Evidence'/(name+'.pdf')) as doc:book.insert_pdf(doc)
        body=(REVIEW/'Additional_Evidence'/(name+'.md')).read_text(encoding='utf-8')
        page=book.new_page(width=185*a.MM,height=280*a.MM);fonts(page)
        assert page.insert_textbox(fitz.Rect(14*a.MM,16*a.MM,171*a.MM,33*a.MM),title,fontname='DisplayArialBold',fontsize=9.5)>=0
        assert page.insert_textbox(fitz.Rect(14*a.MM,38*a.MM,171*a.MM,263*a.MM),body,fontname='DisplayArial',fontsize=9.2,lineheight=1.22)>=0
    assert len(book)==42
    tmp=path.with_suffix('.integrated.pdf');book.save(tmp,garbage=4,deflate=True);book.close();tmp.replace(path)

def integrate():
    records=json.loads((a.TEMP/'artwork_records.json').read_text());records={r['file']:r for r in records};captions_text=captions()
    def manifest(row):
        if row['final_name'].replace('.png','.pdf') not in records:return
        record=records[row['final_name'].replace('.png','.pdf')];path=REVIEW/row['final_name']
        row.update(source_file=path.relative_to(R).as_posix(),current_source_file=path.relative_to(R).as_posix(),source_commit='SELECTED_STRATEGY_ARTIFACT_COMMIT_PENDING',sha256=sha(path),size_mm=' x '.join(f'{v:.3f}' for v in record['size_mm']),min_font_pt=f"{record['min_font_pt']:.3f}",status='AUTHOR_REQUESTED_REVIEW_UPDATE',parent_source_commit=a.BASE)
        try:row['parent_sha256']=a.common.baseline_digest(path.relative_to(R).as_posix())
        except subprocess.CalledProcessError:pass
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    generator_by={'Fig07':'selected_strategy_artwork.py','FigS03':'selected_strategy_source_travel.py','FigS07':'selected_strategy_source_travel.py','FigS05':'extended_ga_artwork_20261008.py'}
    def index(row):
        source=row.get('source_path','');key=source.replace('results/figure_review/','').replace('.png','.pdf')
        if key not in records:return
        src=R/source;dst=R/'results/figures'/row['file'];shutil.copyfile(src,dst);assert sha(src)==sha(dst)
        row.update(sha256_or_lfs_oid='sha256:'+sha(dst),current_status='byte-identical current author-review artwork',generator='src/la_grid/plotting/'+generator_by.get(Path(key).stem,'selected_strategy_panels.py'),notes='Six-policy manuscript display; original full experiment retained. Supplement S11 includes all four earthquake scenarios.')
    update_csv(R/'results/figures/FIGURE_INDEX.csv',index);packets(captions_text)
    append_evidence()
    path=R/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';authority=json.loads(path.read_text())
    paths=['src/la_grid/plotting/Project_Visualizer.py']+[p.relative_to(R).as_posix() for p in (R/'src/la_grid/plotting').glob('selected_strategy*.py')]+['src/la_grid/plotting/integrate_selected_strategy_20261008.py','src/la_grid/plotting/extended_ga_artwork_20261008.py']
    for filename in paths:
        if not (R/filename).exists():continue
        entry={'path':filename,'sha256':hashlib.sha256((R/filename).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'tracked_in_current_git':True};authority['current_code_files']=[r for r in authority['current_code_files'] if r['path']!=filename]+[entry]
    path.write_text(json.dumps(authority,indent=2)+'\n')
    (R/'docs/reproducibility/SELECTED_STRATEGY_ARTWORK_20261008.json').write_text(json.dumps({'base_commit':a.BASE,'selected_scheduled_policies':a.SELECTED,'idealized_reference':'unconstrained','records':list(records.values()),'formal_results_replaced':False},indent=2)+'\n')
    p=REVIEW/'README.md';s=p.read_text(encoding='utf-8');paragraph='Current manuscript comparisons use six scheduled policies: Degree-first, Betweenness-first, Impact-first, Hospital-first, Vulnerability-first and Random, plus the idealized Unconstrained reference.'
    if paragraph not in s:s+='\n'+paragraph+' The original full strategy experiment remains in its source authorities. Fig7B feature labels are explicitly right-aligned. Additional Evidence includes [Degree/betweenness maps and distributions](Additional_Evidence/Degree_and_Betweenness.pdf) and [network/station/community trade-offs](Additional_Evidence/Network_Station_Community_Tradeoffs.pdf).\n'
    p.write_text(s,encoding='utf-8');print('Integrated',len(records),'current figures and candidates')
if __name__=='__main__':integrate()
