"""Use the established downloader to verify actual remote LFS payload bytes."""
import importlib.util
from types import SimpleNamespace
import study as s


def main():
    s.configure();s.verify()
    assert s.preserved()==s.v.read(s.OUT/'PRESERVATION_BASELINE.json')
    changed=s.git(s.ROOT,'diff','--name-only',s.PARENT,'HEAD').decode().splitlines()
    assert changed and all(p.startswith(s.REL+'/') for p in changed),changed
    source=s.BASE/'results/diagnostics/ga_random_initialization_isolation_20261011/publish.py'
    spec=importlib.util.spec_from_file_location('existing_verified_publication',s.v.long_path(source))
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.s=SimpleNamespace(ROOT=s.ROOT,OUT=s.ROOT/s.REL,BRANCH=s.BRANCH,
        lp=s.v.long_path,digest=s.v.sha,save=s.v.write,
        git=lambda *args:s.git(s.ROOT,*args))
    helper.remote()
    receipt=s.v.read(s.OUT/'REMOTE_PUBLICATION_VERIFIED.json')
    receipt.update(protected_files_and_staging_preserved=True,
        samples_generated=2000,production_evaluations=6000,optimizer_searches=0,
        formal_strategy_promoted=False,
        preexisting_external_exception=s.preserved()['preexisting_external_exception'],
        reused_publication_helper_sha256=s.v.sha(s.v.long_path(source)))
    s.v.write(s.OUT/'REMOTE_PUBLICATION_VERIFIED.json',receipt)


if __name__=='__main__':main()
