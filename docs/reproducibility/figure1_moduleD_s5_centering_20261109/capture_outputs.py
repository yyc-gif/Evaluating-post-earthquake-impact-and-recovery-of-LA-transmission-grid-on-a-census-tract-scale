"""Capture hashes for deterministic rebuild comparison."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
TREES=(
    ROOT/'results/figure_review_s6_main4_20261107',
    ROOT/'results/figures_s6_main4_20261107',
)
OUT=Path(__file__).resolve().parent
records={}
for tree in TREES:
    for path in sorted(p for p in tree.rglob('*') if p.is_file()):
        data=path.read_bytes()
        records[path.relative_to(ROOT).as_posix()]={
            'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
(OUT/'BUILD_OUTPUT_HASHES.json').write_text(
    json.dumps(records,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'file_count':len(records),'sha256_by_path':records},indent=2))
