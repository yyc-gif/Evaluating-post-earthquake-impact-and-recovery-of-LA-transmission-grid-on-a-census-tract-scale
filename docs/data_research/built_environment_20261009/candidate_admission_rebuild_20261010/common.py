from pathlib import Path
import hashlib, json, subprocess, datetime

def lp(p):
    s=str(p)
    return Path(s if s.startswith('\\\\?\\') else '\\\\?\\'+str(Path(p).absolute()))

OUT = lp(Path(__file__).resolve().parent)
ROOT = OUT.parents[3]
ORIGINAL = lp(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
RESEARCH = ORIGINAL/'docs/data_research/built_environment_20261009'
BASELINE = '13064debde45f9d0b3cad37276fe844040722b8b'
RAW = OUT/'raw_cache'
RAW.mkdir(exist_ok=True)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def dump(name, obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=str)+'\n',encoding='utf-8')

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git',*args],cwd=str(cwd).removeprefix('\\\\?\\'))

def log(message):
    print(message,flush=True)
    with (OUT/'EXECUTION_LOG.md').open('a',encoding='utf-8') as f:
        f.write(f'- {datetime.datetime.now(datetime.timezone.utc).isoformat()}: {message}\n')

def source(relative):
    """Prefer the actual local payload; verify it against the audited commit."""
    rel='docs/data_research/built_environment_20261009/'+relative
    expected=git('show',f'{BASELINE}:{rel}')
    if expected.startswith(b'version https://git-lfs.github.com/spec/v1'):
        expected_sha=expected.decode().split('oid sha256:')[1].splitlines()[0]
    else: expected_sha=hashlib.sha256(expected).hexdigest()
    choices=[ROOT/rel,ORIGINAL/rel,ROOT.parent/'_cw10'/rel,ROOT.parent/'_stage7_be_validity_20261010'/rel]
    for p in choices:
        if p.exists() and sha(p)==expected_sha:
            records=json.loads((OUT/'REUSED_SOURCE_HASHES.json').read_text()) if (OUT/'REUSED_SOURCE_HASHES.json').exists() else {}
            records[rel]={'path':str(p),'sha256':expected_sha,'source_commit':BASELINE,'bytes':p.stat().st_size}
            dump('REUSED_SOURCE_HASHES.json',records)
            return p
    raise FileNotFoundError('No verified payload for '+rel)

def snapshot():
    previous=json.loads(source('built_env_validity_controlled_audit_20261010/PRESERVATION_BEFORE.json').read_text())
    protected=previous['protected_files']
    result={}
    for rel,expected in protected.items():
        if isinstance(expected,dict): expected=expected.get('sha256')
        p=ORIGINAL/rel
        result[rel]={'sha256':sha(p) if p.exists() else None,'historical_sha256':expected}
    status=git('status','--porcelain=v1','-z',cwd=ORIGINAL)
    index=git('ls-files','--stage','-z',cwd=ORIGINAL)
    staged=git('diff','--cached','--name-only','-z',cwd=ORIGINAL).split(b'\0')
    return {'original_head':git('rev-parse','HEAD',cwd=ORIGINAL).decode().strip(),
            'original_branch':git('branch','--show-current',cwd=ORIGINAL).decode().strip(),
            'logical_index_sha256':hashlib.sha256(index).hexdigest(),
            'status_sha256':hashlib.sha256(status).hexdigest(),
            'staged_count':sum(bool(x) for x in staged),
            'status_record_count':len([x for x in status.split(b'\0') if x]),
            'protected_files':result,'protected_count':len(result),
            'protected_present_count':sum(x['sha256'] is not None for x in result.values()),
            'historical_hash_mismatches':[k for k,v in result.items() if v['sha256']!=v['historical_sha256']]}

if __name__=='__main__':
    dump('PRESERVATION_BEFORE.json',snapshot())
    log('Protected original worktree/index snapshot captured; independent branch at '+BASELINE)
