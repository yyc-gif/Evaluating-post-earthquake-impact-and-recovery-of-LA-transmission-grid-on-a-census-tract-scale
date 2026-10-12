from common import *
import sys
def snapshot():
    keys=json.load(open(lp(PKG/'PRESERVATION_BEFORE.json'),encoding='utf-8'))['protected_files']
    return {'original_HEAD':git('rev-parse','HEAD',root=ORIGINAL).decode().strip(),
        'protected_files':{p:sha(ORIGINAL/p) for p in keys},'protected_count':len(keys),
        'index_sha256':hashlib.sha256(git('ls-files','--stage','-z',root=ORIGINAL)).hexdigest(),
        'status_sha256':hashlib.sha256(git('status','--porcelain=v1','-z',root=ORIGINAL)).hexdigest(),
        'staged_count':len([p for p in git('diff','--cached','--name-only','-z',root=ORIGINAL).split(b'\0') if p])}
if __name__=='__main__':
    s=snapshot();name='PRESERVATION_AFTER.json' if '--after' in sys.argv else 'PRESERVATION_BEFORE.json'
    if '--after' in sys.argv:assert s==json.load(open(lp(PKG/'PRESERVATION_BEFORE.json'),encoding='utf-8'))
    dump(name,s)
    if '--after' not in sys.argv:
        with open(lp(PKG/'STARTING_GIT_STATUS.txt'),'wb') as f:
            f.write(git('status','--short',root=ORIGINAL))
    print(name,'protected',s['protected_count'],'staged',s['staged_count'])
