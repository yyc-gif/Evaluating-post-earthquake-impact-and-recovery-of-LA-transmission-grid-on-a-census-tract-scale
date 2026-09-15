from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal


HERE = Path(__file__).parent
ROOT = HERE.parents[2]
REVIEW = ROOT / "Review_and_Revision" / "IJDRR-D-26-02276"
ROUND10 = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914"
ROUND11 = REVIEW / "11_TwoLayer_Static_QA_20260914"
ROUND13 = REVIEW / "13_TimeIndexed_Interface_QA_20260914"
ROUND14 = REVIEW / "14_Production_Interface_Contract_20260914"
ROUND15 = REVIEW / "15_R1_Upstream_Adapter_20260914"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROUND14))
sys.path.insert(0, str(ROUND15))

from r1_effective_state_adapter import (  # noqa: E402
    adapt_native_r1_effective_state_envelope,
)
from r1_effective_state_exporter import (  # noqa: E402
    EFFECTIVE_STATE_SEMANTICS,
    R1EffectiveStateExportError,
    SCHEMA_VERSION,
    export_r1_effective_state_trajectory,
    hash_frozen_r1_ids,
)
from service_layer_interface import (  # noqa: E402
    load_validate_r1_effective_state_trajectory,
)


PATHS = {
    "main": ROOT / "C257H_Project_Main.py",
    "round11": ROUND11 / "SERVICE_NODE_BASELINE_QA.csv",
    "round13": ROUND13 / "EXTERNAL_R1_EFFECTIVE_STATE_TRAJECTORY.csv",
    "round15_native": ROUND15 / "GOLDEN_NATIVE_SCHEMA_FIXTURE.csv",
    "round15_adapter": ROUND15 / "r1_effective_state_adapter.py",
    "production": ROUND14 / "service_layer_interface.py",
    "collision": HERE / "ZERO_MISSING_COLLISION_FIXTURE.csv",
    "exporter": HERE / "r1_effective_state_exporter.py",
}

EXPECTED_HASHES = {
    "main": "49b22de669239a17c000d9f92c5c340078315c0e07e085f803e964c40fbe1f38",
    "round11": "a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384",
    "round13": "b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6",
    "round15_native": "b52605805f02cf12a959df50bee2fa7a34f5f1d6e8333015a79d74b4a2965249",
    "round15_adapter": "7815704771fbe61b18f057a7ee49d061edd13aee1f85daa37c83781fa21a1f9f",
    "production": "d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514",
}


def safe(path: Path) -> str:
    value = str(path.resolve())
    return value if value.startswith("\\\\?\\") else "\\\\?\\" + value


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(safe(path), keep_default_na=False, **kwargs)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(safe(path), "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


class DynamicExportContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hashes_before = {name: sha256(path) for name, path in PATHS.items()}
        for name, expected in EXPECTED_HASHES.items():
            if cls.hashes_before[name] != expected:
                raise AssertionError(
                    f"Frozen hash mismatch for {name}: {cls.hashes_before[name]} != {expected}"
                )

        cls.static = read_csv(PATHS["round11"], dtype={"record_id": str})
        cls.round13 = read_csv(PATHS["round13"], dtype={"R1_station_id": str})
        cls.round15_native = read_csv(
            PATHS["round15_native"], dtype={"record_id": str}
        )
        cls.collision = read_csv(PATHS["collision"])

        network = cls.static.loc[cls.static["record_type"].eq("R1_NETWORK_ASSET")].copy()
        cls.r1_ids = sorted(network["record_id"].astype(str).unique())
        cls.r1_hash = hash_frozen_r1_ids(cls.r1_ids)
        cls.expected_static_mask = (
            pd.to_numeric(
                network.set_index("record_id")["effective_no_damage_network_state"],
                errors="coerce",
            )
            .reindex(cls.r1_ids)
            .notna()
        )

    @classmethod
    def provenance(
        cls,
        trajectory_id: str,
        source_time_unit: str,
        producer_file: str,
        producer_function: str,
    ) -> dict[str, str]:
        return {
            "schema_version": SCHEMA_VERSION,
            "trajectory_id": trajectory_id,
            "producer_file": producer_file,
            "producer_function": producer_function,
            "effective_state_semantics": EFFECTIVE_STATE_SEMANTICS,
            "frozen_R1_ID_hash": cls.r1_hash,
            "source_time_unit": source_time_unit,
            "source_scenario_identifier": "retained_fixture_no_recompute",
            "producer_code_hash": "retained_fixture_no_execution",
        }

    @classmethod
    def round13_matrices(cls) -> tuple[pd.DataFrame, pd.DataFrame]:
        frame = cls.round13.copy()
        frame["time_index"] = pd.to_numeric(frame["time_index"])
        frame["effective_state_value"] = pd.to_numeric(frame["effective_state_value"])
        frame["state_identified"] = parse_bool(frame["state_identified"])
        state = frame.pivot(
            index="time_index", columns="R1_station_id", values="effective_state_value"
        ).reindex(columns=cls.r1_ids).astype(float)
        mask = frame.pivot(
            index="time_index", columns="R1_station_id", values="state_identified"
        ).reindex(columns=cls.r1_ids)
        return state, mask

    def test_01_round11_static_fixture_is_lossless(self) -> None:
        network = self.static.loc[
            self.static["record_type"].eq("R1_NETWORK_ASSET")
        ].copy()
        native = pd.to_numeric(
            network.set_index("record_id")["effective_no_damage_network_state"],
            errors="coerce",
        ).reindex(self.r1_ids)
        state = pd.DataFrame([native.to_numpy()], columns=self.r1_ids, index=["static"])
        mask = pd.DataFrame(
            [native.notna().to_numpy(dtype=bool)], columns=self.r1_ids, index=["static"]
        )
        exported = export_r1_effective_state_trajectory(
            state,
            mask,
            ["reference_no_damage_snapshot"],
            "static_snapshot",
            self.r1_ids,
            self.provenance(
                "round11_static_fixture",
                "static_snapshot",
                "11_TwoLayer_Static_QA_20260914/SERVICE_NODE_BASELINE_QA.csv",
                "retained_static_export",
            ),
        )
        validated = load_validate_r1_effective_state_trajectory(
            exported.trajectory,
            self.r1_ids,
            expected_identified_mask=self.expected_static_mask,
        )
        row = validated.semantic_states.iloc[0]
        self.assertEqual(int(row.eq(1.0).sum()), 304)
        self.assertEqual(int(row.eq(0.0).sum()), 2)
        self.assertEqual(int(row.isna().sum()), 4)
        self.assertEqual(sorted(row.index[row.eq(0.0)]), ["306980", "309598"])
        self.assertEqual(
            sorted(row.index[row.isna()]),
            ["301479", "303265", "304137", "305021"],
        )

    def test_02_round13_five_step_fixture_matches_round15_adapter(self) -> None:
        state, mask = self.round13_matrices()
        exported = export_r1_effective_state_trajectory(
            state,
            mask,
            list(state.index),
            "dimensionless_qa_index",
            self.r1_ids,
            self.provenance(
                "round13_five_step_fixture",
                "dimensionless_qa_index",
                "13_TimeIndexed_Interface_QA_20260914/EXTERNAL_R1_EFFECTIVE_STATE_TRAJECTORY.csv",
                "retained_fixture_only",
            ),
        )
        round15_restored = adapt_native_r1_effective_state_envelope(
            self.round15_native, self.r1_ids
        )
        assert_frame_equal(
            exported.trajectory.reset_index(drop=True),
            round15_restored.reset_index(drop=True),
            check_exact=True,
            check_dtype=False,
        )
        self.assertEqual(len(exported.trajectory), 1550)
        load_validate_r1_effective_state_trajectory(
            exported.trajectory,
            self.r1_ids,
            expected_identified_mask=self.expected_static_mask,
        )

    def test_03_zero_missing_collision_is_lossless(self) -> None:
        self.assertEqual(len(self.collision), 4)
        state = pd.DataFrame(
            np.ones((1, len(self.r1_ids))), columns=self.r1_ids, index=["collision"]
        )
        mask = pd.DataFrame(
            np.ones((1, len(self.r1_ids)), dtype=bool),
            columns=self.r1_ids,
            index=["collision"],
        )
        for station_id, row in zip(self.r1_ids[:4], self.collision.itertuples(index=False)):
            state.loc["collision", station_id] = float(row.effective_state_value)
            mask.loc["collision", station_id] = (
                str(row.state_identified).strip().lower() == "true"
            )
        exported = export_r1_effective_state_trajectory(
            state,
            mask,
            [0],
            "synthetic_contract_index",
            self.r1_ids,
            self.provenance(
                "zero_missing_collision_fixture",
                "synthetic_contract_index",
                "ZERO_MISSING_COLLISION_FIXTURE.csv",
                "test_fixture_overlay",
            ),
        )
        expected_mask = mask.iloc[0]
        validated = load_validate_r1_effective_state_trajectory(
            exported.trajectory,
            self.r1_ids,
            expected_identified_mask=expected_mask,
        )
        observed = validated.semantic_states.iloc[0, :4]
        self.assertEqual(observed.iloc[0], 0.0)
        self.assertEqual(observed.iloc[1], 1.0)
        self.assertEqual(observed.iloc[2], 0.375)
        self.assertTrue(pd.isna(observed.iloc[3]))
        serialized = exported.trajectory.set_index("R1_station_id").loc[self.r1_ids[:4]]
        self.assertEqual(serialized.iloc[0]["effective_state_value"], 0.0)
        self.assertTrue(bool(serialized.iloc[0]["state_identified"]))
        self.assertEqual(serialized.iloc[3]["effective_state_value"], 0.0)
        self.assertFalse(bool(serialized.iloc[3]["state_identified"]))

    def test_04_gate_output_static_semantic_gap_is_present(self) -> None:
        source = Path(safe(PATHS["main"])).read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = {
            node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        gate = functions["apply_source_gate_to_substation_series"]
        gate_text = ast.get_source_segment(source, gate)
        self.assertIn("values[row_idx, ~keep_mask] = 0.0", gate_text)
        self.assertNotIn("state_identified", gate_text)
        recovery = functions["simulate_recovery_mc_source_gated"]
        recovery_text = ast.get_source_segment(source, recovery)
        self.assertIn("mean_recovery = sum_recovery / max(n_mc, 1)", recovery_text)
        self.assertIn("return recovery_df", recovery_text)
        self.assertNotIn("state_identified", recovery_text)

    def test_05_malformed_inputs_fail_fast(self) -> None:
        state, mask = self.round13_matrices()
        times = list(state.index)
        provenance = self.provenance(
            "malformed_fixture",
            "dimensionless_qa_index",
            "test_dynamic_export_contract.py",
            "malformed_fixture",
        )

        def invoke(
            state_arg=state,
            mask_arg=mask,
            time_arg=times,
            unit_arg="dimensionless_qa_index",
            ids_arg=None,
        ):
            ids = self.r1_ids if ids_arg is None else ids_arg
            current_provenance = dict(provenance)
            current_provenance["frozen_R1_ID_hash"] = hash_frozen_r1_ids(ids)
            current_provenance["source_time_unit"] = unit_arg
            return export_r1_effective_state_trajectory(
                state_arg,
                mask_arg,
                time_arg,
                unit_arg,
                ids,
                current_provenance,
            )

        cases = []
        cases.append(("state missing station", state.drop(columns=self.r1_ids[0]), mask, times, None))
        cases.append(("mask missing station", state, mask.drop(columns=self.r1_ids[0]), times, None))

        unknown = state.copy()
        unknown.columns = ["999999" if c == self.r1_ids[0] else c for c in unknown.columns]
        cases.append(("unknown station", unknown, mask, times, None))

        duplicate = state.copy()
        duplicate.columns = [self.r1_ids[0], self.r1_ids[0], *self.r1_ids[2:]]
        cases.append(("duplicate station", duplicate, mask, times, None))

        shape_mask = pd.concat([mask, mask.iloc[[0]].rename(index={0: 99})])
        cases.append(("shape mismatch", state, shape_mask, times, None))

        unalignable = mask.copy()
        unalignable.columns = ["X" + c for c in unalignable.columns]
        cases.append(("unalignable ID mismatch", state, unalignable, times, None))

        true_nan = state.copy()
        true_nan.iloc[0, 0] = np.nan
        true_nan_mask = mask.copy()
        true_nan_mask.iloc[0, 0] = True
        cases.append(("identified NaN", true_nan, true_nan_mask, times, None))

        negative = state.copy()
        negative.iloc[0, 0] = -0.01
        cases.append(("identified below zero", negative, mask, times, None))

        above = state.copy()
        above.iloc[0, 0] = 1.01
        cases.append(("identified above one", above, mask, times, None))

        masked_nonzero = state.copy()
        masked_nonzero_mask = mask.copy()
        masked_nonzero.iloc[0, 0] = 0.25
        masked_nonzero_mask.iloc[0, 0] = False
        cases.append(("masked nonzero", masked_nonzero, masked_nonzero_mask, times, None))

        cases.append(("source time length", state, mask, times[:-1], None))
        cases.append(("source time nonmonotonic", state, mask, [0, 2, 1, 3, 4], None))
        cases.append(("source unit missing", state, mask, times, ""))

        duplicate_time = state.copy()
        duplicate_time.index = [0, 1, 1, 3, 4]
        duplicate_time_mask = mask.copy()
        duplicate_time_mask.index = duplicate_time.index
        cases.append(("duplicate trajectory time", duplicate_time, duplicate_time_mask, times, None))

        short_ids = self.r1_ids[:-1]
        cases.append(
            (
                "station set not frozen 310",
                state.drop(columns=self.r1_ids[-1]),
                mask.drop(columns=self.r1_ids[-1]),
                times,
                short_ids,
            )
        )

        for label, state_arg, mask_arg, time_arg, special in cases:
            with self.subTest(label=label):
                with self.assertRaises(R1EffectiveStateExportError):
                    if label == "source unit missing":
                        invoke(state_arg, mask_arg, time_arg, unit_arg="")
                    elif label == "station set not frozen 310":
                        invoke(state_arg, mask_arg, time_arg, ids_arg=special)
                    else:
                        invoke(state_arg, mask_arg, time_arg)
        self.assertEqual(len(cases), 15)

    def test_06_explicit_station_labels_allow_safe_column_reordering(self) -> None:
        state, mask = self.round13_matrices()
        reversed_mask = mask[list(reversed(self.r1_ids))]
        exported = export_r1_effective_state_trajectory(
            state,
            reversed_mask,
            list(state.index),
            "dimensionless_qa_index",
            self.r1_ids,
            self.provenance(
                "safe_explicit_id_alignment",
                "dimensionless_qa_index",
                "test_dynamic_export_contract.py",
                "safe_alignment_fixture",
            ),
        )
        self.assertEqual(len(exported.trajectory), 1550)

    def test_07_exporter_dependency_boundary_and_main_untouched(self) -> None:
        tree = ast.parse(Path(safe(PATHS["exporter"])).read_text(encoding="utf-8"))
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
        allowed = {
            "__future__",
            "dataclasses",
            "hashlib",
            "json",
            "typing",
            "numpy",
            "pandas",
        }
        self.assertTrue(imported_roots.issubset(allowed), imported_roots - allowed)
        self.assertEqual(sha256(PATHS["main"]), EXPECTED_HASHES["main"])

    def test_08_run1_run2_exact_determinism(self) -> None:
        state, mask = self.round13_matrices()
        arguments = dict(
            effective_state=state,
            state_identified=mask,
            source_time=list(state.index),
            source_time_unit="dimensionless_qa_index",
            frozen_r1_ids=self.r1_ids,
            provenance=self.provenance(
                "determinism_fixture",
                "dimensionless_qa_index",
                "test_dynamic_export_contract.py",
                "determinism_fixture",
            ),
        )
        run1 = export_r1_effective_state_trajectory(**arguments)
        run2 = export_r1_effective_state_trajectory(**arguments)
        assert_frame_equal(run1.trajectory, run2.trajectory, check_exact=True)
        self.assertEqual(run1.provenance, run2.provenance)

    @classmethod
    def tearDownClass(cls) -> None:
        hashes_after = {name: sha256(path) for name, path in PATHS.items()}
        if hashes_after != cls.hashes_before:
            raise AssertionError("Frozen model, fixtures, adapters, or production files changed")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DynamicExportContractTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        summary = {
            "result": "PASS_DYNAMIC_EXPORT_CONTRACT_VERIFIED",
            "tests": result.testsRun,
            "malformed_cases": 15,
            "round11_station_cells": 310,
            "round13_state_mask_cells": 1550,
            "collision_cases": 4,
            "main_model_unchanged": True,
            "frozen_hashes_unchanged": True,
        }
        print("\nDYNAMIC_EXPORT_TEST_SUMMARY=" + json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
