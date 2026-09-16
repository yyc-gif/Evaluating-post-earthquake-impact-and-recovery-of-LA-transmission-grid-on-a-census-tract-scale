from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

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
ROUND17 = REVIEW / "17_R1_Disabled_Export_Wiring_20260915"
ROUND18 = REVIEW / "18_R1_Producer_Materialization_20260915"
ROUND19 = REVIEW / "19_R1_Producer_Instrumentation_20260915"

for path in [HERE, ROUND14, ROUND16, ROUND17, ROUND18, ROUND19]:
    sys.path.insert(0, str(path))

from r1_main_model_producer_instrumentation import (  # noqa: E402
    R1MainInstrumentationError,
    create_r1_main_model_producer_instrumentation,
)
from r1_effective_state_materializer import R1RealizationMaterializationError  # noqa: E402
from r1_effective_state_export_hook import (  # noqa: E402
    R1EffectiveStateExportHook,
    maybe_export_r1_effective_state,
)
from r1_effective_state_exporter import export_r1_effective_state_trajectory  # noqa: E402
from service_layer_interface import load_validate_r1_effective_state_trajectory  # noqa: E402


PATHS = {
    "main": ROOT / "C257H_Project_Main.py",
    "round11": ROUND11 / "SERVICE_NODE_BASELINE_QA.csv",
    "round13": ROUND13 / "EXTERNAL_R1_EFFECTIVE_STATE_TRAJECTORY.csv",
    "production": ROUND14 / "service_layer_interface.py",
    "exporter": ROUND16 / "r1_effective_state_exporter.py",
    "hook": ROUND17 / "r1_effective_state_export_hook.py",
    "materializer": ROUND18 / "r1_effective_state_materializer.py",
    "observer": ROUND19 / "r1_effective_state_producer_observer.py",
    "controller": HERE / "r1_main_model_producer_instrumentation.py",
}

EXPECTED_FROZEN_HASHES = {
    "round11": "a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384",
    "round13": "b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6",
    "production": "d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514",
    "exporter": "79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b",
    "hook": "e3eb5228be0b17580f7313cac7d234f326f7e00c2a7fd027ba853ef6d01f4bf2",
    "materializer": "ce95b971cadac9bc6f07d24832fcd8d817904395abfa2b447b86c4f3774da77d",
    "observer": "ac0c395e95d81975e80830cae63e67bd2b161eec8141e61a3fa9301e14b3ac9c",
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


class CountingProvider:
    def __init__(self, value: np.ndarray) -> None:
        self.value = value
        self.calls = 0

    def compute(self) -> np.ndarray:
        self.calls += 1
        return self.value.copy()


class DisabledMainInstrumentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hashes_before = {name: sha256(path) for name, path in PATHS.items()}
        for name, expected in EXPECTED_FROZEN_HASHES.items():
            if cls.hashes_before[name] != expected:
                raise AssertionError(
                    f"Frozen hash mismatch for {name}: {cls.hashes_before[name]} != {expected}"
                )

        cls.static = read_csv(PATHS["round11"], dtype={"record_id": str})
        network = cls.static.loc[cls.static["record_type"].eq("R1_NETWORK_ASSET")].copy()
        cls.r1_ids = sorted(network["record_id"].astype(str).unique())
        state = pd.to_numeric(
            network.set_index("record_id")["effective_no_damage_network_state"],
            errors="coerce",
        ).reindex(cls.r1_ids)
        cls.authoritative_mask = state.notna().astype(bool)
        cls.authoritative_mask.index.name = "R1_station_id"

        cls.round13 = read_csv(PATHS["round13"], dtype={"R1_station_id": str})
        cls.round13["time_index"] = pd.to_numeric(cls.round13["time_index"])
        cls.round13["effective_state_value"] = pd.to_numeric(
            cls.round13["effective_state_value"]
        )
        cls.round13["state_identified"] = parse_bool(cls.round13["state_identified"])
        cls.round13_state = cls.round13.pivot(
            index="time_index", columns="R1_station_id", values="effective_state_value"
        ).reindex(columns=cls.r1_ids).astype(float)
        cls.round13_mask = cls.round13.pivot(
            index="time_index", columns="R1_station_id", values="state_identified"
        ).reindex(columns=cls.r1_ids).astype(bool)

    def controller(
        self,
        source_time: list[object],
        *,
        scenario_id: str = "fixture_scenario",
        strategy_id: str = "fixture_strategy",
    ):
        controller = create_r1_main_model_producer_instrumentation(
            enabled=True,
            scenario_id=scenario_id,
            strategy_id=strategy_id,
            source_time=source_time,
            source_time_unit="dimensionless_qa_index",
            frozen_r1_ids=self.r1_ids,
            authoritative_station_mask=self.authoritative_mask,
        )
        controller.validate_run_context(
            substation_ids=self.r1_ids,
            source_time=source_time,
            mc_source_gate_n_jobs=1,
        )
        return controller

    def synthetic_nonzero(self, rows: int) -> np.ndarray:
        values = np.tile(np.linspace(0.0, 1.0, 310), (rows, 1))
        values[:, ~self.authoritative_mask.to_numpy()] = 0.0
        return values.astype(np.float64)

    def test_01_default_controller_is_fully_inactive(self) -> None:
        controller = create_r1_main_model_producer_instrumentation()
        self.assertFalse(controller.enabled)
        self.assertEqual(controller.source_time, ())
        self.assertEqual(controller.frozen_r1_ids, ())
        self.assertIsNone(controller.authoritative_station_mask)
        self.assertIsNone(controller.collected_realizations)

    def test_02_p1_to_p5_fixture_accumulations_are_bitwise_exact(self) -> None:
        times = list(range(8))
        controller = self.controller(times)

        p1 = self.synthetic_nonzero(8)
        p1_control = np.zeros_like(p1)
        p1_observed = np.zeros_like(p1)
        p1_control += p1
        session = controller.start_realization(0)
        self.assertIsNone(
            session.observe_precomputed_segment(
                time_start=0, time_stop=8, caller_owned_segment=p1
            )
        )
        p1_observed += p1
        session.finalize()
        self.assertEqual(p1_control.tobytes(), p1_observed.tobytes())

        gated_control = np.zeros((8, 310), dtype=np.float64)
        gated_observed = np.zeros_like(gated_control)
        session = controller.start_realization(1)
        session.observe_explicit_zero_segment(time_start=0, time_stop=2)
        p3a = self.synthetic_nonzero(2)
        gated_control[2:4] += p3a
        session.observe_precomputed_segment(
            time_start=2, time_stop=4, caller_owned_segment=p3a
        )
        gated_observed[2:4] += p3a
        session.observe_explicit_zero_segment(time_start=4, time_stop=6)
        p3b = self.synthetic_nonzero(2)[:, ::-1].copy()
        p3b[:, ~self.authoritative_mask.to_numpy()] = 0.0
        gated_control[6:8] += p3b
        session.observe_precomputed_segment(
            time_start=6, time_stop=8, caller_owned_segment=p3b
        )
        gated_observed[6:8] += p3b
        session.finalize()
        self.assertEqual(gated_control.tobytes(), gated_observed.tobytes())

        p5_control = np.zeros((8, 310), dtype=np.float64)
        p5_observed = np.zeros_like(p5_control)
        session = controller.start_realization(2)
        session.observe_explicit_zero_segment(time_start=0, time_stop=8)
        session.finalize()
        self.assertEqual(p5_control.tobytes(), p5_observed.tobytes())

        self.assertEqual(len(controller.collected_realizations), 3)
        keys = sorted(controller.collected_realizations)
        self.assertEqual(
            keys,
            [
                ("fixture_scenario", "fixture_strategy", "mc_000000"),
                ("fixture_scenario", "fixture_strategy", "mc_000001"),
                ("fixture_scenario", "fixture_strategy", "mc_000002"),
            ],
        )
        np.testing.assert_array_equal(
            controller.collected_realizations[keys[0]].effective_state.to_numpy(), p1
        )
        np.testing.assert_array_equal(
            controller.collected_realizations[keys[1]].effective_state.to_numpy(),
            gated_observed,
        )
        np.testing.assert_array_equal(
            controller.collected_realizations[keys[2]].effective_state.to_numpy(),
            p5_observed,
        )

    def test_03_p3_expression_is_evaluated_once(self) -> None:
        times = [0, 1]
        controller = self.controller(times)
        session = controller.start_realization(7)
        provider = CountingProvider(self.synthetic_nonzero(2))
        local_sum = np.zeros((2, 310), dtype=np.float64)
        legacy_segment = provider.compute()
        segment_before = legacy_segment.copy()
        session.observe_precomputed_segment(
            time_start=0,
            time_stop=2,
            caller_owned_segment=legacy_segment,
        )
        local_sum += legacy_segment
        session.finalize()
        self.assertEqual(provider.calls, 1)
        self.assertEqual(local_sum.tobytes(), segment_before.tobytes())
        self.assertEqual(legacy_segment.tobytes(), segment_before.tobytes())
        key = ("fixture_scenario", "fixture_strategy", "mc_000007")
        self.assertEqual(
            controller.collected_realizations[key].effective_state.to_numpy().tobytes(),
            segment_before.tobytes(),
        )

    def test_04_zero_side_path_never_adds_to_scientific_accumulator(self) -> None:
        times = list(range(6))
        controller = self.controller(times)
        control = np.zeros((6, 310), dtype=np.float64)
        observed = np.zeros_like(control)
        session = controller.start_realization(4)
        session.observe_explicit_zero_segment(time_start=0, time_stop=2)
        session.observe_explicit_zero_segment(time_start=2, time_stop=4)
        session.observe_explicit_zero_segment(time_start=4, time_stop=6)
        session.finalize()
        self.assertEqual(control.tobytes(), observed.tobytes())
        key = ("fixture_scenario", "fixture_strategy", "mc_000004")
        materialized = controller.collected_realizations[key]
        self.assertTrue((materialized.effective_state.to_numpy() == 0.0).all())

    def test_05_round13_full_chain_is_1550_exact(self) -> None:
        times = list(self.round13_state.index)
        controller = self.controller(times)
        session = controller.start_realization(13)
        for start, stop in [(0, 1), (1, 3), (3, 4), (4, 5)]:
            segment = self.round13_state.iloc[start:stop].to_numpy(copy=True)
            session.observe_precomputed_segment(
                time_start=start,
                time_stop=stop,
                caller_owned_segment=segment,
            )
        session.finalize()
        key = ("fixture_scenario", "fixture_strategy", "mc_000013")
        produced = controller.collected_realizations[key]
        assert_frame_equal(
            produced.state_identified,
            self.round13_mask.rename_axis(index="source_time", columns="R1_station_id"),
            check_exact=True,
        )
        exported = maybe_export_r1_effective_state(
            hook=R1EffectiveStateExportHook(
                enabled=True, callback=export_r1_effective_state_trajectory
            ),
            effective_state=produced.effective_state,
            state_identified=produced.state_identified,
            source_time=produced.source_time,
            source_time_unit=produced.source_time_unit,
            frozen_r1_ids=produced.frozen_r1_ids,
            provenance=produced.provenance,
        )
        expected = self.round13[
            ["time_index", "R1_station_id", "effective_state_value", "state_identified"]
        ].sort_values(["time_index", "R1_station_id"]).reset_index(drop=True)
        actual = exported.trajectory[
            ["time_index", "R1_station_id", "effective_state_value", "state_identified"]
        ].sort_values(["time_index", "R1_station_id"]).reset_index(drop=True)
        assert_frame_equal(actual, expected, check_exact=True, check_dtype=False)
        self.assertEqual(len(actual), 1550)
        loaded = load_validate_r1_effective_state_trajectory(
            exported.trajectory,
            self.r1_ids,
            expected_identified_mask=self.authoritative_mask,
        )
        self.assertEqual(loaded.semantic_states.shape, (5, 310))

    def test_06_authoritative_mask_remains_306_4_and_not_keep_mask(self) -> None:
        self.assertEqual(int(self.authoritative_mask.sum()), 306)
        self.assertEqual(int((~self.authoritative_mask).sum()), 4)
        self.assertEqual(
            sorted(self.authoritative_mask.index[~self.authoritative_mask]),
            ["301479", "303265", "304137", "305021"],
        )
        state = pd.to_numeric(
            self.static.loc[
                self.static["record_type"].eq("R1_NETWORK_ASSET")
            ].set_index("record_id")["effective_no_damage_network_state"],
            errors="coerce",
        ).reindex(self.r1_ids)
        self.assertEqual(sorted(state.index[state.eq(0.0)]), ["306980", "309598"])
        self.assertTrue(self.authoritative_mask.loc[["306980", "309598"]].all())

    def test_07_serial_guard_and_context_fail_fast(self) -> None:
        common = {
            "enabled": True,
            "scenario_id": "scenario",
            "strategy_id": "strategy",
            "source_time": [0, 1],
            "source_time_unit": "dimensionless_qa_index",
            "frozen_r1_ids": self.r1_ids,
            "authoritative_station_mask": self.authoritative_mask,
        }
        creation_cases = [
            ("no_context", {"enabled": True}),
            ("missing_scenario", {**common, "scenario_id": None}),
            ("missing_strategy", {**common, "strategy_id": None}),
            ("missing_unit", {**common, "source_time_unit": ""}),
            ("aggregate", {**common, "trajectory_scope": "aggregate"}),
            (
                "mask_missing_station",
                {**common, "authoritative_station_mask": self.authoritative_mask.iloc[:-1]},
            ),
            (
                "mask_nonboolean",
                {**common, "authoritative_station_mask": self.authoritative_mask.astype(str)},
            ),
        ]
        unknown_mask = self.authoritative_mask.copy()
        unknown_mask.index = self.r1_ids[:-1] + ["UNKNOWN_R1"]
        creation_cases.append(
            ("mask_unknown_station", {**common, "authoritative_station_mask": unknown_mask})
        )
        for name, kwargs in creation_cases:
            with self.subTest(case=name):
                with self.assertRaises(R1MainInstrumentationError):
                    create_r1_main_model_producer_instrumentation(**kwargs)

        controller = create_r1_main_model_producer_instrumentation(**common)
        for name, ids, jobs in [
            ("sub_index_mismatch", list(reversed(self.r1_ids)), 1),
            ("n_subs_not_310", self.r1_ids[:-1], 1),
            ("parallel", self.r1_ids, 2),
        ]:
            with self.subTest(case=name):
                with self.assertRaises(R1MainInstrumentationError):
                    controller.validate_run_context(
                        substation_ids=ids,
                        source_time=[0, 1],
                        mc_source_gate_n_jobs=jobs,
                    )

        controller = self.controller([0, 1])
        controller.start_realization(0)
        with self.assertRaises(R1MainInstrumentationError):
            controller.start_realization(0)

        incomplete_controller = self.controller([0, 1])
        incomplete = incomplete_controller.start_realization(1)
        incomplete.observe_explicit_zero_segment(time_start=0, time_stop=1)
        with self.assertRaises(R1RealizationMaterializationError):
            incomplete.finalize()

        broken_controller = self.controller([0, 1])
        with patch(
            "r1_main_model_producer_instrumentation.create_r1_realization_materializer",
            return_value=None,
        ):
            with self.assertRaises(Exception):
                broken_controller.start_realization(5)

    def test_08_main_wiring_is_default_disabled_and_call_sites_unchanged(self) -> None:
        source = PATHS["main"].read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "simulate_recovery_mc_source_gated"
        )
        args = [arg.arg for arg in function.args.args]
        self.assertEqual(args[-1], "r1_producer_instrumentation")
        self.assertIsInstance(function.args.defaults[-1], ast.Constant)
        self.assertIsNone(function.args.defaults[-1].value)

        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "simulate_recovery_mc_source_gated"
        ]
        self.assertGreaterEqual(len(calls), 3)
        for call in calls:
            self.assertNotIn(
                "r1_producer_instrumentation", {kw.arg for kw in call.keywords}
            )

        text = ast.get_source_segment(source, function)
        self.assertIn(
            "local_sum[time_start:time_stop, :] += (\n"
            "                            curves_by_ds[ds_vec, time_start:time_stop, sub_positions].T * keep_mask\n"
            "                        )",
            text,
        )
        self.assertIn("legacy_segment = (", text)
        self.assertIn("caller_owned_segment=legacy_segment", text)
        self.assertIn("local_sum[time_start:time_stop, :] += legacy_segment", text)
        self.assertNotIn("local_sum += instrumentation_session", text)
        self.assertNotIn("local_sum += observer", text)
        self.assertIn("effective_state_export_hook", text)

        imported_roots = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
        forbidden = {
            "r1_effective_state_exporter",
            "r1_effective_state_export_hook",
            "service_layer_interface",
        }
        self.assertTrue(imported_roots.isdisjoint(forbidden))

    def test_09_scientific_invariants_remain_present_by_static_inspection(self) -> None:
        source = PATHS["main"].read_text(encoding="utf-8")
        required = [
            "local_sum = np.zeros((n_time, n_subs), dtype=np.float64)",
            "threshold = float(getattr(cfg, \"FUNCTIONAL_THRESHOLD\", 0.5))",
            "functional_mask = crossing_idx <= time_start",
            "keep_mask = _keep_mask_for_functional(functional_mask)",
            "mean_recovery = sum_recovery / max(n_mc, 1)",
            "ranges = [",
            "return local_sum, local_connected_count_sum",
        ]
        for fragment in required:
            self.assertIn(fragment, source)

    def test_10_controller_dependency_boundary_is_clean(self) -> None:
        source = PATHS["controller"].read_text(encoding="utf-8")
        tree = ast.parse(source)
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertTrue(
            roots.issubset(
                {
                    "__future__",
                    "dataclasses",
                    "hashlib",
                    "typing",
                    "numpy",
                    "pandas",
                    "r1_effective_state_materializer",
                    "r1_effective_state_producer_observer",
                }
            )
        )
        forbidden = [
            "networkx",
            "connected_components",
            "load_source",
            "functional_threshold",
            "curves_by_ds",
            "damage_state",
            "fragility",
            "repair_time",
            "crew",
            "schedule",
            "genetic_algorithm",
            "service_layer_interface",
            "r1_effective_state_exporter",
            "r1_effective_state_export_hook",
            "to_csv",
            "to_parquet",
        ]
        lowered = source.lower()
        for token in forbidden:
            self.assertNotIn(token.lower(), lowered)

    @classmethod
    def tearDownClass(cls) -> None:
        hashes_after = {name: sha256(path) for name, path in PATHS.items()}
        for name in EXPECTED_FROZEN_HASHES:
            if hashes_after[name] != cls.hashes_before[name]:
                raise AssertionError(f"Frozen input changed during test: {name}")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        DisabledMainInstrumentationTest
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        summary = {
            "result": "PASS_DISABLED_MAIN_MODEL_PRODUCER_WIRING_VERIFIED",
            "tests": result.testsRun,
            "control_flow_cases": 5,
            "fail_fast_cases": 14,
            "round13_cells": 1550,
            "round11_identified": 306,
            "round11_missing": 4,
            "real_scientific_runs": 0,
        }
        print("\nDISABLED_MAIN_INSTRUMENTATION_TEST_SUMMARY=" + json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
