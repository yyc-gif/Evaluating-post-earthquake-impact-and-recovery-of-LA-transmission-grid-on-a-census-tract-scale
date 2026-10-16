"""Fetch this experiment's LFS payloads into an independent verification store."""
from common import *
import argparse
import tempfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--no-write",action="store_true")
    args=parser.parse_args()
    assert git("symbolic-ref","HEAD")=="refs/heads/"+BRANCH
    head=git("rev-parse","HEAD")
    prefix=HERE.relative_to(ROOT).as_posix()+"/"
    paths=git("diff","--name-only",BASE,head).splitlines()
    assert paths and all(p.startswith(prefix) for p in paths)
    refs=git("ls-remote","--heads","origin","refs/heads/"+BRANCH,
             "refs/heads/2026-10-14","refs/heads/1021")
    remote={line.split()[1]:line.split()[0] for line in refs.splitlines()}
    assert remote["refs/heads/"+BRANCH]==head
    assert remote["refs/heads/2026-10-14"]==BASE
    before=json.loads(lp(HERE/"PRESERVATION_BEFORE.json").read_text())
    assert remote["refs/heads/1021"]==before["1021"]["HEAD"]
    records=[]
    for name in paths:
        blob=subprocess.check_output(["git","show",head+":"+name],cwd=ROOT)
        match=re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n",blob)
        if match:
            oid=match[1].decode();size=int(match[2])
            assert sha(ROOT/name)==oid and lp(ROOT/name).stat().st_size==size
            records.append({"path":name,"sha256":oid,"bytes":size})
    store=Path(tempfile.mkdtemp(prefix="bv15_remote_"))
    # An empty explicit store prevents success from a previously cached object.
    assert not list(store.iterdir())
    subprocess.run(["git","-c","lfs.storage="+str(store),"lfs","fetch",
                    "--include="+prefix+"**","--exclude=","origin",head],cwd=ROOT,check=True)
    for row in records:
        oid=row["sha256"];payload=store/"objects"/oid[:2]/oid[2:4]/oid
        assert lp(payload).is_file()
        assert lp(payload).stat().st_size==row["bytes"] and sha(payload)==oid
        row["fresh_remote_payload_sha256_matches"]=True
    assert git("ls-remote","--heads","origin","refs/heads/"+BRANCH)==head+"\trefs/heads/"+BRANCH
    report={"status":"PASS_ACTUAL_REMOTE_LFS_BYTES","verified_commit":head,
            "remote_refs":remote,"fresh_verification_store":str(store),
            "experiment_paths_only":True,"LFS_payloads":len(records),
            "total_verified_LFS_bytes":sum(r["bytes"] for r in records),"payloads":records,
            "publication_and_1021_remote_heads_unchanged":True,"no_merge_or_force_push":True}
    if not args.no_write:dump("REMOTE_DELIVERY_VERIFICATION.json",report)
    print(json.dumps({k:v for k,v in report.items() if k!="payloads"},indent=2))


if __name__=="__main__":main()
