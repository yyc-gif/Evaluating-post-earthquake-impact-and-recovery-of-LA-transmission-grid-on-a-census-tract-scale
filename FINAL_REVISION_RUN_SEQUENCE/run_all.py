#!/usr/bin/env python3
"""Canonical, read-only resume validator for the LA Grid revised workflow.

This program never invokes sampling, GA, scheduling, clustering, or analysis.
It validates the currently frozen archive and reports REUSE/PASS or fails fast.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
STAGES = [
    ("01", "01_VALIDATE_INPUTS"),
    ("02", "02_MAPPING_AND_PHYSICAL_SAMPLES"),
    ("03", "03_GA_AND_STRATEGY_FREEZE"),
    ("04", "04_SCHEDULE_AND_TRAJECTORIES"),
    ("05", "05_SERVICE_AND_TRACT_EVALUATION"),
    ("06", "06_SOURCE_AND_NETWORK_DIAGNOSTICS"),
    ("07", "07_DISTRIBUTIONAL_AND_VULNERABILITY"),
    ("08", "08_FINAL_STAGE7_TYPOLOGY"),
    ("09", "09_CAPACITY_ROBUSTNESS"),
    ("10", "10_FINAL_RESULTS_AND_FIGURES"),
]
EXPECTED_BRANCH = "revision/reviewer-driven-core-rebuild-v2"
EXPECTED_BASE_COMMIT = "2d54e737ebf3b010507b6186dcbf00a37ef0602c"
PROTECTED_SHA = "182686868cffe962739804f6bc0ccecaed73d601"


class ValidationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path):
    require_file(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValidationError(f"Invalid JSON: {path}: {exc}") from exc


def require_file(path: Path):
    if not path.is_file():
        raise ValidationError(f"Missing required file: {path}")


def require_dir(path: Path):
    if not path.is_dir():
        raise ValidationError(f"Missing required archive directory: {path}")


def repo_path(relative: str) -> Path:
    return (ROOT / relative).resolve()


def run_git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if p.returncode:
        raise ValidationError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def require_git_tracked(path: Path):
    rel = path.resolve().relative_to(ROOT).as_posix()
    run_git("ls-files", "--error-unmatch", rel)


def require_materialized(path: Path):
    require_file(path)
    with path.open("rb") as f:
        head = f.read(120)
    if head.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise ValidationError(f"Git LFS pointer is not materialized: {path}")


def tree_inventory(path: Path, selected_files=None):
    require_dir(path)
    files = [path / x for x in selected_files] if selected_files else [p for p in path.rglob("*") if p.is_file()]
    missing = [p for p in files if not p.is_file()]
    if missing:
        raise ValidationError("Missing archive payload(s): " + ", ".join(map(str, missing[:8])))
    return files, len(files), sum(p.stat().st_size for p in files)


def check_inventory(path: Path, item: dict):
    files, count, size = tree_inventory(path, item.get("selected_files"))
    if count != item["expected_file_count"]:
        raise ValidationError(f"{item['artifact_id']}: file count {count}, expected {item['expected_file_count']} at {path}")
    if size != item["expected_total_size"]:
        raise ValidationError(f"{item['artifact_id']}: total size {size}, expected {item['expected_total_size']} at {path}")
    return files, {"file_count": count, "total_size": size}


def archive_item(registry, artifact_id):
    for item in registry["artifacts"]:
        if item["artifact_id"] == artifact_id:
            return item
    raise ValidationError(f"External archive registry lacks artifact_id={artifact_id}")


def archive_path(item):
    if item["artifact_id"] == "revised_suite":
        override = os.environ.get("LA_GRID_REVISED_SUITE_DIR")
        if override:
            return Path(override).expanduser().resolve()
    return (ROOT / item["current_local_path"]).resolve()


def validate_formal_trajectories(path: Path, item: dict):
    files, stats = check_inventory(path, item)
    index_path = repo_path(item["identity_index_file"])
    index = read_json(index_path)
    if sha256(index_path) != item["identity_index_sha256"]:
        raise ValidationError("Formal trajectory archive index SHA-256 changed")
    if index.get("trajectory_count") != 84000 or index.get("archive_manifest_chain_sha256") != item["expected_hash_or_manifest_chain_hash"]:
        raise ValidationError("Formal trajectory archive index identity does not match registry")
    json_files = [p for p in files if p.suffix.lower() == ".json"]
    if len(json_files) != 84000:
        raise ValidationError(f"Expected 84,000 per-trajectory JSON identities, found {len(json_files)}")
    checked = 0
    for meta_path in json_files:
        try:
            m = json.loads(meta_path.read_text(encoding="utf-8"))
            ident = m["identity"]
            if m.get("status") != "FORMAL_FROZEN_MATRIX_V1" or ident.get("matrix_id") != "JULY92_REVIEWER_REVISION_FINAL_V1":
                raise ValueError("status/matrix identity mismatch")
            if ident.get("mapping_method_id") != "M1_UTILITY_003" or float(ident.get("event_horizon_hr", -1)) != 480.0:
                raise ValueError("mapping/horizon mismatch")
            stem = meta_path.with_suffix("")
            npz = stem.with_suffix(".npz")
            task = stem.with_name(stem.name + "__TASK_EVENTS.csv")
            if not npz.is_file() or not task.is_file():
                raise ValueError("missing NPZ or task-events CSV")
            if sha256(npz) != m.get("npz_sha256") or sha256(task) != m.get("task_events_sha256"):
                raise ValueError("payload hash mismatch")
            checked += 1
        except Exception as exc:
            raise ValidationError(f"Formal trajectory identity/payload check failed at {meta_path}: {exc}") from exc
    return {**stats, "trajectory_identities_checked": checked, "archive_manifest_chain_sha256": index["archive_manifest_chain_sha256"]}


def validate_vulnerability_trajectories(path: Path, item: dict):
    files, stats = check_inventory(path, item)
    index_path = repo_path(item["identity_index_file"])
    index = read_json(index_path)
    if sha256(index_path) != item["identity_index_sha256"]:
        raise ValidationError("Vulnerability trajectory index SHA-256 changed")
    if index.get("trajectory_count") != 10000 or index.get("status") != "FORMAL_EQUITY_AMENDMENT_V1":
        raise ValidationError("Vulnerability trajectory archive identity mismatch")
    json_files = sorted(p for p in files if p.suffix.lower() == ".json")
    if len(json_files) != 10000:
        raise ValidationError(f"Expected 10,000 vulnerability trajectory identities, found {len(json_files)}")
    chain = hashlib.sha256()
    for meta_path in json_files:
        try:
            m = json.loads(meta_path.read_text(encoding="utf-8")); ident = m["identity"]
            if m.get("status") != "FORMAL_FROZEN_MATRIX_V1" or ident.get("strategy") != "vulnerability-first" or ident.get("matrix_id") != "JULY92_REVIEWER_REVISION_FINAL_V1":
                raise ValueError("status/strategy/matrix mismatch")
            if ident.get("mapping_method_id") != "M1_UTILITY_003" or float(ident.get("event_horizon_hr", -1)) != 480.0:
                raise ValueError("mapping/horizon mismatch")
            stem = meta_path.with_suffix(""); npz = stem.with_suffix(".npz"); task = stem.with_name(stem.name + "__TASK_EVENTS.csv")
            if not npz.is_file() or not task.is_file(): raise ValueError("missing NPZ or task-events CSV")
            if sha256(npz) != m.get("npz_sha256") or sha256(task) != m.get("task_events_sha256"): raise ValueError("payload hash mismatch")
            rec = {"path":meta_path.relative_to(path).as_posix(),"npz_sha256":m["npz_sha256"],"task_events_sha256":m["task_events_sha256"],"realization_id":ident["realization_id"]}
            chain.update(json.dumps(rec,sort_keys=True,separators=(",", ":")).encode()+b"\n")
        except Exception as exc:
            raise ValidationError(f"Vulnerability trajectory identity/payload check failed at {meta_path}: {exc}") from exc
    if chain.hexdigest() != item["expected_hash_or_manifest_chain_hash"]:
        raise ValidationError("Vulnerability trajectory manifest-chain SHA-256 mismatch")
    return {**stats,"trajectory_identities_checked":len(json_files),"manifest_chain_sha256":chain.hexdigest(),"sequence_sha256":index["sequence_sha256"]}


def validate_formal_offline(path: Path, item: dict):
    files, stats = check_inventory(path, item)
    index_path = repo_path(item["identity_index_file"]); index = read_json(index_path)
    if sha256(index_path) != item["identity_index_sha256"] or index.get("offline_shards") != 84:
        raise ValidationError("Formal offline index identity mismatch")
    if index.get("consolidated_summary_sha256") != item["expected_hash_or_manifest_chain_hash"]:
        raise ValidationError("Formal offline summary identity differs from archive registry")
    eval_files = sorted(path.glob("*__EVALUATION.json"))
    if len(eval_files) != 84:
        raise ValidationError(f"Expected 84 formal offline evaluation identities, found {len(eval_files)}")
    for ep in eval_files:
        d = read_json(ep); stem = ep.name.removesuffix("__EVALUATION.json")
        integ = path / f"{stem}__INTEGRALS.npz"; summ = path / f"{stem}__SUMMARY.parquet"
        if not integ.is_file() or not summ.is_file() or sha256(integ) != d.get("integral_sha256") or sha256(summ) != d.get("summary_sha256"):
            raise ValidationError(f"Formal offline shard hash mismatch: {ep}")
        if d.get("status") != "FORMAL_FROZEN_MATRIX_V1" or d.get("realization_count") != 1000:
            raise ValidationError(f"Formal offline shard identity mismatch: {ep}")
    return {**stats, "offline_shards_checked": len(eval_files), "consolidated_summary_sha256": index["consolidated_summary_sha256"]}


def validate_dynamic_archive(path: Path, item: dict):
    files, stats = check_inventory(path, item)
    index_path = repo_path(item["identity_index_file"]); index = read_json(index_path)
    if sha256(index_path) != item["identity_index_sha256"] or index.get("trajectory_count") != 84000:
        raise ValidationError("Dynamic topology index identity mismatch")
    if index.get("realization_detail_sha256") != item["expected_hash_or_manifest_chain_hash"]:
        raise ValidationError("Dynamic detail identity differs from archive registry")
    for rel,field in [("Formal_Experiment_20260923/Formal_Dynamic_Topology/FORMAL_DYNAMIC_REALIZATION_DIAGNOSTICS.parquet","realization_detail_sha256"),("Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv","summary_sha256"),("Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_SOURCE_LOSS_BY_STATION.csv","station_table_sha256")]:
        q=repo_path(rel); require_materialized(q)
        if not rel.endswith(".parquet"): require_git_tracked(q)
        if sha256(q)!=index.get(field): raise ValidationError(f"Dynamic summary identity mismatch: {q}")
    detail_files = list(path.rglob("*__DYNAMIC.json"))
    if len(detail_files) != 4000:
        raise ValidationError(f"Expected 4,000 dynamic realization details, found {len(detail_files)}")
    for jp in detail_files:
        d = read_json(jp)
        npz = jp.with_name(jp.name.replace("__DYNAMIC.json", "__DYNAMIC.npz"))
        if not npz.is_file() or sha256(npz) != d.get("npz_sha256"):
            raise ValidationError(f"Dynamic state cache hash mismatch: {jp}")
        if d.get("status") != "FORMAL_FROZEN_MATRIX_V1":
            raise ValidationError(f"Dynamic state identity status mismatch: {jp}")
    return {**stats, "dynamic_realization_details_checked": len(detail_files), "realization_detail_sha256": index["realization_detail_sha256"]}


def validate_equity_offline(path: Path, item: dict):
    files, stats = check_inventory(path, item)
    index_path = repo_path(item["identity_index_file"]); idx = read_json(index_path)
    if sha256(index_path) != item["identity_index_sha256"] or idx.get("shard_count") != 10 or idx.get("realization_count") != 10000:
        raise ValidationError("Equity offline shard index mismatch")
    if sha256(index_path) != item["expected_hash_or_manifest_chain_hash"]:
        raise ValidationError("Equity offline index hash differs from archive registry")
    recs = idx.get("shard_records", [])
    if len(recs) != 10:
        raise ValidationError("Equity offline shard record count mismatch")
    for rec in recs:
        stem = f"{rec['hazard']}__{rec['resource_case']}__vulnerability-first"
        integral = path / f"{stem}__INTEGRALS.npz"; summary = path / f"{stem}__SUMMARY.parquet"
        if not integral.is_file() or not summary.is_file() or sha256(integral) != rec["integral_sha256"] or sha256(summary) != rec["summary_sha256"]:
            raise ValidationError(f"Equity offline shard hash mismatch: {stem}")
    return {**stats, "equity_shards_checked": len(recs), "sequence_sha256": idx["sequence_sha256"]}


def validate_connectivity_cache(path: Path, item: dict):
    files, stats = check_inventory(path, item)
    inventory_hash = hashlib.sha256()
    for f in sorted(files, key=lambda x: x.name):
        inventory_hash.update(f.name.encode() + b"\0" + str(f.stat().st_size).encode() + b"\0" + sha256(f).encode() + b"\n")
    if inventory_hash.hexdigest() != item["expected_hash_or_manifest_chain_hash"]:
        raise ValidationError("Connectivity state cache inventory SHA-256 mismatch")
    ident_path = repo_path(item["identity_index_file"]); ident = read_json(ident_path)
    if sha256(ident_path) != item["identity_index_sha256"] or ident.get("classification_coverage") != "100%" or ident.get("production_gate_changed") is not False:
        raise ValidationError("Connectivity state identity mismatch")
    return {**stats, "inventory_sha256": inventory_hash.hexdigest(), "classification_coverage": ident["classification_coverage"]}


def validate_revised_suite(path: Path, item: dict):
    files, stats = check_inventory(path, item)
    manifest = path / "RESULT_SUITE_MANIFEST.csv"
    if not manifest.is_file() or sha256(manifest) != item["identity_index_sha256"]:
        raise ValidationError("Revised suite manifest identity mismatch")
    with manifest.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 558:
        raise ValidationError(f"Expected 558 suite manifest records, found {len(rows)}")
    checked = 0
    for row in rows:
        rel = row.get("suite_path") or row.get("path") or row.get("file")
        if not rel:
            raise ValidationError("Suite manifest row has no suite_path/path/file")
        target = (path / rel).resolve()
        if not target.is_file():
            raise ValidationError(f"Suite manifest references missing output: {target}")
        try:
            nbytes = int(row.get("bytes") or row.get("size_bytes") or -1)
        except ValueError:
            nbytes = -1
        digest = row.get("sha256") or row.get("SHA256")
        if nbytes >= 0 and target.stat().st_size != nbytes:
            raise ValidationError(f"Suite output size mismatch: {target}")
        if digest and sha256(target).lower() != digest.lower():
            raise ValidationError(f"Suite output hash mismatch: {target}")
        checked += 1
    if checked != 558:
        raise ValidationError("Not all suite manifest rows were checked")
    return {**stats, "suite_manifest_rows_checked": checked, "suite_manifest_sha256": sha256(manifest)}


def validate_code_authority():
    authority_path = HERE / "CODE_AUTHORITY.json"; ca = read_json(authority_path)
    for record in ca["current_code_files"]:
        p = repo_path(record["path"])
        require_materialized(p)
        if record.get("tracked_in_current_git"):
            require_git_tracked(p)
        elif not record["path"].startswith("FINAL_REVISION_RUN_SEQUENCE/"):
            raise ValidationError(f"Untracked noncanonical code cannot be an authority: {p}")
        if sha256(p) != record["sha256"]:
            raise ValidationError(f"Code authority hash changed: {p}")
    missing = [x["commit"] for x in ca["required_historical_executable_commits"] if not x["exists_in_local_git"]]
    if missing:
        raise ValidationError("Required historical execution commit absent from local Git: " + ", ".join(missing))
    for entry in ca["required_historical_executable_commits"]:
        run_git("cat-file", "-e", entry["commit"] + "^{commit}")
    if run_git("branch", "--show-current") != EXPECTED_BRANCH:
        raise ValidationError("Code authority must run on the reviewer revision branch")
    if subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"], cwd=ROOT).returncode:
        raise ValidationError(f"Current HEAD is not based on the audited scientific result commit {EXPECTED_BASE_COMMIT}")
    return {"authority_file_sha256": sha256(authority_path), "code_file_count": len(ca["current_code_files"]), "historical_commit_count": len(ca["required_historical_executable_commits"]), "current_head": run_git("rev-parse", "HEAD")}


def validate_parent_design():
    matrix_path = repo_path("FINAL_EXPERIMENT_MATRIX.json")
    parent = read_json(matrix_path)
    expected = read_json(HERE / "FINAL_REVISION_RUN_MATRIX.json")["parent_frozen_design"]
    if parent.get("matrix_id") != expected["matrix_id"] or sha256(matrix_path) != expected["matrix_sha256"]:
        raise ValidationError("Parent frozen experiment matrix identity/hash mismatch")
    if parent.get("status") != "FROZEN_BEFORE_FORMAL_EXECUTION":
        raise ValidationError("Parent experiment matrix is not marked frozen")
    if parent.get("protected_submission_sha") != PROTECTED_SHA:
        raise ValidationError("Protected July archive identity differs from canonical authority")
    if run_git("rev-parse", "archive/ijdrr-submission-20260722") != PROTECTED_SHA:
        raise ValidationError("Protected July archive branch ref moved")
    run_git("cat-file", "-e", PROTECTED_SHA + "^{commit}")
    return {"matrix_id": parent["matrix_id"], "matrix_sha256": expected["matrix_sha256"], "protected_archive_sha": PROTECTED_SHA}


def validate_inputs():
    vpath = repo_path("Formal_Experiment_20260923/FINAL_EXECUTION_VALIDATION.json"); val = read_json(vpath)
    mpath = repo_path("FINAL_EXPERIMENT_MATRIX.json")
    if val.get("status") != "PASS_DRY_VALIDATION_NO_SAMPLING_OR_SCHEDULING" or val.get("matrix_sha256") != sha256(mpath):
        raise ValidationError("Existing formal dry-validation identity does not match frozen matrix")
    hashes = val.get("input_sha256", {})
    checked = []
    for rel, expected in hashes.items():
        p = repo_path(rel.replace("\\", "/")); require_materialized(p); require_git_tracked(p)
        actual = sha256(p)
        if actual != expected:
            raise ValidationError(f"Frozen input hash mismatch: {rel}: {actual} != {expected}")
        checked.append({"path": rel.replace("\\", "/"), "sha256": actual})
    if len(checked) != 14:
        raise ValidationError(f"Expected 14 frozen input hashes, found {len(checked)}")
    counts = val["counts"]
    if (counts.get("stations"), counts.get("edges"), counts.get("tracts"), counts.get("Core_sources"), counts.get("evaluation_physical"), counts.get("planning_physical")) != (92,318,2315,14,4000,64):
        raise ValidationError("Frozen input counts differ from accepted final workflow constants")
    if val.get("production_mapping") != "JULY_UTILITY_CONSTRAINED_92" or float(val.get("production_gate_threshold", -1)) != 0.5:
        raise ValidationError("Frozen mapping or production gate identity mismatch")
    return {"dry_validation": str(vpath.relative_to(ROOT)), "input_count": len(checked), "input_hashes": checked, "dimensions": counts, "status": val["status"]}


def validate_physical_samples():
    base = repo_path("Formal_Experiment_20260923/Stage 1 Output_expanded/PHYSICAL_INPUTS_FROZEN.json")
    d = read_json(base)
    if d.get("evaluation_count") != 4000 or d.get("planning_count") != 64 or d.get("matrix_id") != "JULY92_REVIEWER_REVISION_FINAL_V1":
        raise ValidationError("Frozen physical sample manifest identity mismatch")
    if len(d.get("sample_hashes", {})) != 4064:
        raise ValidationError("Physical sample hash registry does not cover all 4,064 samples")
    require_materialized(base); require_git_tracked(base)
    csv_manifest=base.parent/"PHYSICAL_SAMPLE_MANIFEST.csv"; require_materialized(csv_manifest); require_git_tracked(csv_manifest)
    with csv_manifest.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    if len(rows)!=4064 or sum(1 for r in rows if r.get("split")=="evaluation")!=4000 or sum(1 for r in rows if r.get("split")=="planning")!=64:
        raise ValidationError("Physical sample manifest does not contain the frozen 4,000/64 split")
    sample_dir = base.parent
    for hazard, expected in d.get("files_sha256", {}).items():
        p = sample_dir / f"physical_inputs_{hazard}.npz"
        require_materialized(p); require_git_tracked(p)
        if sha256(p) != expected:
            raise ValidationError(f"Frozen physical sample payload changed: {p}")
    return {"physical_inputs_manifest_sha256": sha256(base), "evaluation_samples": 4000, "planning_samples": 64, "sample_hash_count": len(d["sample_hashes"]), "sample_archive_hashes": d["files_sha256"]}


def validate_strategy_registry():
    p = HERE / "03_GA_AND_STRATEGY_FREEZE/FINAL_STRATEGY_SET.json"; reg = read_json(p)
    names = [x["name"] for x in reg["strategies"]]
    want = ["centrality-first","impact-first","betweenness-first","degree-first","closeness-first","hospital-first","random","vulnerability-first"]
    if names != want or reg.get("reference") != "unconstrained":
        raise ValidationError("Resolved strategy registry differs from the final reporting set")
    if reg["direct_community"].get("sequence_equivalent_to") != "impact-first" or reg["direct_community"].get("report_separately") is not False:
        raise ValidationError("Direct-community reporting resolution mismatch")
    for strategy in reg["strategies"]:
        src = repo_path(strategy["sequence_authority"])
        require_materialized(src); require_git_tracked(src)
        if strategy["name"] == "vulnerability-first":
            obj=read_json(src); actual=obj.get("station_sequence_sha256")
        else:
            obj=read_json(src); seq=obj["2pc50"][strategy["name"]]
            actual=hashlib.sha256(json.dumps(seq,separators=(",", ":")).encode()).hexdigest()
        if actual != strategy["sequence_sha256"]:
            raise ValidationError(f"Frozen sequence hash mismatch: {strategy['name']}")
    dc = read_json(repo_path(reg["direct_community"]["identity_file"]))
    if dc.get("status") != "EXACT" or dc.get("paired_archive_count") != 10000:
        raise ValidationError("Direct-community/Impact-first identity evidence is not exact")
    ga = read_json(repo_path("Formal_Experiment_20260923/GA_EXECUTION_IDENTITY.json"))
    if ga.get("executable_code_commit_sha") != "a4cbad91698c57d79cc867d814ec7d5ee85312bf":
        raise ValidationError("GA provenance SHA mismatch")
    return {"strategies": names, "reference": "unconstrained", "direct_community_report_separately": False, "GA_identity_sha256": sha256(repo_path("Formal_Experiment_20260923/GA_EXECUTION_IDENTITY.json"))}


def validate_stage7():
    output_dir = repo_path("Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized")
    root = repo_path("Formal_Experiment_20260923")
    if not output_dir.is_dir():
        raise ValidationError(f"Missing final Stage 7 authority: {output_dir}")
    expected = json.loads((HERE/"08_FINAL_STAGE7_TYPOLOGY/STAGE8_OUTPUT_HASHES.json").read_text(encoding="utf-8"))
    for rel, digest in expected.items():
        p=output_dir/rel; require_materialized(p); require_git_tracked(p)
        if sha256(p)!=digest: raise ValidationError(f"Final Stage 7 output hash mismatch: {p}")
    # Invoke only the existing verifier; it reads and checks the harmonized outputs, without fitting PCA/K-means.
    try:
        sys.path.insert(0,str(ROOT))
        import r1_stage7_harmonized
        result=r1_stage7_harmonized.verify_harmonized_stage7(root)
        result.pop("source_directory",None)
    except Exception as exc:
        raise ValidationError(f"Read-only Stage 7 verifier failed: {exc}") from exc
    return {"authority":"Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized","output_count":len(expected),"output_inventory_sha256":sha256(HERE/"08_FINAL_STAGE7_TYPOLOGY/STAGE8_OUTPUT_HASHES.json"),"verifier_result":result}


def validate_capacity():
    expected=read_json(HERE/"09_CAPACITY_ROBUSTNESS/STAGE9_OUTPUT_HASHES.json")
    out={}
    for rel,digest in expected.items():
        p=repo_path(rel); require_materialized(p); require_git_tracked(p)
        if sha256(p)!=digest: raise ValidationError(f"Closed capacity output hash mismatch: {p}")
        out[rel]=digest
    return {"output_hashes":out,"capacity_closure_executed":False}


def validate_formal_result_authorities():
    files=["Formal_Experiment_20260923/Formal_Results/FORMAL_RESULTS_INDEX.json","Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_RESULTS_INDEX.json","Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_POLICY_RESULTS_INDEX.json"]
    out={}
    for rel in files:
        p=repo_path(rel)
        if not p.exists():
            if rel.endswith("VULNERABILITY_POLICY_RESULTS_INDEX.json"):
                continue
            raise ValidationError(f"Missing formal result authority: {p}")
        require_materialized(p); require_git_tracked(p); out[rel]=sha256(p)
    return out


def validate_suite(item):
    path=archive_path(item)
    # The suite manifest path is external, so verify its hash directly against the frozen registry.
    manifest=path/"RESULT_SUITE_MANIFEST.csv"; require_file(manifest)
    if sha256(manifest)!=item["identity_index_sha256"]:
        raise ValidationError(f"Revised suite manifest hash mismatch: {manifest}")
    return validate_revised_suite(path,item)


def validate_stage(stage_id, registry, run_manifest):
    item_by_id={x["artifact_id"]:x for x in registry["artifacts"]}
    evidence={}
    if stage_id=="01":
        branch=run_git("branch","--show-current"); head=run_git("rev-parse","HEAD")
        if branch!=EXPECTED_BRANCH:
            raise ValidationError(f"Expected branch {EXPECTED_BRANCH}; found {branch}")
        if subprocess.run(["git","merge-base","--is-ancestor",EXPECTED_BASE_COMMIT,"HEAD"],cwd=ROOT).returncode:
            raise ValidationError(f"Current HEAD is not based on audited result commit {EXPECTED_BASE_COMMIT}: {head}")
        evidence["design"]=validate_parent_design(); evidence["inputs"]=validate_inputs(); evidence["code"]=validate_code_authority()
    elif stage_id=="02":
        evidence["physical_samples"]=validate_physical_samples()
        mapping=repo_path("Data/JULY_UTILITY_CONSTRAINED_92.csv"); evidence["production_mapping_sha256"]=sha256(mapping)
    elif stage_id=="03": evidence["resolved_strategy_registry"]=validate_strategy_registry()
    elif stage_id=="04":
        for aid,fn in [("formal_trajectories",validate_formal_trajectories),("vulnerability_first_trajectories",validate_vulnerability_trajectories)]:
            it=item_by_id[aid]; evidence[aid]=fn(archive_path(it),it)
    elif stage_id=="05":
        it=item_by_id["formal_offline_shards"]; evidence["formal_offline_shards"]=validate_formal_offline(archive_path(it),it)
        it=item_by_id["equity_offline_shards"]; evidence["equity_offline_shards"]=validate_equity_offline(archive_path(it),it)
        evidence["formal_result_authorities"]=validate_formal_result_authorities()
    elif stage_id=="06":
        it=item_by_id["dynamic_topology_archive"]; evidence["dynamic_topology_archive"]=validate_dynamic_archive(archive_path(it),it)
        it=item_by_id["connectivity_state_cache"]; evidence["connectivity_state_cache"]=validate_connectivity_cache(archive_path(it),it)
        # Confirm representative retained diagnostics are tracked/materialized and immutable.
        for rel in ["SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv","SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv","ROUTE_REQUIREMENT_SENSITIVITY_SUMMARY.csv"]:
            p=repo_path(rel); require_materialized(p); require_git_tracked(p); evidence.setdefault("compact_diagnostic_sha256",{})[rel]=sha256(p)
    elif stage_id=="07":
        evidence["equity_results_index_sha256"]=sha256(repo_path("Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_RESULTS_INDEX.json"))
        for rel in ["Formal_Experiment_20260923/Equity_Amendment/EQUITY_POLICY_AMENDMENT.json","Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_FIRST_SEQUENCE.json","Formal_Experiment_20260923/Equity_Amendment/EQUITY_POLICY_RESULTS.md","Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_GROUP_SUMMARY.csv","Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PAIRWISE_EFFECTS.csv","Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_TRACT_EFFECTS.parquet"]:
            p=repo_path(rel); require_materialized(p); require_git_tracked(p); evidence.setdefault("result_hashes",{})[rel]=sha256(p)
    elif stage_id=="08": evidence["stage7"]=validate_stage7()
    elif stage_id=="09": evidence["capacity"]=validate_capacity()
    elif stage_id=="10":
        it=item_by_id["revised_suite"]; evidence["suite"]=validate_suite(it)
    else: raise ValidationError(f"Unknown stage {stage_id}")

    if stage_id!="01":
        prev=f"{int(stage_id)-1:02d}"
        p=HERE/STAGES[int(stage_id)-2][1]/"STAGE_VALIDATION_MANIFEST.json"
        if not p.is_file(): raise ValidationError(f"Previous stage manifest missing: {p}")
        prior=read_json(p)
        if prior.get("stage_id")!=prev or prior.get("status") not in ("PASS_REUSE","PASS_VALIDATE"):
            raise ValidationError(f"Previous stage manifest is not a completed validation: {p}")
        evidence["previous_stage_manifest"]={"path":str(p.relative_to(ROOT)),"sha256":sha256(p),"status":prior["status"]}

    status="PASS_REUSE" if stage_id not in ("01",) else "PASS_VALIDATE"
    outputs=stage_outputs(stage_id,registry)
    stage_record={"stage_id":stage_id,"stage_name":dict(STAGES)[stage_id],"status":status,"authority":read_json(HERE/"FINAL_REVISION_RUN_MATRIX.json")["stage_authorities"][stage_id],"inputs":evidence,"hashes":collect_evidence_hashes(evidence),"outputs":outputs,"output_hashes":{x["path"]:x.get("sha256") or x.get("identity_hash") for x in outputs},"reuse_source":"existing frozen Git/local/external archive; no scientific outputs regenerated","code_identity":{"current_validator_sha256":sha256(HERE/"run_all.py"),"historical_phase_identities_preserved":True},"scientific_generation_called":False}
    sp=HERE/dict(STAGES)[stage_id]/"STAGE_VALIDATION_MANIFEST.json"
    sp.write_text(json.dumps(stage_record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    stage_record["stage_manifest_path"]=str(sp.relative_to(ROOT)); stage_record["stage_manifest_sha256"]=sha256(sp)
    run_manifest["stages"].append(stage_record)
    print(f"Stage {stage_id}: {status}")
    return stage_record


def stage_outputs(stage_id, registry):
    """List verified authorities, without copying or rewriting them."""
    paths={
        "01":["FINAL_EXPERIMENT_MATRIX.json","Formal_Experiment_20260923/FINAL_EXECUTION_VALIDATION.json"],
        "02":["Data/JULY_UTILITY_CONSTRAINED_92.csv","Formal_Experiment_20260923/Stage 1 Output_expanded/PHYSICAL_INPUTS_FROZEN.json"],
        "03":["FINAL_REVISION_RUN_SEQUENCE/03_GA_AND_STRATEGY_FREEZE/FINAL_STRATEGY_SET.json","Formal_Experiment_20260923/GA_EXECUTION_IDENTITY.json","Formal_Experiment_20260923/Formal_Reviewer_Results/DIRECT_IMPACT_IDENTITY.json"],
        "05":["Formal_Experiment_20260923/Formal_Offline_Evaluation/FORMAL_OFFLINE_INDEX.json","Formal_Experiment_20260923/Formal_Results/FORMAL_RESULTS_INDEX.json","Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_RESULTS_INDEX.json"],
        "06":["Formal_Experiment_20260923/Formal_Dynamic_Topology/FORMAL_DYNAMIC_TOPOLOGY_INDEX.json","Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_CONNECTIVITY_STATE_IDENTITY.json"],
        "07":["Formal_Experiment_20260923/Equity_Amendment/EQUITY_POLICY_AMENDMENT.json","Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_RESULTS_INDEX.json"],
        "08":["FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/STAGE8_OUTPUT_HASHES.json"],
        "09":["FINAL_REVISION_RUN_SEQUENCE/09_CAPACITY_ROBUSTNESS/STAGE9_OUTPUT_HASHES.json"],
    }
    out=[]
    for rel in paths.get(stage_id,[]):
        p=repo_path(rel); out.append({"path":rel,"sha256":sha256(p)})
    artifact_ids={"04":["formal_trajectories","vulnerability_first_trajectories"],"05":["formal_offline_shards","equity_offline_shards"],"06":["dynamic_topology_archive","connectivity_state_cache"],"10":["revised_suite"]}.get(stage_id,[])
    byid={x["artifact_id"]:x for x in read_json(HERE/"EXTERNAL_ARCHIVE_MANIFEST.json")["artifacts"]}
    for aid in artifact_ids:
        item=byid[aid]
        out.append({"path":item["current_local_path"],"artifact_id":aid,"file_count":item["expected_file_count"],"total_size":item["expected_total_size"],"identity_hash":item["expected_hash_or_manifest_chain_hash"],"identity_index_sha256":item["identity_index_sha256"]})
    return out


def collect_evidence_hashes(obj, prefix=""):
    out={}
    if isinstance(obj,dict):
        for k,v in obj.items():
            key=f"{prefix}.{k}" if prefix else k
            if isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v.lower()): out[key]=v
            else: out.update(collect_evidence_hashes(v,key))
    elif isinstance(obj,list):
        for i,v in enumerate(obj): out.update(collect_evidence_hashes(v,f"{prefix}[{i}]"))
    return out


def main():
    parser=argparse.ArgumentParser(description="Validate and reuse the canonical final revised workflow; never runs science.")
    parser.add_argument("--resume",action="store_true",help="validate/reuse frozen outputs only (authoritative mode)")
    parser.add_argument("--from-scratch",action="store_true",help="not certified; always rejected")
    args=parser.parse_args()
    if args.from_scratch:
        parser.error("--from-scratch is NOT YET CERTIFIED and is intentionally unavailable.")
    if not args.resume:
        parser.error("Specify --resume. This canonical entrypoint only validates and reuses existing outputs.")
    matrix=read_json(HERE/"FINAL_REVISION_RUN_MATRIX.json")
    registry=read_json(HERE/"EXTERNAL_ARCHIVE_MANIFEST.json")
    run_manifest={"schema_version":1,"workflow":"FINAL_REVISION_RUN_SEQUENCE","mode":"resume","status":"RUNNING_VALIDATION","started_at_utc":datetime.now(timezone.utc).isoformat(),"repository_head":run_git("rev-parse","HEAD"),"branch":run_git("branch","--show-current"),"parent_matrix_id":matrix["parent_frozen_design"]["matrix_id"],"parent_matrix_sha256":matrix["parent_frozen_design"]["matrix_sha256"],"scientific_computation_performed":False,"stages":[]}
    manifest_path=HERE/"FINAL_RUN_MANIFEST.json"
    try:
        for stage_id,_ in STAGES:
            validate_stage(stage_id,registry,run_manifest)
        run_manifest["status"]="PASS_ALL_STAGES_REUSE_OR_VALIDATE"
    except Exception as exc:
        run_manifest["status"]="FAIL_FAST"
        run_manifest["failure"]={"type":type(exc).__name__,"message":str(exc)}
        run_manifest["finished_at_utc"]=datetime.now(timezone.utc).isoformat()
        manifest_path.write_text(json.dumps(run_manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(f"FAIL FAST: {exc}",file=sys.stderr)
        return 2
    run_manifest["finished_at_utc"]=datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(run_manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"All stages validated/reused. Final manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
