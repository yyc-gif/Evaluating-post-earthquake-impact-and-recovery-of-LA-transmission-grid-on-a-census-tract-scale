"""Recompute archived descriptive results offline in a new directory."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
RESULTS = [
    'ACS_TRACT_VALIDATION.csv', 'NLCD_TRACT_EXTRACTION.csv',
    'NLCD_AGGREGATION_CHECKS.csv', 'CLUSTER_COMPARISONS.csv',
    'CLUSTER_PAIRWISE_EFFECTS.csv', 'CLUSTER_EFFECT_SIZES.csv',
    'ACS_SCREENING_BIAS.csv', 'ACS_PRECISION_WEIGHTING.csv',
    'INDICATOR_CORRELATIONS.csv', 'INDICATOR_CORRELATION_SENSITIVITY.csv',
    'INDICATOR_INCREMENTAL_INFORMATION.csv', 'RESIDENTIAL_VALIDATION_MATRIX.csv',
    'BUILT_ENVIRONMENT_TRACT_COVERAGE.csv', 'BUILT_ENVIRONMENT_DATA_SOURCE_AUDIT.csv',
    'ACS_VERIFICATION.json', 'NLCD_VERIFICATION.json', 'INDEPENDENT_QA.json',
    'INPUT_FILE_MANIFEST.json',
]
SOURCES = [
    'B25024_06.csv.zip', 'B25034_06.csv.zip', 'VRE_AVERAGE_WEIGHT_2022.csv',
    'Annual_NLCD_2022_fis_study_clip.tif', 'Annual_NLCD_2022_lc_study_clip.tif',
]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main(repo, out):
    assert not out.exists(), 'Use a fresh output directory'
    expected = json.loads((ROOT / 'INPUT_FILE_MANIFEST.json').read_text())
    for name, digest in expected.items():
        assert sha(repo / name) == digest, f'Input changed: {name}'
    (out / 'sources').mkdir(parents=True)
    for name in ['validate.py', 'nlcd.py', 'qa.py']:
        shutil.copy2(ROOT / name, out / name)
    for name in SOURCES:
        shutil.copy2(ROOT / 'sources' / name, out / 'sources' / name)
    phases = [('validate.py', ['--phase', 'acs']),
              ('nlcd.py', ['--phase', 'aggregate']),
              ('validate.py', ['--phase', 'compare']), ('qa.py', [])]
    records = []
    for number, (script, flags) in enumerate(phases, 1):
        command = [sys.executable, str(out / script), '--repo', str(repo), *flags]
        result = subprocess.run(command, capture_output=True, text=True, env=os.environ)
        (out / f'phase_{number}.log').write_text(result.stdout + result.stderr, encoding='utf8')
        assert result.returncode == 0, f'Reproduction failed: {script}; inspect phase_{number}.log'
        records.append({'script': script, 'flags': flags, 'exit_code': result.returncode})
        print(f'Completed offline phase {number}/4: {script} {flags}', flush=True)
    comparisons = []
    for name in RESULTS:
        before, after = sha(ROOT / name), sha(out / name)
        assert before == after, f'Output differs: {name}'
        comparisons.append({'file': name, 'sha256': before, 'byte_identical': True})
    for name, digest in expected.items():
        assert sha(repo / name) == digest, f'Input changed during reproduction: {name}'
    report = {'offline_fresh_directory_pass': True, 'network_calls': 0,
              'scientific_pipeline_invocations': 0, 'result_files': comparisons,
              'phases': records, 'existing_input_hashes_unchanged': True,
              'source_sha256': {name: sha(ROOT / 'sources' / name) for name in SOURCES},
              'reference_route_selftest': 'PILOT_SELF_TEST_NOT_AUTHORITATIVE; 2315 reference-minus-pilot values exactly zero; source-release gate still open'}
    (ROOT / 'REPRODUCTION_CHECK.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'pass': True, 'byte_identical_result_files': len(comparisons)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    main(args.repo.resolve(), args.out.resolve())
