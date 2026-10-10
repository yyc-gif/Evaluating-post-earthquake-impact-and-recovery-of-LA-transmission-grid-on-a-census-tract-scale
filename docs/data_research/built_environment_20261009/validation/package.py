"""Manifest and export only this validation package, never generated caches."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def selected():
    roots = [p for p in ROOT.iterdir() if p.is_file() and
             (p.name == '.gitignore' or p.suffix in {'.py', '.md', '.csv', '.json', '.txt'})
             and p.name != 'PACKAGE_MANIFEST.json']
    sources = [p for p in (ROOT / 'sources').iterdir()
               if p.is_file() and not p.name.endswith('_VRE_LA.csv')]
    return sorted(roots + sources, key=lambda p: p.relative_to(ROOT).as_posix())


def main(phase, out):
    if phase == 'manifest':
        members = {p.relative_to(ROOT).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
                   for p in selected()}
        report = {'start_head': 'dab976173dcb5da7fdbd4a2c91d879317a797331',
                  'branch': 'revision/reviewer-driven-core-rebuild-v2',
                  'purpose': 'Existing-label descriptive validation only',
                  'excluded': ['vendor', '__pycache__', '_reference*', '_reproduction*',
                               '_*.npz', '_*.tif', 'sources/*_VRE_LA.csv', 'vre_equation5.png'],
                  'members': members}
        (ROOT / 'PACKAGE_MANIFEST.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    report = json.loads((ROOT / 'PACKAGE_MANIFEST.json').read_text())
    assert set(report['members']) == {p.relative_to(ROOT).as_posix() for p in selected()}
    for name, record in report['members'].items():
        assert sha(ROOT / name) == record['sha256'], f'Package changed: {name}'
        assert (ROOT / name).stat().st_size == record['bytes']
    if phase == 'export':
        assert out is not None and not out.exists(), 'Export to a new directory only'
        for name in [*report['members'], 'PACKAGE_MANIFEST.json']:
            dest = out / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dest)
            assert sha(dest) == sha(ROOT / name)
    print(json.dumps({'phase': phase, 'member_count': len(report['members']),
                      'total_bytes': sum(x['bytes'] for x in report['members'].values()),
                      'all_member_hashes_pass': True}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['manifest', 'verify', 'export'], required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    main(args.phase, args.out)
