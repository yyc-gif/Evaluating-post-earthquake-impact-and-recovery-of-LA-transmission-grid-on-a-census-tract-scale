"""Retrieve original LNS evidence and hydrate only verified frozen inputs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from datetime import datetime, timezone

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_research_collect_20261009 import long_path, save, session, get, pages
from la_grid.diagnostics.ga_research_preserve_20261009 import INPUTS, snapshot, git
from la_grid.diagnostics.ga_lns_outcome_reconcile_20261010 import collect, summary, paired

OUT = REPO_ROOT / 'results/diagnostics/ga_noncontiguous_connectivity_lns_20261010'
RUNS = (38033702030, 38034064901, 38065463263, 38065546076)


def hydrate(old):
    common = Path(git(old, 'rev-parse', '--git-common-dir').decode().strip())
    if not common.is_absolute():
        common = old / common
    receipt = []
    for name in INPUTS:
        p = long_path(REPO_ROOT / name)
        pointer = git(REPO_ROOT, 'show', 'HEAD:' + name)
        if pointer.startswith(b'version https://git-lfs.github.com/spec/v1'):
            fields = dict(line.split(' ', 1) for line in pointer.decode().splitlines())
            oid = fields['oid'][7:]
            obj = long_path(common / 'lfs/objects' / oid[:2] / oid[2:4] / oid)
            data = obj.read_bytes() if obj.exists() else long_path(old / name).read_bytes()
            assert hashlib.sha256(data).hexdigest() == oid and len(data) == int(fields['size'])
            p.write_bytes(data)
            target = long_path(REPO_ROOT / '.git/lfs/objects' / oid[:2] / oid[2:4] / oid)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        receipt.append(dict(path=name, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    save(OUT / 'FROZEN_INPUT_HYDRATION.json', receipt)


def retrieve():
    s = session(authenticate=True)
    manifest = dict(retrieved_at=datetime.now(timezone.utc).isoformat(), runs=[], artifacts=[])
    for run_id in RUNS:
        run = get(s, f'actions/runs/{run_id}')
        artifacts = pages(s, f'actions/runs/{run_id}/artifacts', 'artifacts')
        manifest['runs'].append({k: run[k] for k in ('id', 'head_sha', 'status', 'conclusion', 'html_url')})
        assert run['status'] == 'completed' and run['conclusion'] == 'success', run_id
        for a in artifacts:
            archive = long_path(OUT / 'original_artifacts' / str(run_id) / f"{a['id']}.zip")
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                assert not a['expired'], a
                response = s.get(a['archive_download_url'], timeout=180)
                response.raise_for_status()
                archive.write_bytes(response.content)
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            if a.get('digest'):
                assert a['digest'] == 'sha256:' + digest, a['id']
            dest = archive.with_suffix('')
            members = []
            with zipfile.ZipFile(archive) as z:
                for item in z.infolist():
                    if item.is_dir():
                        continue
                    path = dest / item.filename
                    assert path.resolve().is_relative_to(dest.resolve())
                    data = z.read(item)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                    members.append(dict(path=item.filename, sha256=hashlib.sha256(data).hexdigest()))
            manifest['artifacts'].append(dict(run_id=run_id, id=a['id'], name=a['name'],
                archive=str(archive.relative_to(long_path(REPO_ROOT))), sha256=digest, members=members))
            save(OUT / 'ORIGINAL_ACTIONS_MANIFEST.json', manifest)
        print('RETRIEVED', run_id, len(artifacts), flush=True)
    save(OUT / 'ORIGINAL_ACTIONS_MANIFEST.json', manifest)


def audit():
    expected = set(json.loads((REPO_ROOT / 'Formal_Experiment_20260923/Stage 5 Output_expanded/FINAL_DIRECT_COMMUNITY_SEQUENCE.json').read_text())['ordered_station_ids'])
    results = {}
    for version, run_id in [('v1', RUNS[0]), ('v2', RUNS[1])]:
        records, paths = collect(version, long_path(OUT / 'original_artifacts' / str(run_id)))
        for cases in records.values():
            for row in cases.values():
                assert set(row['best_sequence']) == expected
        data = summary(version, records)
        labels = [m['method'] for m in data['methods']]
        data['all_five_contrasts_simultaneous'] = [dict(candidate=a, reference=b,
            **paired([records[s][a]['search_best_loss_hr'] - records[s][b]['search_best_loss_hr'] for s in sorted(records)], 5))
            for a, b in [(labels[2], labels[3]), (labels[2], labels[0]), (labels[2], labels[1]), (labels[3], labels[1]), (labels[1], labels[0])]]
        results[version] = data
    transfer = []
    for p in long_path(OUT / 'original_artifacts' / str(RUNS[3])).rglob('RESULTS.json'):
        d = json.loads(p.read_text())
        assert d['status'] == 'COMPLETE'
        transfer.append(d)
    assert len(transfer) == 8 and {d['seed'] for d in transfer} == set(range(1000, 1008))
    results.update(status='160_FULL_RUNS_VERIFIED', observations=160,
        all_original_92_ids_verified=True, transfer_seed_count=8,
        repeated_checkpoints_not_independent=True, objective_calls_for_audit=0,
        multiplicity_note='Existing family=3 applies to three primary contrasts only. Five-contrast sensitivity supplied separately.')
    save(OUT / 'ORIGINAL_160_AUDIT.json', results)
    print(results['status'], flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--old-checkout', type=Path, required=True)
    p.add_argument('--revision-checkout', type=Path, required=True)
    p.add_argument('--verify-preservation', action='store_true')
    a = p.parse_args()
    current = snapshot(a.revision_checkout)
    dest = OUT / 'PRESERVATION_BASELINE.json'
    if a.verify_preservation:
        assert current == json.loads(long_path(dest).read_text()), 'Protected revision or staging changed.'
        save(OUT / 'PRESERVATION_VERIFIED.json', dict(status='PASS', **current))
        print('PRESERVATION_PASS', len(current['files_sha256']), flush=True)
        return
    if long_path(dest).exists():
        assert current == json.loads(long_path(dest).read_text())
    else:
        save(dest, current)
    hydrate(a.old_checkout)
    retrieve()
    audit()


if __name__ == '__main__':
    main()
