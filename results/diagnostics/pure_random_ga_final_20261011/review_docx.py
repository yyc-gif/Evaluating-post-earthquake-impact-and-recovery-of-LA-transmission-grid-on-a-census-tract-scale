"""Narrow OOXML review patch from a verified parent; no model or statistics calls."""
from __future__ import annotations
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import zipfile

from lxml import etree as E
from docx import Document

ROOT = Path(__file__).resolve().parents[3]
def lp(path):
    return Path('\\\\?\\' + str(path.resolve())) if not str(path).startswith('\\\\?\\') else path
OUT = lp(Path(__file__).resolve().parent)
REVIEW = lp(ROOT / 'Review_and_Revision/Pure_Random_GA_20261011')
SOURCE = lp(ROOT.parent / '_ms7/docs/data_research/built_environment_20261009/manuscript_reconciliation_20261010/Manuscript_Stage7_Integration_REVIEW.docx')
SOURCE_SHA = '3f90a76593b24abbb4a175766ba9f2f7f683919781c475f4e7f4320f0e58acc4'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w':W, 'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
def sha(data): return hashlib.sha256(data).hexdigest()
def text(node): return ''.join(node.xpath('.//w:t/text()', namespaces=NS))
def dump(path, value): path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def patch_text(p, value):
    prop = deepcopy(p.find('{'+W+'}pPr'))
    runs=p.findall('{'+W+'}r')
    rprop=deepcopy(runs[0].find('{'+W+'}rPr')) if runs else None
    for child in list(p): p.remove(child)
    if prop is not None:p.append(prop)
    run=E.SubElement(p,'{'+W+'}r')
    if rprop is not None:run.append(rprop)
    t=E.SubElement(run,'{'+W+'}t');t.text=value
    t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')

def main():
    assert sha(SOURCE.read_bytes())==SOURCE_SHA
    qa=json.loads((OUT/'NUMERICAL_AND_COHORT_QA.json').read_text())
    assert qa['status']=='PASS' and qa['policy_records']==6000
    with (OUT/'POLICY_OUTCOMES.csv').open(newline='',encoding='utf-8') as stream:
        levels=list(csv.DictReader(stream))
    with (OUT/'PAIRED_EFFECTS.csv').open(newline='',encoding='utf-8') as stream:
        effects=list(csv.DictReader(stream))
    primary='population_weighted_normalized_burden_hr'
    assert sum(r['metric']==primary for r in levels)==3
    ga, impact='GA-pure-random','Impact-first'
    def mean(policy, metric):return float(next(r['mean'] for r in levels if r['strategy']==policy and r['metric']==metric))
    def effect(metric):return next(r for r in effects if r['reference']==impact and r['metric']==metric)
    def delta(metric):return float(effect(metric)['mean_difference'])
    def ci(metric, simultaneous=False):
        prefix='simultaneous95' if simultaneous else 'ci95'
        r=effect(metric)
        return f"[{float(r[prefix+'_low']):.3f}, {float(r[prefix+'_high']):.3f}]"
    assert int(effect(primary)['improved_count'])==1741 and int(effect(primary)['worsened_count'])==259
    assert f"{delta(primary):.3f}"=='-0.533'
    assert f"{delta('L_source_population_mass_weighted_hr'):.3f}"=='-0.821'
    assert f"{delta('L_self_population_mass_weighted_hr'):.3f}"=='0.277'
    assert f"{delta('L_threshold_population_mass_weighted_hr'):.3f}"=='0.011'
    with zipfile.ZipFile(SOURCE) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
    xml=E.fromstring(parts['word/document.xml']);body=xml.find('w:body',NS)
    pars=body.findall('w:p',NS);tables=body.findall('w:tbl',NS)
    assert len(pars)==143 and len(tables)==5
    old_xml={i:E.tostring(p) for i,p in enumerate(pars)}
    old_tables={i:E.tostring(t) for i,t in enumerate(tables)}
    ledger=[]
    changes={}
    def change(i,new,reason):
        old=text(pars[i]);patch_text(pars[i],new);changes[i]=new
        ledger.append(dict(location=f'original paragraph P{i:03d}',action='REPLACE',reason=reason,before=old,after=new))
    ga_result=f"On a separate prospective cohort of 2,000 new paired 2pc50 realizations under C57_D1/M1/G1, the frozen GA had mean normalized population loss of {mean(ga,primary):.3f} h versus {mean(impact,primary):.3f} h for Impact-first. The paired difference was {delta(primary):.3f} h (two-contrast simultaneous 95% interval {ci(primary,True)} h), or {-delta(primary)/mean(impact,primary)*100:.2f}% of the Impact-first mean. GA had lower loss in 1,741 realizations and higher loss in 259. Reduced source-path loss (-0.821 h) offset increased self-loss (+0.277 h) and threshold loss (+0.011 h). These exact event-integral components describe the mechanism; they do not identify a causal contribution of a particular station movement. Figure 1 shows mean effective-service trajectories for this new cohort."
    hospital=f"Mean normalized burden over the 103 hospital-associated tracts was {mean(ga,'hospital_mean_normalized_burden_hr'):.3f} h for GA and {mean(impact,'hospital_mean_normalized_burden_hr'):.3f} h for Impact-first. The paired difference was {delta('hospital_mean_normalized_burden_hr'):.3f} h (descriptive pointwise 95% interval {ci('hospital_mean_normalized_burden_hr')} h). This unweighted tract mean is not hospital load, patient disruption, facility uptime or energy loss. Mean per-realization system T80 was {mean(ga,'T80_restricted_hr'):.3f} h and {mean(impact,'T80_restricted_hr'):.3f} h, respectively, with all crossings before 480 h. These means are distinct from tract-mean T80 and the 80% crossing of a mean trajectory."
    equity=f"GA reduced population-weighted mean burden in every fixed SOVI tract quartile relative to Impact-first, but did not reduce disparity. Q4 was already less burdened than Q1. Mean per-realization absolute Q4-Q1 separation rose from {mean(impact,'absolute_Q4_minus_Q1_hr'):.3f} to {mean(ga,'absolute_Q4_minus_Q1_hr'):.3f} h; its paired increase was {delta('absolute_Q4_minus_Q1_hr'):.3f} h (pointwise 95% interval {ci('absolute_Q4_minus_Q1_hr')} h). Mean population-weighted tract burden Gini rose from {mean(impact,'burden_gini'):.5f} to {mean(ga,'burden_gini'):.5f}, a difference of {delta('burden_gini'):.5f}. Figure 4 and Table GA1 distinguish group outcomes from dispersion. Groups are tract quartiles rather than equal-population bins, with population weighting within each group. Absolute gaps and Gini are calculated per realization before averaging."
    abstract_old='The direct community-objective genetic search did not improve its best deterministic incumbent, impact-first.'
    assert abstract_old in text(pars[3])
    change(1,'Coauthor review copy of the retained July 23, 2026 manuscript reconstruction, with October 10 Stage 7 integration and October 11 frozen GA validation. Historical network and restoration findings retain their original cohorts; neither the typology nor the new GA is automatically promoted.','Review-copy provenance updated; source manuscript unchanged')
    change(3,text(pars[3]).replace(abstract_old,'A frozen random-initialized GA evaluated on a separate 2,000-realization cohort reduced mean population loss by 0.533 h relative to impact-first, but increased absolute quartile separation and burden Gini.'),'New candidate-specific evidence; independent historical results retained')
    change(20,'A complete 92-station priority permutation was optimized with a GA initialized by 100 independent uniformly random permutations, with ordered crossover probability 0.80, swap mutation probability 0.10, tournament size 3 and one generational elite. No heuristic or previously optimized order entered initialization or the archive. Twenty runs used seeds 2026103100-2026103119 and separate caches, each with 100,000 distinct evaluations; cached duplicates did not consume the budget. Candidate fitness was minus the original mean normalized population-weighted service-loss integral across the same 64 disjoint 2pc50 planning realizations, with the original physical samples, repair durations, dispatch scheduler, directed travel, M1 mapping and G1 source gate unchanged. The minimum-loss final order across these runs was selected; ties within 1e-9 h were resolved by lowest seed. The unique selected order came from seed 2026103108 with planning loss 32.99552241352315 h. No new search was performed for this selection. Its full permutation, SHA-256, search history, within-run tie conventions and reused 64-state production verification are in the reproducibility package.','One final GA protocol and actual random-only candidate; old surrogate and warm-start methods removed')
    change(24,text(pars[24]).replace('saved 1,000-realization 2pc50 direct-community sequence','saved historical 1,000-realization 2pc50 Impact-first sequence (previously labeled direct-community), not the newly validated GA sequence'),'Keep unchanged Stage 7 recovery inputs and exact labels; no silent epoch substitution')
    validation='After the candidate, controls and analysis were frozen, 2,000 new paired physical realizations were drawn under unchanged 2pc50/C57_D1/M1/G1 (seed 2026110300; independent per-realization SeedSequences). No physical hash overlapped the 5,064 registered prior states. Three fixed orders were evaluated: GA, Impact-first and the legacy formal order, the last retained only as a supplementary provenance comparator. All 6,000 production trajectories passed independent kernel parity and saved event-integral checks. Inference resampled whole paired realizations 20,000 times (seed 2026110400). Simultaneous 95% Bonferroni percentile intervals cover the two population-loss contrasts; other intervals are descriptive pointwise 95%. No validation-time tuning, priority search or reselection occurred.'
    additions={30:[(validation,'New fixed validation scope and inference')],41:[(ga_result,'Prospective population and mechanism results'),(hospital,'Candidate-specific hospital-associated loss and system T80'),(equity,'Negative distributional finding retained')]}
    for anchor,items in additions.items():
        at=pars[anchor]
        for value,reason in items:
            p=deepcopy(pars[40]);patch_text(p,value);at.addnext(p);at=p
            ledger.append(dict(location=f'after original paragraph P{anchor:03d}',action='INSERT',reason=reason,before='',after=value))
        if anchor==41:
            caption=deepcopy(pars[51]);patch_text(caption,'Table GA1. Prospective 2,000-realization GA and Impact-first outcomes under 2pc50/C57_D1/M1/G1. Values are means; original tables retain their historical cohorts. T80 is a per-realization system crossing, hospital burden is an unweighted associated-tract mean, and gap and Gini are realization-specific before averaging.');at.addnext(caption);at=caption
            table=deepcopy(tables[2])
            rows=table.findall('w:tr',NS)
            for r in rows[1:]:table.remove(r)
            metrics=[primary,'T80_restricted_hr','hospital_mean_normalized_burden_hr','burden_Q1_hr','burden_Q4_hr','absolute_Q4_minus_Q1_hr','burden_gini']
            for policy,label in [(ga,'GA'),(impact,'Impact-first'),(None,'GA minus Impact')]:
                row=deepcopy(rows[1]);values=[label]+[f'{(delta(m) if policy is None else mean(policy,m)):.3f}' if m!='burden_gini' else f'{(delta(m) if policy is None else mean(policy,m)):.5f}' for m in metrics]
                for cell,value in zip(row.findall('w:tc',NS),values):patch_text(cell.find('w:p',NS),value)
                table.append(row)
            at.addnext(table)
            ledger.append(dict(location='after prospective results in section 3.3',action='INSERT',reason='Separate new-cohort table without renumbering original tables',before='',after=text(caption)+' '+text(table)))
    change(40,'In the archived 1,000-realization fixed-rule evaluation, '+text(pars[40])[0].lower()+text(pars[40])[1:],'Historical cohort marked explicitly')
    change(43,'In the archived 1,000-realization cohort, '+text(pars[43])[0].lower()+text(pars[43])[1:],'Historical quartile values are not relabeled as new validation')
    change(58,'The GA result is an expected-loss comparison for one fixed candidate, not proof of global optimality or universal improvement. Random-only initialization was a data-supported post-data methodological choice, not a pass of the original automatic adoption rule. Only 10 of 20 individual 100,000-evaluation runs met the strict planning-proximity threshold of 0.001 h above the previously frozen planning best, below the prespecified 90%. Repeated-run selection does not imply that every run finds the same quality. Candidate-specific independent validation cannot be inherited from an older sequence. Hospital-associated burden and dispersion remain separate from the aggregate mean-loss objective.','Preserve post-data choice and failed single-run reliability gate')
    change(60,text(pars[60])+' The new GA validation adds an efficiency benefit against Impact-first without an equity benefit: lower absolute group burdens coexist with greater separation and Gini. It does not alter the historical typology recovery coordinates or establish a new cluster-specific priority.','Integrate fresh results without changing scientific definitions')
    old='The revised direct-objective genetic search retained its impact-first deterministic incumbent.'
    assert old in text(pars[67])
    change(67,text(pars[67]).replace(old,'On a separate 2,000-realization prospective cohort, the fixed random-initialized GA lowers mean population loss by 0.533 h against Impact-first, while increasing absolute quartile separation and Gini.'),'Conclusion updated only for the new GA comparison')
    change(128,'Figure 1. Mean population-weighted effective-service trajectories on 2,000 new paired physical realizations under 2pc50/C57_D1/M1/G1. Blue denotes the frozen GA and orange Impact-first. Panel A expands the first 96 h; panel B retains the full 0-480 h horizon. Values are modeled availability proxies, not delivered MW. The crossing of a mean curve is not mean per-realization system T80.','New candidate-specific mean recovery curves')
    change(130,'Figure 2. Archived 1,000-realization Impact-first tract T80 (formerly labeled direct-community). Values are mean-trajectory service-availability proxy crossings, not results for the newly validated GA.','Preserve historical map bytes while distinguishing its saved sequence')
    change(132,text(pars[132])+' Archived 1,000-realization fixed-rule cohort; this is not the new GA comparison.','Preserve unaffected historical figure and identify its cohort')
    change(134,'Figure 4. New-cohort absolute group burdens and dispersion for GA versus Impact-first under 2pc50/C57_D1/M1/G1. Panel A shows population-weighted means within fixed SOVI tract quartiles (Q1 lowest, Q4 highest vulnerability); panels B and C show paired changes in mean per-realization absolute Q4-Q1 separation and population-weighted Gini. Intervals are descriptive pointwise 95%. All groups improve in absolute burden, but both disparity measures increase. Groups are not equal-population bins.','Candidate-specific fairness results; unfavorable endpoints retained')
    caption='Figure 7. Frozen four-class typology of 2,287 complete residential tracts under archived 2pc50/C57_D1/M1/G1 Impact-first recovery, not the new GA. Classes use'+text(pars[140]).split('Classes use',1)[1]
    change(140,caption,'Unchanged Stage 7 figure source epoch explicit; concise caption to retain page fit')
    row=tables[0].findall('w:tr',NS)[-1]
    before=text(row)
    for c,value in zip(row.findall('w:tc',NS),['Optimization','Random-initialized GA; 20 seeds; 100,000 distinct calls/run','Fixed prospective 2,000-realization comparison','Expected aggregate loss; hospital and disparity reported separately']):patch_text(c.find('w:p',NS),value)
    ledger.append(dict(location='Table 1 optimization row',action='REPLACE',reason='Actual final protocol',before=before,after=text(row)))
    c=tables[2].findall('w:tr',NS)[2].find('w:tc',NS)
    before=text(c);patch_text(c.find('w:p',NS),'Impact-first (archived cohort)')
    ledger.append(dict(location='Table 3 Impact-first row label',action='REPLACE',reason='No old value attributed to new GA',before=before,after=text(c)))
    relxml=E.fromstring(parts['word/_rels/document.xml.rels'])
    rels={r.get('Id'):r.get('Target') for r in relxml}
    media_changes={}
    for idx,name,height in [(127,'FIG_GA_RECOVERY',90),(133,'FIG_GA_EQUITY',125)]:
        rid=pars[idx].find('.//a:blip',NS).get('{'+NS['r']+'}embed')
        target='word/'+rels[rid]
        assert target.endswith('.png')
        payload=(OUT/'artwork'/(name+'.png')).read_bytes()
        media_changes[target]=payload
        # Keep source inline width; update height to the actual plot aspect ratio.
        for extent in pars[idx].xpath('.//wp:extent | .//a:xfrm/a:ext',namespaces=NS):
            extent.set('cy',str(round(int(extent.get('cx'))*height/180)))
        changes[idx]='[authorized figure replacement]'
        ledger.append(dict(location=f'original paragraph P{idx:03d} / {target}',action='REPLACE_IMAGE',reason='New fixed candidate and fresh cohort, source inline width retained',before=sha(parts[target]),after=sha(payload)))
    unchanged_pars=[i for i in old_xml if i not in changes]
    assert all(E.tostring(pars[i])==old_xml[i] for i in unchanged_pars)
    assert all(E.tostring(tables[i])==old_tables[i] for i in (1,3,4))
    newparts=dict(parts);newparts.update(media_changes)
    newparts['word/document.xml']=E.tostring(xml,xml_declaration=True,encoding='UTF-8',standalone=True)
    target=REVIEW/'Manuscript_Random_GA_Validation_REVIEW.docx'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in newparts.items():z.writestr(name,data)
    with zipfile.ZipFile(target) as z:
        changed=[n for n in parts if z.read(n)!=parts[n]]
        assert set(changed)=={'word/document.xml',*media_changes}
    reopened=Document(target)
    assert len(reopened.inline_shapes)==8 and len(reopened.tables)==6
    assert sha(SOURCE.read_bytes())==SOURCE_SHA
    with (REVIEW/'MANUSCRIPT_PARAGRAPH_CHANGE_LEDGER.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['location','action','reason','before','after']);writer.writeheader();writer.writerows(ledger)
    dump(OUT/'MANUSCRIPT_STRUCTURAL_QA.json',dict(status='PASS',source=str(SOURCE),source_sha256=SOURCE_SHA,
        review_sha256=sha(target.read_bytes()),changed_package_parts=changed,
        unchanged_package_parts=[n for n in parts if n not in changed],
        unchanged_original_paragraph_indices=unchanged_pars,unchanged_tables=[1,3,4],
        original_images=8,review_images=8,new_table='GA1',tracked_changes=False,
        source_untouched=True,stage7_values_and_labels_untouched=True,
        physics_calls=0,bootstrap_calls=0,source_cohort_separated=True,
        numerical_source_sha256={n:sha((OUT/n).read_bytes()) for n in ['POLICY_OUTCOMES.csv','PAIRED_EFFECTS.csv']},
        rendering='PENDING actual render inspection'))
    print('DOCX_CREATED',target,'SHA256',sha(target.read_bytes()),'changed_parts',changed)

if __name__=='__main__':main()
