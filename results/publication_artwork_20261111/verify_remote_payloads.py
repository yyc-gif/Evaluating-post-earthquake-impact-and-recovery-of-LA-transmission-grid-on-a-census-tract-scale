"""Download actual publication payloads; a Git LFS pointer is not delivery."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
BASE = '68c83459e60ef31f7e86af9155d5a11e1680235d'
REPOSITORY = 'yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    commit = git('rev-parse', args.commit)
    changed = set(git('diff', '--name-only', BASE, commit).splitlines())
    records = json.loads(git('lfs', 'ls-files', '--json', commit))['files']
    groups = {}
    for record in records:
        if record['name'] in changed:
            groups.setdefault(record['oid'], []).append(record)
    rows = []
    for oid, files in groups.items():
        record = files[0]
        path = record['name']
        assert path.startswith('results/publication_artwork_20261111/'), path
        url = f'https://media.githubusercontent.com/media/{REPOSITORY}/{commit}/' + urllib.parse.quote(path)
        for attempt in range(3):
            try:
                digest = hashlib.sha256()
                size = 0
                magic = b''
                with urllib.request.urlopen(url, timeout=180) as response:
                    status = response.status
                    for block in iter(lambda: response.read(1024 * 1024), b''):
                        if not magic:
                            magic = block[:64]
                        digest.update(block)
                        size += len(block)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(3 * (attempt + 1))
        assert status == 200 and digest.hexdigest() == oid, (path, size, digest.hexdigest(), oid)
        local = ROOT / path
        assert size == local.stat().st_size
        assert not magic.startswith(b'version https://git-lfs.github.com/spec/')
        suffix = local.suffix.lower()
        expected = {'.pdf': b'%PDF', '.png': b'\x89PNG', '.tif': b'II*\x00'}
        if suffix in expected:
            assert magic.startswith(expected[suffix]), (path, magic)
        rows.append(dict(paths=[r['name'] for r in files], sha256=oid, bytes=size,
                         http_status=status, actual_payload_downloaded=True, url=url))
        print(f'Verified {len(rows)}/{len(groups)}: {path} ({size:,} bytes)', flush=True)
    assert groups, 'No changed publication LFS objects were selected.'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(commit=commit, unique_lfs_objects=len(rows),
        downloaded_bytes=sum(r['bytes'] for r in rows), files=rows), indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
