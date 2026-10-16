"""Run the renderer again and compare all exported figure/preview bytes."""
from common import *
import sys


def main():
    targets=[p for p in lp(HERE).rglob("*") if p.is_file() and
             p.suffix.lower() in [".pdf",".png"] and "inputs" not in p.parts]
    before={p.relative_to(lp(HERE)).as_posix():sha(p) for p in targets}
    subprocess.run([sys.executable,str(HERE/"build_review.py")],cwd=ROOT,check=True)
    rows=[{"path":name,"before_sha256":wanted,"after_sha256":sha(HERE/name),
           "byte_identical":sha(HERE/name)==wanted} for name,wanted in before.items()]
    save("REBUILD_ARTWORK_HASH_COMPARISON.csv",rows)
    assert all(row["byte_identical"] for row in rows)
    dump("REBUILD_IDEMPOTENCE.json",{"status":"PASS","rendered_files":len(rows),
        "all_PDF_and_PNG_payloads_byte_identical":True,"models_refitted":0,
        "official_suite_builder_invoked":False,"command":"python build_review.py"})
    print("All",len(rows),"figure and preview files are byte-identical after rerender")


if __name__=="__main__":main()
