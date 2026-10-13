"""Read committed dependency text, never execute legacy generators."""
import re
from common import *

EXPLICIT = [
    'src/la_grid/core/C257H_Project_Main.py',
    'src/la_grid/revision/formal/stage7.py',
    'src/la_grid/revision/r1_stage7_harmonized.py',
    'src/la_grid/revision/run_stage7_sovi_harmonization.py',
    'src/la_grid/plotting/Project_Visualizer.py',
    'src/la_grid/plotting/Project_Visualizer_expanded.py',
    'src/la_grid/plotting/make_manuscript_composites.py',
    'src/la_grid/plotting/render_revised_stage7.py',
    'src/la_grid/plotting/refine_policy_cluster_presentation.py',
    'src/la_grid/plotting/r1_formal_figures.py',
    'src/la_grid/plotting/build_revised_result_suite.py',
    'src/la_grid/plotting/render_revised_suite.py',
    'src/la_grid/plotting/update_framework_figure.py',
    'src/la_grid/plotting/index_revised_suite.py',
    'src/la_grid/plotting/update_coauthor_figure_index.py',
    'src/la_grid/plotting/render_final_artwork_remediation.py',
    'src/la_grid/paths.py',
    'tests/test_stage7_sovi_harmonization.py',
    '.github/workflows/stage7-physical-feature-gate.yml',
    'FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/run_08_stage7_typology.py',
    'FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/README.md',
    'FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/STAGE8_OUTPUT_HASHES.json',
    'FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/STAGE_VALIDATION_MANIFEST.json',
    'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json',
    'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md',
    'results/figure_review/FIGURE_MANIFEST.csv',
    'results/figure_review/README.md',
    'results/figures/FIGURE_INDEX.csv',
    'results/figures/README.md',
    'Formal_Experiment_20260923/FORMAL_STAGE7_INPUT_IDENTITY.json',
    'Formal_Experiment_20260923/STAGE7_EXECUTION_IDENTITY.json',
]


def main():
    sources = Sources()
    paths = git('ls-tree', '-r', '--name-only', AUTH).decode().splitlines()
    missing = [p for p in EXPLICIT if p not in paths]
    assert not missing, missing
    pattern = re.compile(r'stage.?7|Fig0?7|FigS0?9|hotspot|2291|2,291|residential_typology|CLUSTER_(?:OLD|NEW)|range\(1,\s*6\)|five.?cluster|5.?cluster', re.I)
    texts, records, matches = {}, [], []
    scan = [p for p in paths if (p.startswith('src/') or p.startswith('tests/') or p.startswith('FINAL_REVISION_RUN_SEQUENCE/')) and Path(p).suffix in ['.py', '.md', '.json', '.yml']]
    scan += [p for p in EXPLICIT if p not in scan]
    for rel in scan:
        path = sources.source(rel)
        text = path.read_text(encoding='utf-8-sig')
        found = [(i, line) for i, line in enumerate(text.splitlines(), start=1) if pattern.search(line)]
        if found or rel in EXPLICIT:
            texts[rel] = text
            for i, line in found:
                matches.append(dict(path=rel, line=i, text=line.strip(), sha256=sha(path)))
    for rel in EXPLICIT:
        dest('evidence/' + rel).write_text(texts[rel], encoding='utf-8', newline='\n')
        records.append(dict(path=rel, sha256=sha(sources.source(rel)), matching_lines=sum(m['path'] == rel for m in matches)))
    save('FORMAL_DEPENDENCY_MATCHES.csv', matches)
    save('FORMAL_DEPENDENCY_SOURCE_HASHES.csv', records)
    legacy = 'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv'
    legacy_top = 'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/stage7_top10_slow_vulnerable_tracts.csv'
    for rel, target in [(legacy, 'LEGACY_2291_CLUSTER_AND_HOTSPOT_VALUES.csv'), (legacy_top, 'LEGACY_TOP10.csv')]:
        dest('inputs/' + target).write_bytes(sources.source(rel).read_bytes())
    old = frame('inputs/LEGACY_2291_CLUSTER_AND_HOTSPOT_VALUES.csv', 'tract_id')
    raw_ids = old.index.copy()
    assert raw_ids.str.fullmatch(r'\d{10,11}').all()
    old.index = old.index.str.zfill(11)
    assert old.index.str.fullmatch(r'06037\d{6}').all()
    assert set(old.index).issubset(frame('inputs/FULL_2315_COHORT_STATUS.csv', 'tract_id').index)
    save('LEGACY_GEOID_TEXT_CANONICALIZATION.csv', [dict(source_text=a, canonical_GEOID=b,
        restored_leading_zero_only=a != b, numeric_FIPS_unchanged=int(a) == int(b)) for a,b in zip(raw_ids,old.index)])
    assert len(old) == 2291 and old.index.is_unique
    assert np.isfinite(old.SlowVulnerable_Hotspot_Score).all()
    save('D1_LEGACY_SCORE_GEOID_VALUES.csv', old[['SlowVulnerable_Hotspot_Score', 'SlowVulnerable_Hotspot_Rank', 'SlowVulnerable_Hotspot_Top10']].reset_index())
    source_lines = texts['src/la_grid/core/C257H_Project_Main.py'].splitlines()
    excerpt = []
    for i, line in enumerate(source_lines):
        if 'Hotspot_' in line or 'SlowVulnerable_Hotspot_' in line:
            excerpt.extend(f'{j + 1}: {source_lines[j]}'.rstrip() for j in range(max(0, i - 2), min(len(source_lines), i + 3)))
    md('D1_FORMAL_DEFINITION_SOURCE_EXCERPTS.md', '\n'.join(dict.fromkeys(excerpt)))
    captions = texts['results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md']
    sections = []
    for heading in ['## Figure 7.', '## Supplementary Figure S9.']:
        start = captions.index(heading)
        end = captions.find('\n## ', start + 1)
        sections.append(captions[start:end if end >= 0 else None].strip())
    md('CURRENT_FORMAL_CAPTIONS_EXACT_EXTRACT.md', '\n\n'.join(sections))
    tracked_manuscripts = [p for p in paths if p.lower().endswith(('.doc', '.docx'))]
    local_candidates = [Path(r'C:\Users\yinch\Downloads\LA Grid Paper Revised.docx'),
                        SOURCE_ROOT / 'provenance/legacy_outputs/Submission_Package/Manuscript_IJDRR.docx']
    save('MANUSCRIPT_AUTHORITY_PATH_AUDIT.csv', [dict(path=p, tracked_at_authority=True, role='ARCHIVED_OR_MEETING_NOT_ESTABLISHED_CURRENT') for p in tracked_manuscripts] +
         [dict(path=str(p), exists=lp(p).is_file(), sha256=sha(p) if lp(p).is_file() else '', role='LOCAL_CANDIDATE_ONLY_AUTHOR_MUST_IDENTIFY_ACTIVE_MANUSCRIPT') for p in local_candidates])
    save('SOURCE_HASH_VERIFICATION_DEPENDENCIES.csv', sources.records)
    dump('DEPENDENCY_AUDIT_SUMMARY.json', dict(authority=AUTH, scanned_files=len(scan), matched_files=len(texts),
         explicit_current_dependencies=len(EXPLICIT), legacy_D1_cohort=2291, D1_new_8_tracts_unavailable=True,
         active_manuscript_not_confirmed=True, no_legacy_generator_executed=True))
    print('Read-only dependencies verified:', len(texts), 'files;legacy D1 values preserved exactly', flush=True)


if __name__ == '__main__':
    main()
