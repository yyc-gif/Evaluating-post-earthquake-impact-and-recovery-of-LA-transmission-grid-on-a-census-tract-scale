from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal


HERE = Path(__file__).parent
ROOT = HERE.parents[2]
REVIEW = ROOT / "Review_and_Revision" / "IJDRR-D-26-02276"
ROUND11 = REVIEW / "11_TwoLayer_Static_QA_20260914"
ROUND13 = REVIEW / "13_TimeIndexed_Interface_QA_20260914"
ROUND14 = REVIEW / "14_Production_Interface_Contract_20260914"
ROUND16 = REVIEW / "16_R1_Dynamic_Export_Contract_20260915"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROUND14))
sys.path.insert(0, str(ROUND16))

from r1_effective_state_export_hook import (  # noqa: E402
    R1EffectiveStateExportHook,
    R1EffectiveStateExportHookError,
    maybe_export_r1_effective_state,
)
from r1_effective_state_exporter import (  # noqa: E402
    EFFECTIVE_STATE_SEMANTICS,
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
    "exporter": ROUND16 / "r1_effective_state_exporter.py",
    "production": ROUND14 / "service_layer_interface.py",
    "hook": HERE / "r1_effective_state_export_hook.py",
}

EXPECTED_FROZEN_HASHES = {
    "round11": "a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384",
    "round13": "b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6",
    "exporter": "79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b",
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


class DisabledExportWiringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hashes_before = {name: sha256(path) for name, path in PATHS.items()}
        for name, expected in EXPECTED_FROZEN_HASHES.items():
            if cls.hashes_before[name] != expected:
                raise AssertionError(
                    f"Frozen hash mismatch for {name}: {cls.hashes_before[name]} != {expected}"
                )

        baseline = read_csv(PATHS["round11"], dtype={"record_id": str})
        network = baseline.loc[baseline["record_type"].eq("R1_NETWORK_ASSET")]
        cls.r1_ids = sorted(network["record_id"].astype(str).unique())
        if len(cls.r1_ids) != 310:
            raise AssertionError(f"Expected 310 frozen R1 IDs, got {len(cls.r1_ids)}")
        cls.r1_hash = hash_frozen_r1_ids(cls.r1_ids)

        cls.round13 = read_csv(PATHS["round13"], dtype={"R1_station_id": str})
        cls.round13["time_index"] = pd.to_numeric(cls.round13["time_index"])
        cls.round13["effective_state_value"] = pd.to_numeric(
            cls.round13["effective_state_value"]
        )
        cls.round13["state_identified"] = parse_bool(cls.round13["state_identified"])
        cls.state = cls.round13.pivot(
            index="time_index", columns="R1_station_id", values="effective_state_value"
        ).reindex(columns=cls.r1_ids).astype(float)
        cls.mask = cls.round13.pivot(
            index="time_index", columns="R1_station_id", values="state_identified"
        ).reindex(columns=cls.r1_ids).astype(bool)
        cls.source_time = list(cls.state.index)

    @classmethod
    def provenance(cls, **overrides: object) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "trajectory_id": "sce_reference__hospital_first__realization_0007",
            "producer_file": "synthetic_fixture_only",
            "producer_function": "fixture_producer_no_scientific_computation",
            "effective_state_semantics": EFFECTIVE_STATE_SEMANTICS,
            "frozen_R1_ID_hash": cls.r1_hash,
            "source_time_unit": "dimensionless_qa_index",
            "source_scenario_identifier": "sce_reference",
            "producer_code_hash": "fixture_no_execution",
            "scenario_id": "sce_reference",
            "strategy_id": "hospital_first",
            "realization_id": "0007",
            "trajectory_scope": "realization",
        }
        result.update(overrides)
        return result

    def export_kwargs(self, **overrides: object) -> dict[str, object]:
        result: dict[str, object] = {
            "effective_state": self.state,
            "state_identified": self.mask,
            "source_time": self.source_time,
            "source_time_unit": "dimensionless_qa_index",
            "frozen_r1_ids": self.r1_ids,
            "provenance": self.provenance(),
        }
        result.update(overrides)
        return result

    def test_01_default_hook_is_disabled_and_callback_free(self) -> None:
        hook = R1EffectiveStateExportHook()
        self.assertIs(hook.enabled, False)
        self.assertIsNone(hook.callback)

    def test_02_disabled_seam_is_exact_no_op(self) -> None:
        calls: list[dict[str, object]] = []

        def callback(**kwargs: object) -> None:
            calls.append(kwargs)

        hook = R1EffectiveStateExportHook(enabled=False, callback=callback)
        local_sum = np.array(
            [[0.0, 0.125, 4.0], [1.5, -0.0, 9.25]], dtype=np.float64
        )
        increment = np.array(
            [[0.75, 0.5, 0.25], [0.125, 2.0, 0.0]], dtype=np.float64
        )
        legacy = local_sum.copy()
        legacy += increment
        candidate = local_sum.copy()

        state_before = self.state.copy(deep=True)
        mask_before = self.mask.copy(deep=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            before_files = sorted(Path(temp_dir).iterdir())
            returned = maybe_export_r1_effective_state(
                hook=hook,
                **self.export_kwargs(),
            )
            after_files = sorted(Path(temp_dir).iterdir())

        candidate += increment
        self.assertIsNone(returned)
        self.assertEqual(calls, [])
        self.assertEqual(before_files, after_files)
        self.assertTrue(np.array_equal(candidate, legacy))
        assert_frame_equal(self.state, state_before, check_exact=True)
        assert_frame_equal(self.mask, mask_before, check_exact=True)

        self.assertIsNone(
            maybe_export_r1_effective_state(
                hook=None,
                effective_state=None,
                state_identified=None,
                source_time=None,
                source_time_unit=None,
                frozen_r1_ids=None,
                provenance=None,
            )
        )

    def test_03_enabled_missing_producer_channels_fail_closed(self) -> None:
        hook = R1EffectiveStateExportHook(
            enabled=True, callback=export_r1_effective_state_trajectory
        )
        cases = [
            self.export_kwargs(effective_state=None, state_identified=None),
            self.export_kwargs(state_identified=None),
            self.export_kwargs(effective_state=None),
        ]
        for kwargs in cases:
            with self.subTest(missing=[k for k, v in kwargs.items() if v is None]):
                with self.assertRaises(R1EffectiveStateExportHookError):
                    maybe_export_r1_effective_state(hook=hook, **kwargs)

        with self.assertRaises(R1EffectiveStateExportHookError):
            maybe_export_r1_effective_state(
                hook=R1EffectiveStateExportHook(enabled=True, callback=None),
                **self.export_kwargs(),
            )

    def test_04_round13_fixture_transport_is_lossless(self) -> None:
        hook = R1EffectiveStateExportHook(
            enabled=True, callback=export_r1_effective_state_trajectory
        )
        result = maybe_export_r1_effective_state(hook=hook, **self.export_kwargs())
        self.assertEqual(len(result.trajectory), 1550)

        expected = self.round13[
            ["time_index", "R1_station_id", "effective_state_value", "state_identified"]
        ].copy()
        actual = result.trajectory[
            ["time_index", "R1_station_id", "effective_state_value", "state_identified"]
        ].copy()
        expected = expected.sort_values(["time_index", "R1_station_id"]).reset_index(drop=True)
        actual = actual.sort_values(["time_index", "R1_station_id"]).reset_index(drop=True)
        assert_frame_equal(actual, expected, check_exact=True, check_dtype=False)
        self.assertEqual(
            result.trajectory.groupby("time_index", sort=True)["source_time"].first().tolist(),
            self.source_time,
        )
        self.assertEqual(
            set(result.trajectory["source_time_unit"]), {"dimensionless_qa_index"}
        )
        loaded = load_validate_r1_effective_state_trajectory(
            result.trajectory, self.r1_ids
        )
        self.assertEqual(loaded.semantic_states.shape, (5, 310))

    def test_05_aggregate_and_incomplete_identity_are_rejected(self) -> None:
        hook = R1EffectiveStateExportHook(
            enabled=True, callback=export_r1_effective_state_trajectory
        )
        for bad_provenance in [
            self.provenance(trajectory_scope="mc_mean"),
            self.provenance(trajectory_scope="aggregate"),
            self.provenance(realization_id=""),
            {key: value for key, value in self.provenance().items() if key != "realization_id"},
        ]:
            with self.subTest(provenance=bad_provenance):
                with self.assertRaises(R1EffectiveStateExportHookError):
                    maybe_export_r1_effective_state(
                        hook=hook, **self.export_kwargs(provenance=bad_provenance)
                    )

    def test_06_same_fixture_is_deterministic(self) -> None:
        hook = R1EffectiveStateExportHook(
            enabled=True, callback=export_r1_effective_state_trajectory
        )
        run1 = maybe_export_r1_effective_state(hook=hook, **self.export_kwargs())
        run2 = maybe_export_r1_effective_state(hook=hook, **self.export_kwargs())
        assert_frame_equal(run1.trajectory, run2.trajectory, check_exact=True)
        self.assertEqual(run1.provenance, run2.provenance)

    def test_07_hook_dependency_and_textual_boundaries_are_clean(self) -> None:
        source = PATHS["hook"].read_text(encoding="utf-8")
        tree = ast.parse(source)
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertTrue(roots.issubset({"__future__", "dataclasses", "typing"}))

        forbidden = [
            "apply_source_gate",
            "connected_components",
            "load_source",
            "damage_state_samples",
            "fragility",
            "repair_time",
            "schedule",
            "crew",
            "genetic_algorithm",
            "service_layer",
        ]
        lowered = source.lower()
        for token in forbidden:
            self.assertNotIn(token.lower(), lowered)

    def test_08_main_contains_only_disabled_future_seam(self) -> None:
        source = PATHS["main"].read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "simulate_recovery_mc_source_gated"
        )
        args = [arg.arg for arg in function.args.args]
        self.assertEqual(args[-1], "effective_state_export_hook")
        self.assertIsInstance(function.args.defaults[-1], ast.Constant)
        self.assertIsNone(function.args.defaults[-1].value)

        function_source = ast.get_source_segment(source, function)
        self.assertIn("# R1_DYNAMIC_EXPORT_SEAM:", function_source)
        self.assertIn(
            "local_sum[time_start:time_stop, :] += (\n"
            "                        curves_by_ds[ds_vec, time_start:time_stop, sub_positions].T * keep_mask\n"
            "                    )",
            function_source,
        )
        self.assertNotIn("maybe_export_r1_effective_state(", function_source)
        self.assertNotIn("export_r1_effective_state_trajectory(", function_source)

        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        production_calls = [
            node
            for node in calls
            if isinstance(node.func, ast.Name)
            and node.func.id == "simulate_recovery_mc_source_gated"
        ]
        self.assertGreaterEqual(len(production_calls), 3)
        for call in production_calls:
            self.assertNotIn(
                "effective_state_export_hook", {keyword.arg for keyword in call.keywords}
            )

    @classmethod
    def tearDownClass(cls) -> None:
        hashes_after = {name: sha256(path) for name, path in PATHS.items()}
        for name in EXPECTED_FROZEN_HASHES:
            if hashes_after[name] != cls.hashes_before[name]:
                raise AssertionError(f"Frozen input changed during test: {name}")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DisabledExportWiringTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        summary = {
            "result": "PASS_DISABLED_EXPORT_WIRING_SEAM_VERIFIED",
            "tests": result.testsRun,
            "round13_cells": 1550,
            "disabled_callback_calls": 0,
            "aggregate_scopes_rejected": 2,
            "producer_missing_channel_cases": 3,
            "scientific_runs": 0,
        }
        print("\nDISABLED_WIRING_TEST_SUMMARY=" + json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
