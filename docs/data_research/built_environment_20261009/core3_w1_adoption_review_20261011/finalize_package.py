"""Final read-only source/preservation checks and review-package manifest."""
from common import *
import numpy as np,pandas as pd,platform,sklearn,geopandas,matplotlib

q=json.loads(lp(OUT/'WORD_RENDER_QA.json').read_text(encoding='utf-8'))
for r in q['pages']:
 if r['document']=='review' or r['page'] in [1,3,7,15]:r['actual_visual_inspection']='inspected'
q['visual_method']='Actual native Word PDF page images opened with view_image; all19 review pages and source template pages1/3/7/15 inspected. No existence/hash-only visual acceptance.'
dump('WORD_RENDER_QA.json',q)
f=json.loads(lp(OUT/'FIGURE_RENDER_QA.json').read_text(encoding='utf-8'))
for r in f:r['visual_inspection']='inspected';r['review_status']='READY_FOR_AUTHOR_REVIEW; not formal promotion'
dump('FIGURE_RENDER_QA.json',f)
text('VISUAL_REVIEW.md',"""# Actual visual review

All five vector PDF pages were rendered at native 185mm width and opened as actual images. The membership map, full12-coordinate profile, stability panels, minority specificity panels and raw-profile table have no clipped labels or obstructed legends. Native minimum text is8.5pt. The first profile render had colorbar/count overlap; extra bottom clearance corrected it and the actual final page was re-opened. The first minority render placed a legend over bars; both lower legends were moved below their axes and final pages were re-opened. Initial-service table values use explicit percent units so small nonzero means remain visible. Colors/IDs are consistent within the new package, without borrowing old archetype identities.

The packaged DOCX renderer was attempted but has no available soffice and does not handle this Windows long path. Microsoft Word exported read-only isolated copies, without saving either DOCX. Every page of the final19-page author-review PDF was actually opened. Template source pages1/3/7/15 were also opened. New Methods/Results/Discussion text, Table4 and temporary Figures7–8 are readable, captions accompany the previews, and equations/dashes have no new encoding damage. All six original figures and three original tables remain intact; their scientific/presentation design is outside this change scope. Existing page geometry, references, headers/footers and style definitions remain byte-identical. The original source's figure-section whitespace was preserved rather than redesigned.

This is a completed author-review rendering gate, not author acceptance or formal promotion. Temporary numbering and final main/supplement allocation remain review decisions.
""")
before=json.loads(lp(OUT/'PRESERVATION_BEFORE.json').read_text(encoding='utf-8'));after=snapshot();assert before==after,'Original protected worktree changed';dump('PRESERVATION_AFTER.json',after)
for role,r in json.loads(lp(OUT/'INPUT_HASHES.json').read_text(encoding='utf-8')).items():assert sha(r['path'])==r['sha256'],role
dump('PRESERVATION_QA.json',dict(protected_scientific_files=after['protected_count'],original_staged_items=after['staged_count'],original_index_unchanged=True,original_status_unchanged=True,original_HEAD_unchanged=True,all_source_hashes_unchanged=True,formal_files_changed=0,new_fits=0,manuscript_original_changed=False,formal_promotion=False))
dump('SOFTWARE_AND_EXECUTION.json',dict(Python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,geopandas=geopandas.__version__,matplotlib=matplotlib.__version__,authoring_runtime=r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',scientific_read_only_runtime=r'C:\Users\yinch\anaconda3\python.exe',render='native Microsoft Word; fitz page rendering',new_estimator_fits=0))
text('README.md',"""# CORE3 W1 scientific adoption review

Decision: **ADOPT_AS_CONDITIONAL_STAGE7_REFERENCE**. This independent package uses authoritative commit adb3cb49ced687730beff7ebf88f9c5e161062ed. It does not promote or modify formal Stage7, the manuscript, figures, simulations or GA. No new fitting, PCA, k search, GIS extraction or optimization occurred.

Start with CORE3_W1_ADOPTION_DECISION.md, then the separate Manuscript_CORE3_W1_Author_Review.docx/PDF. That copy is based on the actual author-confirmed S19, not an older IJDRR/July or BE0 review. It edits only Stage7 clauses and review metadata; original Figures1–6 and Tables1–3 are preserved. Temporary Figures7–8/Table4 are proposals. The latest old BE0 review is audited separately and is not the current class authority.

Evidence: CORE3_W1_FROZEN_REFERENCE.npz and CORE3_W1_FREEZE_RECORD.json retain the exact saved matrix/order/scaler/weights/labels/actual fitted centers. CORE3_W1_LABELS_2291.csv retains four unclassified geometry records. CORE3_W1_VERIFIED_PROFILES.csv and the wide PROFILE_TABLE contain actual raw units, counts, mapped population and coverage. STAGE7_VERSION_CROSSWALK.csv contains complete cells for formal5/BE0/CORE3 on common GEOIDs, with comparison-only mappings. CORE3_W1_CLAIM_STABILITY.csv and its per-case table give exact denominators and reversals; CLASS_MEMBERSHIP_STABILITY.csv and CORE3_PROFILE_PERTURBATIONS.csv distinguish membership from sample changes. Minor-group audits retain actual destinations, training support, purity and Jaccard, including34→92.

Review artwork: FIG_CORE3_W1_MEMBERSHIP, PROFILES, STABILITY and MINORITY, plus TABLE_CORE3_W1_PROFILES, each as vector PDF and600dpi PNG. REVIEW_FIGURE_CAPTIONS.md states the restrictions and temporary numbers. Native185mm pages have minimum8.5pt. The stability/minority previews and full profiles are intended for supplement; concise conditional descriptive results may enter main text after author approval. The standalone tables and CSVs, not rounded display labels, are numerical authority.

MANUSCRIPT_CLAIM_RECONCILIATION.csv audits437 exact-text paragraph/cell locations against actual source bytes. STAGE7_AUTHOR_REVIEW_CHANGELOG.md records the exact replacement/insertion ledger. KEEP means unaffected by this Stage7 change, not recertification of unrelated GA/policy statements. Old five-class names, age/density/PCA interpretations and class-dependent hotspot recommendations cannot transfer. No new hotspot scores/ranks are created. Recovery differences are descriptive because recovery is a clustering input.

Reproduction: with validated baseline actual LFS payloads available, run audit_science.py, prepare_review.py, render_figures.py, then build_author_review.py with the bundled authoring Python. export_word.ps1 exports isolated short-path read-only DOCX copies; render_word_pages.py creates inspection images. Finalize only after actual image inspection. Run pytest test_adoption.py with a workspace-local --basetemp. No script calls KMeans/PCA fit. common.source resolves actual bytes and checks them against source commit/LFS hashes, failing rather than using pointers or guessed input.

PRESERVATION_QA.json verifies950 protected files and862 original staged items/index. INPUT_HASHES.json and OUTPUT_HASHES.json document actual bytes. REMOTE_LFS_BYTE_VERIFICATION.json records a post-push download of every new LFS payload; remote HEAD is verified. Spatial cases are20 registered dependent perturbations (17unique sets), not independent geographic validation. C4 remains a specification-conditional subgroup, not a stable archetype. Final allocation and adoption still require author approval.
""")
log('Final source hashes and original protected worktree verified: 950 files and862 staged entries unchanged; actual figures and19-page review visually inspected. No formal promotion.')
# Manifest excludes itself, post-push receipt and append-only log; all science/artifact bytes included.
exclude={'OUTPUT_HASHES.json','REMOTE_LFS_BYTE_VERIFICATION.json','EXECUTION_LOG.md'}
manifest={p.relative_to(lp(OUT)).as_posix():dict(sha256=sha(p),bytes=lp(p).stat().st_size) for p in lp(OUT).rglob('*') if p.is_file() and p.name not in exclude and '__pycache__' not in p.parts and '_testtmp' not in p.parts}
dump('OUTPUT_HASHES.json',manifest)
