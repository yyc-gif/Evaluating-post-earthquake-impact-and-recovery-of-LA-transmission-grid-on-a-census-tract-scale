"""Record completed tests and review-package hashes without self-hashing."""
from common import *
import xml.etree.ElementTree as ET
import platform
from importlib.metadata import version


def main():
    root=ET.parse(lp(HERE/"tests.xml")).getroot()
    suites=list(root.iter("testsuite"))
    totals={key:sum(int(s.get(key,0)) for s in suites) for key in ["tests","failures","errors","skipped"]}
    assert totals["tests"]==12 and totals["failures"]==totals["errors"]==totals["skipped"]==0
    dump("TEST_RESULTS.json",{"status":"PASS","pytest":totals,"Python":platform.python_version(),
        "command":"python -m pytest results/diagnostics/fig7d_continuous_bivariate_20261015/test_bivariate_review.py -q",
        "scope":"New visualization-only experiment; official suite was not rebuilt or modified"})
    dump("ENVIRONMENT.json",{"Python":platform.python_version(),"platform":platform.platform(),
         "packages":{name:version(name) for name in ["numpy","pandas","PyMuPDF","Pillow","geopandas","pytest"]},
         "fonts":{"Arial_SHA256":sha(FONT),"Arial_Bold_SHA256":sha(BOLD)}})
    excluded={"PACKAGE_HASHES.json","REMOTE_DELIVERY_VERIFICATION.json"}
    rows=[]
    for path in sorted(lp(HERE).rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or ".pytest_cache" in path.parts:continue
        name=path.relative_to(lp(HERE)).as_posix()
        if name not in excluded:rows.append({"path":name,"sha256":sha(path),"bytes":path.stat().st_size})
    dump("PACKAGE_HASHES.json",{"algorithm":"SHA256","excludes":sorted(excluded),"files":rows})
    print("Recorded",len(rows),"payload hashes and",totals["tests"],"passing tests")


if __name__=="__main__":main()
