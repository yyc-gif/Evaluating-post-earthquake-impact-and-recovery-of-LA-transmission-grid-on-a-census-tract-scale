"""Independent scientific identity, claim-denominator and manuscript preservation gates."""
import json,zipfile,hashlib
import numpy as np
import pandas as pd
from lxml import etree as E
from sklearn.metrics import adjusted_rand_score
from common import *

def j(n):return json.loads(lp(OUT/n).read_text(encoding='utf-8'))
def csv(n):return pd.read_csv(lp(OUT/n),dtype={'tract_id':str})

def test_saved_solution_and_exact_geoids():
 z=np.load(lp(OUT/'CORE3_W1_FROZEN_REFERENCE.npz'));a=np.load(src(W+'run_records/W1.npz'))
 assert z['feature_columns'].tolist()==COLS and np.array_equal(z['tract_ids'],a['tract_ids'])
 for key,sourcekey in [('labels','s42_labels'),('fitted_centers','s42_centers'),('scaler_mean','scaler_mean'),('scaler_scale','scaler_scale'),('coordinate_factors','coordinate_factors')]:assert np.array_equal(z[key],a[sourcekey])
 assert np.bincount(z['labels']).tolist()==[650,802,801,34]
 m=csv('CORE3_W1_LABELS_2291.csv');assert len(m)==2291 and m.tract_id.is_unique and m.tract_id.str.fullmatch(r'\d{11}').all()
 assert set(m[m.review_class.isna()].tract_id)==set(UNRESOLVED)
 assert len(csv('OUTSIDE_RESIDENTIAL_COHORT.csv'))==24

def test_original_unit_values_population_and_weight_budgets():
 z=np.load(lp(OUT/'CORE3_W1_FROZEN_REFERENCE.npz'));assert np.isclose(np.square(z['coordinate_factors']).sum(),1)
 p=csv('CORE3_W1_VERIFIED_PROFILES.csv')
 for k in range(4):
  for i,c in enumerate(COLS):
   r=p[(p.review_class==f'C{k+1}')&(p.feature==c)].iloc[0]
   v=z['values'][z['labels']==k,i];assert np.isclose(v.mean(),r['mean']) and np.isclose(np.median(v),r['median'])
 m=csv('CORE3_W1_PROFILE_TABLE.csv');assert m.n.sum()==2287 and m.mapped_population.sum()==9037153
 assert csv('UNCLASSIFIED_RESIDENTIAL_TRACTS.csv').formal_population.sum()==12390
 assert csv('OUTSIDE_RESIDENTIAL_COHORT.csv').formal_population.sum()==16979
 d=csv('VERIFIED_DOMAIN_SEPARATION.csv');assert np.allclose(d.TSS,d.BSS+d.WSS,atol=1e-8)
 assert d.groupby(['scheme','seed']).domain_between_fraction.sum().sub(1).abs().max()<1e-12

def test_all_claim_support_denominators():
 c=csv('CORE3_W1_CLAIM_STABILITY.csv');v=csv('CLAIM_STABILITY_CASE_VALUES.csv')
 assert len(c)==720 and len(v)==14400 and c.N.eq(20).all()
 for _,r in c.iterrows():
  sub=v[(v.class_a==r.class_a)&(v.class_b==r.class_b)&(v.feature==r.feature)&(v.comparison_family==r.comparison_family)]
  assert len(sub)==20 and sub.seed.nunique()==20
  assert sub.supports_reference_direction.sum()==r.supporting_cases and sub.reverses_reference_direction.sum()==r.contradicting_cases
  assert r.supporting_cases+r.contradicting_cases+r.exact_zero_cases==20
 r=c[(c.class_a=='C2')&(c.class_b=='C3')&(c.feature=='B_480_hr')&(c.comparison_family=='W5_full')].iloc[0];assert r.contradicting_cases==20

def test_crosswalk_cells_and_version_ari():
 m=csv('STAGE7_TRACT_VERSION_MEMBERSHIP.csv');q=j('STAGE7_VERSION_COMPARISON_QA.json');d=csv('STAGE7_VERSION_CROSSWALK.csv')
 assert len(m)==2287 and m.tract_id.is_unique
 for name,a,b in [('A_FORMAL5__B_BE0_4','A_formal_class','B_BE0_raw_class'),('A_FORMAL5__C_CORE3_W1_4','A_formal_class','C_CORE3_raw_class'),('B_BE0_4__C_CORE3_W1_4','B_BE0_raw_class','C_CORE3_raw_class')]:assert np.isclose(adjusted_rand_score(m[a],m[b]),q[name]['ARI'])
 assert d.groupby(['source_version','target_version']).n.sum().eq(2287).all()
 assert np.allclose(d.groupby(['source_version','target_version','source_class']).fraction_of_source.sum(),1)
 assert not d.scientific_equivalence.any()

def test_minority_specificity_and_destination_conservation():
 d=csv('CORE3_W1_MINOR_GROUP_AUDIT.csv');r=d.query('scheme=="W1" and seed==54 and scope=="spatial_all"').iloc[0]
 assert r.training_support==4 and r.original_members_retained==34 and r.matched_prediction_n==92 and r.incoming_nonreference_members==58
 assert np.isclose(r.purity,34/92) and np.isclose(r.Jaccard,34/92) and r.retention==1
 assert d.query('scope=="full_fit"').training_support.eq(34).all()
 for _,r in d.iterrows():assert sum(json.loads(r.destination_counts))==r.reference_n
 for s in ['W2','W3','W5']:
  r=d.query('scheme==@s and seed==54 and scope=="spatial_all"').iloc[0];assert r.original_members_retained==0 and sum(json.loads(r.destination_counts))==34
 c=csv('CLASS_MEMBERSHIP_STABILITY.csv');assert len(c)==1200
 assert c.prediction_n.ge(c.intersection).all() and c.baseline_n.ge(c.intersection).all()

def test_source_docx_unrelated_content_preserved_and_no_encoding_damage():
 p=j('INPUT_HASHES.json')['AUTHOR_CONFIRMED_S19']['path'];ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 with zipfile.ZipFile(lp(p)) as a,zipfile.ZipFile(lp(OUT/'Manuscript_CORE3_W1_Author_Review.docx')) as b:
  for n in a.namelist():
   if n not in ['word/document.xml','word/_rels/document.xml.rels']:assert a.read(n)==b.read(n)
  old=E.fromstring(a.read('word/document.xml'));new=E.fromstring(b.read('word/document.xml'));op=old.findall('w:body/w:p',ns);np_=new.findall('w:body/w:p',ns)
  changed={2,9,23,40,47};texts=[''.join(x.xpath('.//w:t/text()',namespaces=ns)) for x in np_]
  for i,p0 in enumerate(op,1):
   if i not in changed:assert E.tostring(p0) in [E.tostring(p1) for p1 in np_]
  old23=''.join(op[22].xpath('.//w:t/text()',namespaces=ns));prefix=old23.split('The retained Stage 7')[0];assert any(t.startswith(prefix) for t in texts)
  old40=''.join(op[39].xpath('.//w:t/text()',namespaces=ns));prefix=old40.split('The Stage 7 descriptive')[0];assert any(t==prefix for t in texts)
  assert any('Q4−Q1' in t and '±1 h' in t for t in texts)
  assert not any('âˆ' in t or 'Â±' in t for t in texts)
 assert j('DOCX_FIDELITY_QA.json')['original_images_preserved']==6

def test_no_new_fits_and_review_gate_not_promotion():
 q=j('INDEPENDENT_SCIENTIFIC_QA.json');assert q['new_fits']==q['new_PCA']==q['new_k_searches']==q['new_physical_or_GA_runs']==0
 assert q['adoption_decision']=='ADOPT_AS_CONDITIONAL_STAGE7_REFERENCE' and not q['formal_promotion']
 assert j('CORE3_W1_FREEZE_RECORD.json')['exact_saved_solution_not_refit']
 d=csv('MANUSCRIPT_CLAIM_RECONCILIATION.csv')
 assert set(d.required_action)<= {'KEEP','REVISE','REMOVE','MOVE TO SUPPLEMENTARY','REQUIRES SEPARATE VALIDATION'}
 assert len(d)==437 and d.original_exact_text.notna().all()

def test_actual_render_receipts_and_pdf_identity():
 import fitz
 q=j('WORD_RENDER_QA.json');review=[r for r in q['pages'] if r['document']=='review'];assert len(review)==19
 assert all(r['actual_visual_inspection']=='inspected' and not r['text_outside_page'] for r in review)
 for r in j('FIGURE_RENDER_QA.json'):
  assert r['visual_inspection']=='inspected' and r['min_font_pt']>=8.5
  with fitz.open(lp(OUT/(r['figure']+'.pdf'))) as d:assert len(d)==1 and abs(d[0].rect.width*25.4/72-185)<.001
 assert sha(OUT/'Manuscript_CORE3_W1_Author_Review.pdf')==q['native_export_pdf_sha256']
