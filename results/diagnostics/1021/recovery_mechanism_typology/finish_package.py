"""Finalize local QA and hashes, confined to the new experiment package."""
from support import *
import importlib.metadata
import platform
import xml.etree.ElementTree as ET


def main():
    registry=json.loads((HERE/"FROZEN_INPUT_REGISTRY.json").read_text())
    after=snapshot()
    assert after==registry["publication_snapshot"]
    assert all(sha(ARCHIVE/path)==h for path,h in registry["protected_950"].items())
    dump("PRESERVATION_AFTER.json",{
        "publication_snapshot":after,"same_as_pre_experiment":True,
        "protected_950_files_unchanged":True,
        "prior_payloads_unchanged":all(sha(PARENT/p)==h for p,h in registry["preserved_prior_payloads"].items()),
        "prior_payload_count":len(registry["preserved_prior_payloads"]),
        "only_new_directory_changed":all(p.startswith("results/diagnostics/1021/recovery_mechanism_typology/")
                                         for p in git("diff","--name-only",START).decode().splitlines())})
    suites=list(ET.parse(HERE/"tests.xml").getroot().iter("testsuite"))
    assert sum(int(s.get("failures","0"))+int(s.get("errors","0")) for s in suites)==0
    dump("TEST_RESULTS.json",{
        "tests":sum(int(s.get("tests","0")) for s in suites),"failures":0,"errors":0,
        "skipped":sum(int(s.get("skipped","0")) for s in suites),"python":platform.python_version(),
        "versions":{k:importlib.metadata.version(k) for k in ["numpy","scipy","scikit-learn","pandas","geopandas","matplotlib","pytest","threadpoolctl"]},
        "independent_qa":json.loads((HERE/"INDEPENDENT_QA.json").read_text()),
        "scope":"All prior1021 method tests plus prior engineering tests plus this experiment's regression tests."})
    hashes={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.name not in ["PACKAGE_HASHES.json","REMOTE_DELIVERY_VERIFICATION.json"]}
    dump("PACKAGE_HASHES.json",hashes)
    print("Package",len(hashes),"payloads; preserved",len(registry["preserved_prior_payloads"]),"prior payloads and950 scientific files.")


if __name__=="__main__":
    main()
