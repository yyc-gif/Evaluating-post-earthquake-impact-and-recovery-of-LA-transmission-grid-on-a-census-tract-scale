"""Run lightweight package contracts and record exact derived-file hashes."""
import json
import subprocess
import sys

from audit import OUT, ROOT, SPEC, dump, git, longpath, sha


def main():
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    changed=git('diff','--name-only',SPEC['baseline_commit']).decode().splitlines()
    untracked=git('ls-files','--others','--exclude-standard').decode().splitlines()
    assert all(p.startswith(prefix) for p in changed+untracked),changed+untracked
    commands=[
        [sys.executable,'-m','compileall','-q',str(longpath(OUT))],
        [sys.executable,'-m','pytest','-q','test_audit.py','--basetemp','./test_tmp'],
    ]
    results=[]
    for command in commands:
        result=subprocess.run(command,cwd=OUT,text=True,capture_output=True,encoding='utf-8')
        shown=['AUDIT_PACKAGE_DIRECTORY' if arg==str(longpath(OUT)) else arg for arg in command[1:]]
        results.append(dict(command=['python',*shown],exit_code=result.returncode,
                            stdout=result.stdout.strip(),stderr=result.stderr.strip()))
        print(result.stdout, end='')
        print(result.stderr, end='', file=sys.stderr)
        result.check_returncode()
    before=json.loads((OUT/'PRESERVATION_BEFORE.json').read_text())
    after=json.loads((OUT/'PRESERVATION_AFTER.json').read_text())
    assert before==after
    dump('PACKAGE_VALIDATION.json',dict(status='PASS',checks=results,
         changed_paths_scoped_to_package=True,protected_files_unchanged=before['protected_count'],
         no_formal_changes=True,no_simulation_or_clustering=True))
    files={}
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name not in {'DERIVED_FILE_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json'}:
            files[path.name]=dict(sha256=sha(path),bytes=longpath(path).stat().st_size)
    dump('DERIVED_FILE_HASHES.json',files)
    print('VALIDATED_PACKAGE',len(files),'files; scope only; protected files unchanged')


if __name__=='__main__':
    main()
