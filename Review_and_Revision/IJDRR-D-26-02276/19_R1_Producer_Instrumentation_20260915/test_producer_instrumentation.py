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
ROUND11 = REVIEW / "11_TwoLayer_Static_QA_20260914"
ROUND13 = REVIEW / "13_TimeIndexed_Interface_QA_20260914"
ROUND14 = REVIEW / "14_Production_Interface_Contract_20260914"
ROUND16 = REVIEW / "16_R1_Dynamic_Export_Contract_20260915"
ROUND17 = REVIEW / "17_R1_Disabled_Export_Wiring_20260915"
ROUND18 = REVIEW / "18_R1_Producer_Materialization_20260915"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROUND14))
sys.path.insert(0, str(ROUND16))
sys.path.insert(0, str(ROUND17))
sys.path.insert(0, str(ROUND18))

from r1_effective_state_materializer import (  # noqa: E402
    R1RealizationMaterializationError,
    create_r1_realization_materializer,
)
from r1_effective_state_producer_observer import (  # noqa: E402
    IDENTIFIABILITY_SCOPE,
    R1EffectiveStateProducerObserver,
    R1ProducerObserverError,
    create_r1_effective_state_producer_observer,
    observe_precomputed_r1_segment,
)
from r1_effective_state_export_hook import (  # noqa: E402
    R1EffectiveStateExportHook,
    maybe_export_r1_effective_state,
)
from r1_effective_state_exporter import (  # noqa: E402
    EFFECTIVE_STATE_SEMANTICS,
    SCHEMA_VERSION,
    export_r1_effective_state_trajectory,
    hash_frozen_r1_ids,
)
from service_layer_interface import load_validate_r1_effective_state_trajectory  # noqa: E402


PATHS = {
    "main": ROOT / "C257H_Project_Main.py",
    "round11": ROUND11 / "SERVICE_NODE_BASELINE_QA.csv",
    "round13": ROUND13 / "EXTERNAL_R1_EFFECTIVE_STATE_TRAJECTORY.csv",
    "production": ROUND14 / "service_layer_interface.py",
    "exporter": ROUND16 / "r1_effective_state_exporter.py",
    "hook": ROUND17 / "r1_effective_state_export_hook.py",
    "materializer": ROUND18 / "r1_effective_state_materializer.py",
    "observer": HERE / "r1_effective_state_producer_observer.py",
}

EXPECTED_FROZEN_HASHES = {
    "main": "b9efcd0487b1e9f115876a3c6f2b45dc342e20c7a516cd491846d4f9557654df",
    "round11": "a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384",
    "round13": "b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6",
    "production": "d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514",
    "exporter": "79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b",
    "hook": "e3eb5228be0b17580f7313cac7d234f326f7e00c2a7fd027ba853ef6d01f4bf2",
    "materializer": "ce95b971cadac9bc6f07d24832fcd8d817904395abfa2b447b86c4f3774da77d",
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


def frame_hash(frame: pd.DataFrame) -> str:
    return hashlib.sha256(
        frame.to_csv(index=True, lineterminator="\n", float_format="%.17g").encode("utf-8")
    ).hexdigest()


def parse_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


class ExplosivePayload:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError(f"Disabled observer inspected payload attribute {name}")


class ProducerInstrumentationTest(unittest.TestCase):
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
        cls.r1_hash = hash_frozen_r1_ids(cls.r1_ids)
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

    @classmethod
    def provenance(
        cls, source_time_unit: str = "dimensionless_qa_index", **overrides: object
    ) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "trajectory_id": "fixture__strategy__realization_0019",
            "producer_file": "precomputed_fixture_only",
            "producer_function": "fixture_segment_supplier",
            "effective_state_semantics": EFFECTIVE_STATE_SEMANTICS,
            "frozen_R1_ID_hash": cls.r1_hash,
            "source_time_unit": source_time_unit,
            "source_scenario_identifier": "fixture_scenario",
            "producer_code_hash": "fixture_no_scientific_execution",
            "scenario_id": "fixture_scenario",
            "strategy_id": "fixture_strategy",
            "realization_id": "0019",
            "trajectory_scope": "realization",
        }
        result.update(overrides)
        return result

    def make_enabled_observer(
        self,
        source_time: list[object],
        *,
        provenance: dict[str, object] | None = None,
    ) -> tuple[R1EffectiveStateProducerObserver, object]:
        provenance = self.provenance() if provenance is None else provenance
        materializer = create_r1_realization_materializer(
            enabled=True,
            frozen_r1_ids=self.r1_ids,
            source_time=source_time,
            source_time_unit=str(provenance["source_time_unit"]),
            provenance=provenance,
        )
        observer = create_r1_effective_state_producer_observer(
            enabled=True,
            materializer=materializer,
            provenance=provenance,
            authoritative_station_mask=self.authoritative_mask,
        )
        return observer, materializer

    def mask_segment(self, start: int, stop: int, source_time: list[object]) -> pd.DataFrame:
        values = np.broadcast_to(
            self.authoritative_mask.to_numpy(dtype=bool),
            (stop - start, len(self.r1_ids)),
        ).copy()
        return pd.DataFrame(
            values,
            index=pd.Index(source_time[start:stop]),
            columns=self.r1_ids,
        )

    def test_01_disabled_observer_is_preinspection_no_op(self) -> None:
        observer = create_r1_effective_state_producer_observer(
            enabled=False,
            materializer=ExplosivePayload(),
            provenance=ExplosivePayload(),
            authoritative_station_mask=ExplosivePayload(),
        )
        self.assertFalse(observer.enabled)
        self.assertIsNone(observer.materializer)
        self.assertIsNone(observer.authoritative_station_mask)
        self.assertIsNone(
            observe_precomputed_r1_segment(
                observer=observer,
                time_start=ExplosivePayload(),
                time_stop=ExplosivePayload(),
                effective_state_segment=ExplosivePayload(),
                state_identified_segment=ExplosivePayload(),
            )
        )

        segment = np.array([[0.0, 0.125, 0.5], [1.0, 0.375, 0.0]], dtype=np.float64)
        control = np.zeros_like(segment)
        observed = np.zeros_like(segment)
        control += segment
        observe_precomputed_r1_segment(
            observer=observer,
            time_start=0,
            time_stop=2,
            effective_state_segment=None,
            state_identified_segment=None,
        )
        observed += segment
        self.assertTrue(np.array_equal(control, observed))
        self.assertEqual(control.tobytes(), observed.tobytes())

    def _run_parity_fixture(
        self, source_time: list[int], segments: list[tuple[int, int, pd.DataFrame]]
    ) -> tuple[np.ndarray, np.ndarray, object]:
        observer, materializer = self.make_enabled_observer(source_time)
        control = np.zeros((len(source_time), len(self.r1_ids)), dtype=np.float64)
        observed = np.zeros_like(control)
        expected = np.zeros_like(control)
        for start, stop, segment in segments:
            mask = self.mask_segment(start, stop, source_time)
            state_hash = frame_hash(segment)
            mask_hash = frame_hash(mask)
            control[start:stop, :] += segment.to_numpy(dtype=np.float64)
            returned = observe_precomputed_r1_segment(
                observer=observer,
                time_start=start,
                time_stop=stop,
                effective_state_segment=segment,
                state_identified_segment=mask,
            )
            self.assertIsNone(returned)
            observed[start:stop, :] += segment.to_numpy(dtype=np.float64)
            expected[start:stop, :] = segment.to_numpy(dtype=np.float64)
            self.assertEqual(frame_hash(segment), state_hash)
            self.assertEqual(frame_hash(mask), mask_hash)
        self.assertEqual(control.tobytes(), observed.tobytes())
        produced = materializer.finalize()
        self.assertTrue(np.array_equal(produced.effective_state.to_numpy(), expected))
        return control, observed, produced

    def test_02_five_control_flow_semantics_are_explicit_and_bitwise(self) -> None:
        times = list(range(8))
        zero_0_2 = pd.DataFrame(0.0, index=times[0:2], columns=self.r1_ids)
        fraction = np.tile(np.linspace(0.0, 1.0, len(self.r1_ids)), (2, 1))
        fraction[:, ~self.authoritative_mask.to_numpy()] = 0.0
        nonzero_2_4 = pd.DataFrame(fraction, index=times[2:4], columns=self.r1_ids)
        zero_4_6 = pd.DataFrame(0.0, index=times[4:6], columns=self.r1_ids)
        mixed = np.tile(np.array([0.0, 0.25, 0.5, 1.0]), 78)[:310]
        mixed = np.vstack([mixed, mixed[::-1]])
        mixed[:, ~self.authoritative_mask.to_numpy()] = 0.0
        mixed_6_8 = pd.DataFrame(mixed, index=times[6:8], columns=self.r1_ids)

        self._run_parity_fixture(
            times,
            [
                (0, 2, zero_0_2),
                (2, 4, nonzero_2_4),
                (4, 6, zero_4_6),
                (6, 8, mixed_6_8),
            ],
        )

        full_zero = pd.DataFrame(0.0, index=times, columns=self.r1_ids)
        self._run_parity_fixture(times, [(0, 8, full_zero)])

        ungated = pd.DataFrame(
            np.vstack([np.linspace(0.0, 1.0, 310) for _ in times]),
            index=times,
            columns=self.r1_ids,
        )
        ungated.loc[:, ~self.authoritative_mask] = 0.0
        self._run_parity_fixture(times, [(0, 8, ungated)])

    def test_03_observer_copy_breaks_caller_alias(self) -> None:
        times = [0, 1]
        observer, materializer = self.make_enabled_observer(times)
        segment = pd.DataFrame(
            np.tile(np.linspace(0.0, 1.0, 310), (2, 1)),
            index=times,
            columns=self.r1_ids,
        )
        segment.loc[:, ~self.authoritative_mask] = 0.0
        mask = self.mask_segment(0, 2, times)
        state_snapshot = segment.copy(deep=True)
        mask_snapshot = mask.copy(deep=True)
        observe_precomputed_r1_segment(
            observer=observer,
            time_start=0,
            time_stop=2,
            effective_state_segment=segment,
            state_identified_segment=mask,
        )
        assert_frame_equal(segment, state_snapshot, check_exact=True)
        assert_frame_equal(mask, mask_snapshot, check_exact=True)

        segment.iloc[:, :] = 0.0
        mask.iloc[:, :] = False
        produced = materializer.finalize()
        assert_frame_equal(
            produced.effective_state,
            state_snapshot.rename_axis(index="source_time", columns="R1_station_id"),
            check_exact=True,
        )
        assert_frame_equal(
            produced.state_identified,
            mask_snapshot.rename_axis(index="source_time", columns="R1_station_id"),
            check_exact=True,
        )

    def test_04_round13_observer_transport_is_1550_exact(self) -> None:
        times = list(self.round13_state.index)
        observer, materializer = self.make_enabled_observer(times)
        for start, stop in [(0, 1), (1, 3), (3, 5)]:
            state = self.round13_state.iloc[start:stop].copy()
            mask = self.round13_mask.iloc[start:stop].copy()
            observe_precomputed_r1_segment(
                observer=observer,
                time_start=start,
                time_stop=stop,
                effective_state_segment=state,
                state_identified_segment=mask,
            )
        produced = materializer.finalize()
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
        self.assertEqual(observer.segments_observed, 3)
        self.assertEqual(observer.cells_observed, 1550)

    def test_05_round11_supports_station_static_identifiability(self) -> None:
        self.assertEqual(IDENTIFIABILITY_SCOPE, "STATION_STATIC_WITHIN_TRAJECTORY")
        self.assertEqual(int(self.authoritative_mask.sum()), 306)
        self.assertEqual(int((~self.authoritative_mask).sum()), 4)
        self.assertEqual(
            sorted(self.authoritative_mask.index[~self.authoritative_mask]),
            ["301479", "303265", "304137", "305021"],
        )
        for _, row in self.round13_mask.iterrows():
            self.assertTrue(row.equals(self.authoritative_mask))
        static_values = pd.to_numeric(
            self.static.loc[
                self.static["record_type"].eq("R1_NETWORK_ASSET")
            ].set_index("record_id")["effective_no_damage_network_state"],
            errors="coerce",
        ).reindex(self.r1_ids)
        self.assertEqual(sorted(static_values.index[static_values.eq(0.0)]), ["306980", "309598"])
        self.assertTrue(self.authoritative_mask.loc[["306980", "309598"]].all())

    def test_06_factor_expression_refactor_is_bitwise_exact(self) -> None:
        curves = np.array(
            [
                [0.0, 0.125, 0.5, 1.0],
                [1.0, 0.375, 0.0, 0.875],
                [0.25, 0.75, 0.625, 0.0],
            ],
            dtype=np.float64,
        )
        keep = np.array([True, False, True, False], dtype=bool)
        direct = np.zeros_like(curves)
        named = np.zeros_like(curves)
        direct += curves * keep
        legacy_segment = curves * keep
        named += legacy_segment
        self.assertEqual(legacy_segment.dtype, (curves * keep).dtype)
        self.assertEqual(legacy_segment.shape, curves.shape)
        self.assertEqual((curves * keep).tobytes(), legacy_segment.tobytes())
        self.assertEqual(direct.tobytes(), named.tobytes())

    def test_07_observer_fail_fast_contract(self) -> None:
        times = [0, 1]
        valid_state = pd.DataFrame(0.0, index=times, columns=self.r1_ids)
        valid_mask = self.mask_segment(0, 2, times)

        with self.assertRaises(R1ProducerObserverError):
            create_r1_effective_state_producer_observer(
                enabled=True,
                materializer=None,
                provenance=self.provenance(),
                authoritative_station_mask=self.authoritative_mask,
            )

        for scope in ["mc_mean", "aggregate"]:
            with self.subTest(scope=scope):
                observer, _ = self.make_enabled_observer(times)
                observer.provenance = self.provenance(trajectory_scope=scope)
                with self.assertRaises(R1ProducerObserverError):
                    observe_precomputed_r1_segment(
                        observer=observer,
                        time_start=0,
                        time_stop=2,
                        effective_state_segment=valid_state,
                        state_identified_segment=valid_mask,
                    )

        observer, _ = self.make_enabled_observer(times)
        with self.assertRaises(R1ProducerObserverError):
            observe_precomputed_r1_segment(
                observer=observer,
                time_start=0,
                time_stop=2,
                effective_state_segment=None,
                state_identified_segment=valid_mask,
            )
        with self.assertRaises(R1ProducerObserverError):
            observe_precomputed_r1_segment(
                observer=observer,
                time_start=0,
                time_stop=2,
                effective_state_segment=valid_state,
                state_identified_segment=None,
            )

        bad_cases: list[tuple[str, object, object]] = []
        bad_cases.append(("shape_mismatch", valid_state.iloc[[0]], valid_mask))
        bad_cases.append(("subset", valid_state.iloc[:, :-1], valid_mask.iloc[:, :-1]))
        bad_cases.append(("anonymous_array", valid_state.to_numpy(), valid_mask))
        station_mismatch = valid_mask.rename(columns={self.r1_ids[-1]: "UNKNOWN_R1"})
        bad_cases.append(("station_mismatch", valid_state, station_mismatch))
        time_mismatch = valid_mask.copy()
        time_mismatch.index = [10, 11]
        bad_cases.append(("time_mismatch", valid_state, time_mismatch))
        masked_nonzero = valid_state.copy()
        masked_nonzero.loc[0, self.r1_ids[0]] = 0.25
        masked_mask = valid_mask.copy()
        masked_mask.loc[0, self.r1_ids[0]] = False
        bad_cases.append(("masked_nonzero", masked_nonzero, masked_mask))
        invalid_value = valid_state.copy()
        invalid_value.loc[0, self.r1_ids[0]] = 1.25
        bad_cases.append(("identified_invalid", invalid_value, valid_mask))

        for name, state, mask in bad_cases:
            with self.subTest(case=name):
                fresh_observer, _ = self.make_enabled_observer(times)
                with self.assertRaises((R1ProducerObserverError, R1RealizationMaterializationError)):
                    observe_precomputed_r1_segment(
                        observer=fresh_observer,
                        time_start=0,
                        time_stop=2,
                        effective_state_segment=state,
                        state_identified_segment=mask,
                    )

    def test_08_static_control_flow_paths_are_identified_without_execution(self) -> None:
        source = PATHS["main"].read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "simulate_recovery_mc_source_gated"
        )
        function_source = ast.get_source_segment(source, function)
        required_fragments = [
            "if not source_gate_enabled:",
            "local_sum += curves_by_ds[ds_vec, :, sub_positions].T",
            "if len(event_idxs) == 0:",
            "functional_mask = crossing_idx <= time_start",
            "keep_mask = _keep_mask_for_functional(functional_mask)",
            "if np.any(keep_mask):",
            "curves_by_ds[ds_vec, time_start:time_stop, sub_positions].T * keep_mask",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, function_source)

    def test_09_observer_dependency_boundary_and_main_are_frozen(self) -> None:
        source = PATHS["observer"].read_text(encoding="utf-8")
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
                    "typing",
                    "numpy",
                    "pandas",
                    "r1_effective_state_materializer",
                }
            )
        )
        forbidden = [
            "networkx",
            "connected_components",
            "load_source",
            "keep_mask =",
            "functional_threshold",
            "curves_by_ds",
            "damage_state",
            "fragility",
            "repair_time",
            "crew",
            "schedule",
            "genetic_algorithm",
            "local_sum",
            "service_layer_interface",
            "r1_effective_state_exporter",
            "r1_effective_state_export_hook",
        ]
        lowered = source.lower()
        for token in forbidden:
            self.assertNotIn(token.lower(), lowered)
        self.assertEqual(sha256(PATHS["main"]), EXPECTED_FROZEN_HASHES["main"])

    @classmethod
    def tearDownClass(cls) -> None:
        hashes_after = {name: sha256(path) for name, path in PATHS.items()}
        for name in EXPECTED_FROZEN_HASHES:
            if hashes_after[name] != cls.hashes_before[name]:
                raise AssertionError(f"Frozen input changed during test: {name}")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProducerInstrumentationTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        summary = {
            "result": "PASS_PRODUCER_INSTRUMENTATION_CONTRACT_VERIFIED",
            "tests": result.testsRun,
            "control_flow_cases": 5,
            "round13_cells": 1550,
            "round11_identified": 306,
            "round11_missing": 4,
            "observer_fail_fast_cases": 12,
            "scientific_runs": 0,
            "main_model_unchanged": True,
        }
        print("\nPRODUCER_INSTRUMENTATION_TEST_SUMMARY=" + json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
