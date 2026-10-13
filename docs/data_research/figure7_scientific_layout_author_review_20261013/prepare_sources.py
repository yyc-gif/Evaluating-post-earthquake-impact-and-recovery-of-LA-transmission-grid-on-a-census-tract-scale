"""Retrieve actual pinned Figure 7 artwork and freeze review-only inputs."""
from pathlib import Path
import io
import json
import re
import sys

ROOT = Path(str(Path(__file__).resolve().parents[3]).removeprefix('\\\\?\\'))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import fitz
import pandas as pd

OLD = '59d9001edadef57c5ff1dc6af6ca8d7817fb4f94'
CURRENT = '8f2dcb3b9762137b9f2686609c34480334f5d44e'
FROZEN = '0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
DECISION = '05a78645b17bf8de04326e54181f9db432d7186c'
SCIENTIFIC = '49cc153c3f4d7a8c29cf94baf090dbfc0be4d068'
SP = 'docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/'
DP = 'docs/data_research/stage7_fig7d_policy_robustness_and_final_integration_gate_20261013/'
INPUTS = HERE / 'inputs'
sources = []


def acquire(commit, rel, name):
    b = u.payload(commit, rel)
    pointer = u.git('show', commit + ':' + rel)
    match = re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)', pointer)
    sources.append({'commit': commit, 'path': rel, 'local': 'inputs/' + name,
                    'sha256': u.digest(b), 'bytes': len(b), 'lfs_oid': match[1].decode() if match else None})
    u.write(INPUTS / name, b)
    return b


def state(root):
    index = u.git('rev-parse', '--path-format=absolute', '--git-path', 'index', root=root).decode().strip()
    return {'HEAD': u.git('rev-parse', 'HEAD', root=root).decode().strip(),
            'status_sha256': u.digest(u.git('status', '--porcelain=v1', '-z', root=root)),
            'index_sha256': u.sha(index),
            'staged_names_sha256': u.digest(u.git('diff', '--cached', '--name-only', '-z', root=root))}


def main():
    for name in ['.gitattributes', '.gitignore']:
        if not (ROOT / name).exists():
            u.write(ROOT / name, u.git('show', CURRENT + ':' + name))
    reference = json.loads(u.payload(CURRENT, 'docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/PRESERVATION_BEFORE.json'))
    protection = u.protected_snapshot(reference)
    assert protection['protected_count'] == 950
    u.dump(HERE / 'PRESERVATION_BEFORE.json', protection)
    checkouts = [ROOT.parent / name for name in ['_ok13', '_xc13', '_fs12']]
    states = {str(p): state(p) for p in checkouts}
    official = ROOT.parent / '_ok13'
    tracked = u.git('ls-files', '-z', 'results/figure_review', 'results/figures',
                    'src/la_grid/plotting/build_current_suite_k3.py', root=official).decode().split('\0')
    official_hashes = {p: u.sha(official / p) for p in tracked if p}
    u.dump(HERE / 'INITIAL_OFFICIAL_SUITE_AND_WORKTREE_STATE.json', {
        'source_branch': 'review/official-figure-suite-ncv14-h2-k3-d3-20261013', 'HEAD': CURRENT,
        'remote_HEAD_verified': CURRENT, 'worktrees': states, 'official_tracked_file_hashes': official_hashes,
        'initial_review_HEAD': u.git('rev-parse', 'HEAD').decode().strip()})
    for commit, name in [(OLD, 'HISTORICAL_FIGURE7'), (CURRENT, 'CURRENT_FIGURE7')]:
        b = acquire(commit, 'results/figure_review/Main/Fig07.pdf', name + '.pdf')
        caps = acquire(commit, 'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md', name + '_CAPTIONS.md')
        with fitz.open(stream=b, filetype='pdf') as d:
            p = d[0]
            p.get_pixmap(dpi=160, alpha=False).save(u.lp(HERE / (name + '_185MM.png')))
            spans = [s for block in p.get_text('dict', flags=0)['blocks'] for line in block.get('lines', []) for s in line['spans']]
            u.dump(HERE / (name + '_ARTWORK_INSPECTION.json'), {'size_mm': [v * 25.4 / 72 for v in [p.rect.width, p.rect.height]],
                'text': p.get_text(), 'spans': [{'text': s['text'], 'size': s['size'], 'bbox': s['bbox'], 'color': s['color']} for s in spans],
                'image_objects': len(p.get_images()), 'vector_paths': len(p.get_cdrawings())})
        caption = next((b for h, b in u.captions(caps.decode()).items() if h.startswith('Figure 7.')))
        print(name, caption, flush=True)
    for rel, name in [
        ('candidate/EIGHT_VARIABLE_FROZEN_TABLE.csv', 'EIGHT_VARIABLE_FROZEN_TABLE.csv'),
        ('candidate/COHORT_STANDARDIZER_AND_WEIGHTS.csv', 'COHORT_STANDARDIZER_AND_WEIGHTS.csv'),
        ('candidate/K3_CLUSTER_MEMBERSHIP.csv', 'K3_CLUSTER_MEMBERSHIP.csv'),
        ('candidate/CLASS_ID_REGISTRY.csv', 'CLASS_ID_REGISTRY.csv'),
        ('candidate/FULL_2315_COHORT_STATUS.csv', 'FULL_2315_COHORT_STATUS.csv'),
        ('candidate/FROZEN_PREPROCESSING_AND_LABELS.npz', 'FROZEN_PREPROCESSING_AND_LABELS.npz'),
        ('candidate/FROZEN_CANDIDATE_SPECIFICATION.json', 'FROZEN_CANDIDATE_SPECIFICATION.json'),
        ('figures.py', 'FROZEN_FIGURE_CANDIDATE_SOURCE.py')]:
        acquire(FROZEN, SP + rel, name)
    acquire(DECISION, DP + 'FROZEN_POLICY_TRACT_MEANS_2315.csv', 'FROZEN_POLICY_TRACT_MEANS_2315.csv')
    acquire(CURRENT, 'results/figure_review/CURRENT_CLUSTER_PALETTE.json', 'CURRENT_CLUSTER_PALETTE.json')
    acquire(CURRENT, 'src/la_grid/plotting/build_current_suite_k3.py', 'CURRENT_GENERATOR_SOURCE.py')
    acquire(OLD, 'results/figure_review/CURRENT_CLUSTER_PALETTE.json', 'HISTORICAL_CLUSTER_PALETTE.json')
    acquire(OLD, 'src/la_grid/plotting/finish_author_figure_suite_20261012.py', 'HISTORICAL_FINISH_SOURCE.py')
    acquire(OLD, 'src/la_grid/plotting/Project_Visualizer.py', 'HISTORICAL_THEME_GENERATOR_SOURCE.py')
    acquire(OLD, 'docs/reproducibility/COAUTHOR_MAP_LEGEND_FEEDBACK_20261008.md', 'ARCHIVED_WHITE_NA_AUTHOR_RECORD.md')
    acquire(OLD, 'docs/reproducibility/official_figure_suite_review_20261012/write_review_memo.py', 'ARCHIVED_WHITE_NA_REVIEW_SOURCE.py')
    u.dump(HERE / 'SOURCE_AUTHORITY_AND_HASHES.json', {'old_artwork': OLD, 'current_suite': CURRENT,
        'frozen_K3': FROZEN, 'D3_decision': DECISION, 'natural_hazard_scientific_authority': SCIENTIFIC,
        'sources': sources, 'no_scientific_models_run': True})
    print('Actual old/current artwork rendered, input payloads verified, original 950 files protected.', flush=True)


if __name__ == '__main__':
    main()
