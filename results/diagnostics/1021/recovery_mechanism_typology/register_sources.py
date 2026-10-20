"""Verify actual frozen source bytes without extracting new responses or fitting."""
import json
import platform
from support import *


def main():
    assert git("symbolic-ref", "HEAD").decode().strip() == "refs/heads/1021"
    assert git("rev-parse", "HEAD").decode().strip() == START
    original_status = git("status", "--porcelain=v1", "--untracked-files=all").decode()
    original_index = Path(git("rev-parse", "--git-path", "index").decode().strip())
    if not original_index.is_absolute():
        original_index = ROOT/original_index
    preserved = {}
    for p in PARENT.rglob("*"):
        if p.is_file() and HERE not in p.parents and "__pycache__" not in p.parts:
            preserved[p.relative_to(PARENT).as_posix()] = sha(p)
    old = json.loads((PRIOR/"PACKAGE_HASHES.json").read_text())
    assert all(sha(PRIOR/k) == v for k,v in old.items())
    rows = []
    src = pd.read_csv(PRIOR/"SOURCE_HASHES.csv")
    for row in src.itertuples():
        p = Path(row.path)
        actual = sha(p) if p.is_absolute() else legacy.hashlib.sha256(payload(row.path)).hexdigest()
        assert actual == row.sha256, row.path
        rows.append({"path":row.path,"sha256":actual,"role":row.role})
    events = pd.read_csv(PRIOR/"EVENT_SOURCE_HASHES_AND_IDENTITIES.csv")
    for row in events.itertuples():
        p = Path(row.event_path)
        assert sha(p) == row.event_npz_sha256
        assert sha(p.with_suffix(".json")) == row.event_manifest_sha256
    protected = json.loads(payload("docs/reproducibility/author_suite_final_layout_20261012/PRESERVATION_BEFORE.json"))["protected_files"]
    assert len(protected) == 950
    assert all(sha(ARCHIVE/k) == v for k,v in protected.items())
    save("FROZEN_SOURCE_HASHES.csv",rows)
    dump("FROZEN_INPUT_REGISTRY.json",{
        "branch":"refs/heads/1021","starting_commit":START,"python":platform.python_version(),
        "original_status_including_new_untracked_protocol":original_status,
        "original_index_sha256":sha(original_index),"publication_snapshot":snapshot(),
        "preserved_prior_payloads":preserved,"protected_950":protected,
        "external_archive_root":str(ARCHIVE),"verified_event_payloads":len(events),
        "prior_event_registry_sha256":sha(PRIOR/"EVENT_SOURCE_HASHES_AND_IDENTITIES.csv"),
        "protocol_sha256":sha(HERE/"PROTOCOL.md"),"new_features_or_fits_examined":False,
        "clean_clone_limitation":"Actual raw events and integral shards require the manifest-bound local archive; compact derived data will be delivered."})
    print("Verified",len(rows),"sources,",len(events),"events, 950 protected files; no new fits.")


if __name__ == "__main__":
    main()
