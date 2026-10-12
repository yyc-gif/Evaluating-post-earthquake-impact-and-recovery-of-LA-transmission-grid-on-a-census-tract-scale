"""Reuse the established actual-byte remote verifier, scoped to this package."""
import importlib.util
import sys
from types import SimpleNamespace
import audit as a


def remote():
    source=a.BASE/'results/diagnostics/ga_random_initialization_isolation_20261011'
    sys.path.insert(0,str(source))
    spec=importlib.util.spec_from_file_location('existing_remote_verifier',source/'publish.py')
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.s=SimpleNamespace(ROOT=a.ROOT,OUT=a.OUT,BRANCH=a.BRANCH,
        git=a.git,lp=a.lp,digest=a.sha,
        save=lambda path,value:a.save(str(path.relative_to(a.OUT)),value))
    m.remote()


if __name__=='__main__':
    remote()
