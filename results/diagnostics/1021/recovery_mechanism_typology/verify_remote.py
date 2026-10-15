"""Fresh-store verification of actual new LFS bytes and explicit branch heads."""
from support import *
import re
import subprocess
import time


def extended(path):
    return Path("\\\\?\\"+str(path.resolve())) if os.name=="nt" else path


def main(write=True):
    head=git("rev-parse","refs/heads/1021").decode().strip()
    def remote(branch):
        return git("ls-remote","origin","refs/heads/"+branch).decode().split()[0]
    assert remote("1021")==head
    assert remote("2026-10-14")==legacy.FROZEN
    paths=git("diff","--name-only",START,head).decode().splitlines()
    assert paths and all(p.startswith("results/diagnostics/1021/recovery_mechanism_typology/") for p in paths)
    rows=[]
    for path in paths:
        blob=git("show",head+":"+path)
        match=re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n",blob)
        if match:
            rows.append({"path":path,"oid":match[1].decode(),"size":int(match[2])})
    cache=ROOT/"build"/("rm_"+hex(time.time_ns())[-8:])
    assert not cache.exists()
    cache.mkdir(parents=True)
    command=["git","-C",str(ROOT),"-c","lfs.storage="+str(cache),"lfs","fetch",
             "--include="+",".join(row["path"] for row in rows),"--exclude=","origin",head]
    fetched=subprocess.run(command,capture_output=True,text=True)
    assert fetched.returncode==0,fetched.stdout+fetched.stderr
    for row in rows:
        oid=row["oid"]
        path=extended(cache/"objects"/oid[:2]/oid[2:4]/oid)
        assert path.stat().st_size==row["size"]
        assert sha(path)==oid==sha(ROOT/row["path"])
    assert remote("1021")==head and remote("2026-10-14")==legacy.FROZEN
    result={"status":"PASS_ACTUAL_REMOTE_PAYLOAD_BYTES","artifact_commit":head,"remote_HEAD_matches":True,
            "explicit_branch":"refs/heads/1021","publication_remote_commit_unchanged":legacy.FROZEN,
            "empty_download_store":True,"paths_verified":len(rows),
            "unique_bytes_downloaded":sum({row["oid"]:row["size"] for row in rows}.values()),"payloads":rows}
    if write:
        dump("REMOTE_DELIVERY_VERIFICATION.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!="payloads"},indent=2))


if __name__=="__main__":
    main(write="--no-write" not in sys.argv)
