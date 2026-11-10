"""Compare all generated suite and mirror file hashes across two builds."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
before=json.loads((HERE/'IDEMPOTENCE_BUILD1.json').read_text(encoding='utf-8'))
after=json.loads((HERE/'BUILD_OUTPUT_HASHES.json').read_text(encoding='utf-8'))
paths=sorted(set(before)|set(after))
changed=[path for path in paths if before.get(path)!=after.get(path)]
result={'build_1_file_count':len(before),'build_2_file_count':len(after),
        'all_generated_files_byte_identical':not changed,
        'changed_paths':changed}
assert len(before)==len(after) and not changed,result
(HERE/'IDEMPOTENCE_QA.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
