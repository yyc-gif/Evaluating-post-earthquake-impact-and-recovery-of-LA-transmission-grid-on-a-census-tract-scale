"""Frozen visualization inputs and strictly scoped review outputs."""
from pathlib import Path
import hashlib
import io
import json
import os
import re
import subprocess
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE="b307e6deafc054864787a3db63ad95218be91659"
BRANCH="review/fig7d-continuous-bivariate-20261015"
PUBLICATION=ROOT.parent/"_final_p2"
EXPLORATION=ROOT.parent/"_1021"
ARCHIVE=Path("C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/LA_grid_reviewer_revision")
P75=38.38135467381475
D_RECT=(259.2,425.,518.4000244140625,648.)
PANEL_RECT=(259.2,409.,518.4000244140625,648.)
FONT=Path("C:/Windows/Fonts/arial.ttf")
BOLD=Path("C:/Windows/Fonts/arialbd.ttf")


def lp(p):
    if str(p).startswith("\\\\?\\"):return Path(p)
    p=Path(p).resolve()
    return Path("\\\\?\\"+str(p)) if os.name=="nt" else p


def sha(p):
    h=hashlib.sha256()
    with lp(p).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()


def git(*args,cwd=ROOT):
    return subprocess.check_output(["git",*args],cwd=cwd).decode().strip()


def source(rel):
    blob=subprocess.check_output(["git","show",BASE+":"+rel],cwd=ROOT)
    m=re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n",blob)
    if not m:return blob
    oid=m[1].decode()
    common=Path(git("rev-parse","--git-common-dir"))
    for p in [ROOT/rel,PUBLICATION/rel,EXPLORATION/rel,ARCHIVE/rel,common/"lfs/objects"/oid[:2]/oid[2:4]/oid]:
        if lp(p).is_file() and sha(p)==oid:return lp(p).read_bytes()
    raise FileNotFoundError(f"Missing actual source payload: {rel} {oid}")


def write(name,data):
    p=lp(HERE/name);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(data if isinstance(data,bytes) else data.encode("utf-8"))


def dump(name,data):
    write(name,json.dumps(data,indent=2,allow_nan=False)+"\n")


def save(name,data):
    write(name,pd.DataFrame(data).to_csv(index=False,float_format="%.17g",lineterminator="\n"))


def snapshot():
    result={}
    for name,worktree in [("publication",PUBLICATION),("1021",EXPLORATION)]:
        index=Path(git("rev-parse","--git-path","index",cwd=worktree))
        if not index.is_absolute():index=worktree/index
        files={}
        roots=[worktree/"results/figure_review",worktree/"results/figures",worktree/"results/stage7/2026-10-14"]
        if name=="1021":roots += [worktree/"results/diagnostics/1021"]
        for root in roots:
            if lp(root).is_dir():
                for p in lp(root).rglob("*"):
                    if p.is_file() and "__pycache__" not in p.parts:
                        clean=Path(str(p).removeprefix("\\\\?\\"))
                        files[clean.relative_to(worktree).as_posix()]=sha(p)
        for rel in git("ls-files",cwd=worktree).splitlines():
            if rel.lower().endswith((".docx",".doc")) and lp(worktree/rel).is_file():files[rel]=sha(worktree/rel)
        result[name]={"HEAD":git("rev-parse","HEAD",cwd=worktree),
                      "status":git("status","--porcelain=v1","--untracked-files=all",cwd=worktree),
                      "index_sha256":sha(index),"payloads":files}
    return result


def inputs():
    f=pd.read_csv(lp(HERE/"inputs/tract_features.csv"),dtype={"tract_id":str},float_precision="round_trip")
    status=pd.read_csv(lp(HERE/"inputs/full_domain_status.csv"),dtype={"tract_id":str},float_precision="round_trip")
    return f,status
