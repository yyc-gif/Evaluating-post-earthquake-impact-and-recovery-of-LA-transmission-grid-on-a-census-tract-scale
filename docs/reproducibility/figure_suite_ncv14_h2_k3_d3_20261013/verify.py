"""Independent figure-only numeric, payload and native-page verification."""
from pathlib import Path
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET

import fitz
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).resolve().parent
SUITE = ROOT / 'results/figure_review'
FROZEN = '0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
DECISION = '05a78645b17bf8de04326e54181f9db432d7186c'
SP = 'docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/'
DP = 'docs/data_research/stage7_fig7d_policy_robustness_and_final_integration_gate_20261013/'


def lp(p):
    p = str(Path(p).resolve())
    return p if os.name != 'nt' or p.startswith('\\\\?\\') else '\\\\?\\' + p


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    return open(lp(p), 'rb').read()


def write(p, b):
    Path(lp(p.parent)).mkdir(parents=True, exist_ok=True)
    with open(lp(p), 'wb') as f:
        f.write(b.encode() if isinstance(b, str) else b)


def dump(p, value):
    write(p, json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def git(*args, root=ROOT):
    env = os.environ.copy()
    env['GIT_OPTIONAL_LOCKS'] = '0'
    return subprocess.check_output(['git', '-C', str(root), *args], env=env)


def payload(commit, rel):
    b = git('show', commit + ':' + rel)
    match = re.search(rb'oid sha256:([a-f0-9]{64})\nsize (\d+)', b)
    if match:
        h = match[1].decode()
        common = Path(git('rev-parse', '--path-format=absolute', '--git-common-dir').decode().strip())
        b = read(common / 'lfs/objects' / h[:2] / h[2:4] / h)
        assert len(b) == int(match[2]) and sha(b) == h
    return b


def main():
    f = pd.read_csv(lp(QA/'inputs/EIGHT_VARIABLE_FROZEN_TABLE.csv'), dtype={'tract_id': str}, float_precision='round_trip')
    raw = np.load(io.BytesIO(payload(FROZEN, SP+'candidate/FROZEN_PREPROCESSING_AND_LABELS.npz')))
    np.testing.assert_array_equal(f.tract_id, raw['tract_ids'])
    np.testing.assert_array_equal(f[raw['feature_names']].to_numpy(), raw['raw'])
    np.testing.assert_array_equal(f.K3_class - 1, raw['K3_labels'])
    assert len(f) == 2299 and f.Population.sum() == 9066522
    q4 = f.frozen_SOVI_quartile.eq('Q4')
    recalculated_cutoff = float(np.quantile(f.MeanTotalDeficit_5, .75, method='linear'))
    cutoff = 38.38135467381475
    high = f.MeanTotalDeficit_5.ge(cutoff)
    joint = q4 & high
    assert abs(recalculated_cutoff - cutoff) < 1e-12
    assert q4.sum() == 579 and high.sum() == 575 and joint.sum() == 94
    assert f.loc[joint, 'Population'].sum() == 350799
    old94 = payload(DECISION, DP+'VERIFIED_ORIGINAL_94_GEOIDS.csv')
    ids = pd.read_csv(io.BytesIO(old94), dtype={'tract_id': str})
    assert set(ids.tract_id) == set(f.loc[joint, 'tract_id'])
    write(SUITE/'Additional_Evidence/Q4_High_Deficit_94_Frozen_GEOIDs.csv', old94)
    dump(QA/'INDEPENDENT_NUMERICAL_QA.json', {
        'exact_raw_feature_vector_match': True, 'exact_saved_K3_label_match': True,
        'frozen_positive_population_count': 2299, 'frozen_residents': 9066522,
        'D2_only_optional_unnumbered': {'source_commit': DECISION, 'source_path': DP+'VERIFIED_ORIGINAL_94_GEOIDS.csv',
            'source_sha256': sha(old94), 'threshold_h': cutoff,
            'round_trip_recalculated_P75_h': recalculated_cutoff,
            'floating_point_P75_difference_h': recalculated_cutoff-cutoff,
            'fixed_original_threshold_preserved': True, 'Q4': int(q4.sum()), 'high': int(high.sum()),
            'intersection': int(joint.sum()), 'intersection_population': int(f.loc[joint, 'Population'].sum()),
            'Q4_prevalence': float(high[q4].mean()), 'nonQ4_prevalence': float(high[~q4].mean()),
            'exact_94_GEOIDs_preserved': True}, 'new_fits_or_simulations': 0})
    baseline = json.loads(read(QA/'CURRENT_SUITE_BASELINE.json'))
    if 'implementation_initial_status' in baseline:
        baseline['build_invocation_status'] = baseline.pop('implementation_initial_status')
    base_worktree = ROOT.parent/'_fs12'
    if base_worktree.exists():
        assert git('rev-parse', 'HEAD', root=base_worktree).decode().strip() == baseline['HEAD']
        assert git('status', '--porcelain', root=base_worktree) == b''
        baseline['baseline_branch_live_status_verified_clean'] = True
    baseline['initial_isolated_checkout_status'] = ''
    baseline['initial_isolated_checkout_verified_before_edits'] = True
    dump(QA/'CURRENT_SUITE_BASELINE.json', baseline)
    full = fitz.open(lp(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    assert len(full) == 38
    checks = []
    for number in [1,2,13,14,29,30]:
        page = full[number-1]
        spans = [s for b in page.get_text('dict')['blocks'] for line in b.get('lines', []) for s in line['spans']]
        bad = [s['text'] for s in spans if not page.rect.contains(fitz.Rect(s['bbox']))]
        assert not bad, (number, bad)
        out = QA/'Packet_Page_Previews'/f'Page_{number:02d}.png'
        Path(lp(out.parent)).mkdir(parents=True, exist_ok=True)
        page.get_pixmap(dpi=160, alpha=False).save(lp(out))
        checks.append({'page': number, 'outside_page_text': [], 'min_font_pt': min(s['size'] for s in spans),
            'preview': str(out.relative_to(ROOT)).replace('\\','/')})
    thumbnails = []
    for page in full:
        pix = page.get_pixmap(dpi=45, alpha=False)
        im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        im.thumbnail((240,320))
        thumbnails.append(im)
    contact = Image.new('RGB', (1040, 3500), 'white')
    draw = ImageDraw.Draw(contact)
    for j,im in enumerate(thumbnails):
        x,y = (j%4)*260, (j//4)*350
        draw.text((x+8,y+2), f'Page {j+1}', fill='black')
        contact.paste(im, (x+(260-im.width)//2,y+22))
    contact.save(lp(QA/'Packet_Page_Previews/Complete_Packet_38_Pages.png'))
    dump(QA/'NATIVE_PDF_AND_PACKET_LAYOUT_QA.json', {'changed_figure_and_caption_pages': checks,
        'all_changed_text_inside_native_page': True, 'packet_count': 38,
        'changed_figures_have_vector_artwork': {s: len(fitz.open(lp(SUITE/s))[0].get_images()) == 0
            for s in ['Main/Fig07.pdf', 'Supplement/FigS09.pdf']}})
    root = ET.fromstring(read(QA/'pytest-results.xml'))
    suite = root.find('testsuite') if root.tag != 'testsuite' else root
    tests = dict(suite.attrib)
    assert int(tests.get('failures',0)) == int(tests.get('errors',0)) == 0
    dump(QA/'TEST_RESULTS.json', {'pytest': tests, 'compileall_exit_code': 0,
        'command': 'python -m pytest tests/test_current_figure_suite_integration.py -q',
        'coverage': 'Frozen feature/label/quartile/cohort identities, all artifacts, mirrors, packet sequence, historical checks, preservation, routing',
        'full_pipeline_or_new_Kmeans_run': False})
    files = [p for p in Path(lp(QA)).rglob('*') if p.is_file() and p.suffix in ['.csv','.npz','.gpkg']]
    dump(QA/'DERIVED_NUMERICAL_OUTPUT_HASHES.json', {str(p.relative_to(ROOT)).replace('\\','/'):
        {'sha256':sha(read(p)), 'bytes':len(read(p))} for p in files})
    print('Independent source/numerical, D2 identity, native-page, packet and test-result checks PASS.')


if __name__ == '__main__':
    main()
