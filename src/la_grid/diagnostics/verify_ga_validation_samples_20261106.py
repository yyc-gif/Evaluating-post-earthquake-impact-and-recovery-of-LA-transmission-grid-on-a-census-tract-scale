"""Verify the frozen 2,000-sample GA validation capsule identities.

The script checks every archived draw record and overlap with the original
64 planning plus 1,000 evaluation draws. It independently regenerates four
predeclared sample indices with the frozen production samplers; it does not
execute a restoration schedule or create a replacement validation cohort.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

import numpy as np


ARCHIVE_SHA256 = "74d83734549c83b7bcb57270a07db3ab4c696d4384c5a851461184cfcb28947d"
FREEZE_SHA256 = "45d157c0a3b9460d7c29e389b649afef0f0e6bc568bfba8eb773f9b5b974ae15"
PHYSICAL_INPUTS_SHA256 = "fa40cc26567c22e7d8195e04949e2ef7dbc960a9751f4b9af3d687edf542cdcb"
CORE_SOURCE_SHA256 = "f1f70952ae2c7cc0767543a32fdc20a8ad1c7d58c76f576e980ca23d00f2facd"
R1_SOURCE_SHA256 = "c1a439dd054271f5b0c5a398c29c890db2750601db7f327dcd9bb880a69b8c22"
SEED_PREFIX = [202610091, 3, 2]
REGENERATE_INDICES = [0, 1, 1000, 1999]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def physical_hash(ids, damage, duration) -> str:
    return sha256_bytes(
        ("\n".join(map(str, ids)) + "\n").encode("utf-8")
        + np.asarray(damage, dtype="<i8").tobytes()
        + np.asarray(duration, dtype="<f8").tobytes()
    )


def _long_path(path: Path) -> str:
    value = str(path.resolve())
    if os.name == "nt" and len(value) >= 240 and not value.startswith("\\\\?\\"):
        return "\\\\?\\" + value
    return value


def _load_production_sampler(repo_root: Path):
    sys.path.insert(0, str(repo_root / "src"))
    from la_grid.core import C257H_Project_Main as core
    from la_grid.core.legacy_entrypoints.C257H_Project_Main_expanded import ExpandedConfig

    core_file = repo_root / "src/la_grid/core/C257H_Project_Main.py"
    r1_file = repo_root / "src/la_grid/revision/r1_realization_scheduling.py"
    if sha256_file(core_file) != CORE_SOURCE_SHA256 or sha256_file(r1_file) != R1_SOURCE_SHA256:
        raise ValueError("Production sampling source hash differs from the frozen validation receipt")

    cfg = ExpandedConfig()
    devices = core.load_devices(cfg.DEVICES_CSV)
    pga = core.load_pga(cfg.PGA_CSV, cfg.SCENARIOS)
    for frame in (devices, pga):
        frame["id"] = frame["id"].map(core.clean_substation_id)
        if frame.id.duplicated().any():
            raise ValueError("Frozen station input contains duplicate station IDs")
    data = devices.merge(pga, on="id", how="left", validate="one_to_one").set_index("id")
    return core, cfg, data


def verify(archive: Path, repo_root: Path, output: Path) -> dict:
    if sha256_file(archive) != ARCHIVE_SHA256:
        raise ValueError("Validation archive SHA-256 differs from its registered identity")
    physical_path = repo_root / "Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_2pc50.npz"
    if sha256_file(physical_path) != PHYSICAL_INPUTS_SHA256:
        raise ValueError("Frozen 2pc50 physical input archive SHA-256 mismatch")

    core, cfg, device_data = _load_production_sampler(repo_root)
    regenerated = []
    archived_hashes = set()
    seed_checks = 0
    with np.load(_long_path(physical_path), allow_pickle=False) as original:
        station_ids = original["station_ids"].astype(str).tolist()
        pga_series = device_data.loc[station_ids, "pga_2pc50"]
        devices = device_data.loc[station_ids]

        original_hashes = set()
        for split in ("planning", "evaluation"):
            ds_matrix = original[f"{split}_ds"].T
            duration_matrix = original[f"{split}_duration"].T
            for ds, duration in zip(ds_matrix, duration_matrix):
                original_hashes.add(physical_hash(station_ids, ds, duration))

        with zipfile.ZipFile(archive, "r") as bundle:
            for index in range(2000):
                name = f"physical/{index:04d}/DRAW.json"
                record = json.loads(bundle.read(name))
                payload_sha = record.pop("payload_sha256")
                if sha256_bytes(json.dumps(record, sort_keys=True).encode("utf-8")) != payload_sha:
                    raise ValueError(f"Draw-record payload digest mismatch at r={index}")
                draw_ids = list(map(str, record["station_ids"]))
                damage = np.asarray(record["damage_state"], dtype=np.int64)
                duration = np.asarray(record["duration_hr"], dtype=np.float64)
                expected_seed = SEED_PREFIX + [index]
                if (record.get("r") != index or record.get("entropy") != expected_seed
                        or record.get("freeze_sha256") != FREEZE_SHA256):
                    raise ValueError(f"Seed/freeze identity mismatch at r={index}")
                if draw_ids != station_ids:
                    raise ValueError(f"Ordered station IDs mismatch at r={index}")
                if sha256_bytes(damage.astype("<i8").tobytes()) != record["damage_sha256"]:
                    raise ValueError(f"Damage array digest mismatch at r={index}")
                if sha256_bytes(duration.astype("<f8").tobytes()) != record["duration_sha256"]:
                    raise ValueError(f"Duration array digest mismatch at r={index}")
                digest = physical_hash(draw_ids, damage, duration)
                if digest != record["physical_sha256"] or digest in archived_hashes:
                    raise ValueError(f"Physical identity mismatch/duplicate at r={index}")
                archived_hashes.add(digest)
                seed_checks += 1
                if digest in original_hashes:
                    raise ValueError(f"Independent validation draw overlaps original cohort at r={index}")

                if index in REGENERATE_INDICES:
                    rng = np.random.default_rng(np.random.SeedSequence(expected_seed))
                    generated_ds = core.sample_damage_states(pga_series, devices, 1, rng)
                    _, generated_duration = core.damage_to_functionality_and_repair(
                        generated_ds, rng, cfg
                    )
                    generated_ds = np.asarray(generated_ds[:, 0], dtype=np.int64)
                    generated_duration = np.asarray(generated_duration[:, 0], dtype=np.float64)
                    if not (np.array_equal(generated_ds, damage)
                            and np.array_equal(generated_duration, duration)):
                        raise ValueError(f"Production sampler did not reproduce archived draw r={index}")
                    regenerated.append({
                        "r": index,
                        "seed_entropy": expected_seed,
                        "physical_sha256": digest,
                        "damage_duration_bitwise_match": True,
                    })

    if seed_checks != 2000 or len(archived_hashes) != 2000:
        raise ValueError("The archive did not contain 2,000 unique registered physical identities")
    if len(original_hashes) != 1064:
        raise ValueError(f"Expected 64 planning + 1,000 evaluation identities; found {len(original_hashes)}")
    result = {
        "status": "PASS",
        "validation_archive_sha256": ARCHIVE_SHA256,
        "freeze_sha256": FREEZE_SHA256,
        "seed_protocol": "numpy.default_rng(numpy.random.SeedSequence([202610091,3,2,r]))",
        "archived_sample_seed_records_verified": seed_checks,
        "unique_validation_physical_hashes": len(archived_hashes),
        "original_planning_and_evaluation_hashes": len(original_hashes),
        "overlap_with_original_physical_hashes": 0,
        "independently_regenerated_indices": regenerated,
        "sampler_sources": {
            "src/la_grid/core/C257H_Project_Main.py": CORE_SOURCE_SHA256,
            "src/la_grid/revision/r1_realization_scheduling.py": R1_SOURCE_SHA256,
            "Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_2pc50.npz": PHYSICAL_INPUTS_SHA256,
        },
        "interpretation": "Four prespecified draws were regenerated only to verify archive identity; no schedules or service trajectories were rerun.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(_long_path(output), "w", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.archive, args.repo_root, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
