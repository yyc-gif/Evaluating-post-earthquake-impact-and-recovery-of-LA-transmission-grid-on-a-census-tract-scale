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

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROUND14))
sys.path.insert(0, str(ROUND16))
sys.path.insert(0, str(ROUND17))

from r1_effective_state_materializer import (  # noqa: E402
    R1RealizationMaterializationError,
    R1RealizationMaterializer,
    create_r1_realization_materializer,
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
from service_layer_interface import (  # noqa: E402
    load_validate_r1_effective_state_trajectory,
)


PATHS = {
    "main": ROOT / "C257H_Project_Main.py",
    "round11": ROUND11 / "SERVICE_NODE_BASELINE_QA.csv",
    "round13": ROUND13 / "EXTERNAL_R1_EFFECTIVE_STATE_TRAJECTORY.csv",
    "production": ROUND14 / "service_layer_interface.py",
    "exporter": ROUND16 / "r1_effective_state_exporter.py",
    "hook": ROUND17 / "r1_effective_state_export_hook.py",
    "materializer": HERE / "r1_effective_state_materializer.py",
}

EXPECTED_FROZEN_HASHES = {
    "main": "b9efcd0487b1e9f115876a3c6f2b45dc342e20c7a516cd491846d4f9557654df",
    "round11": "a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384",
    "round13": "b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6",
    "production": "d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514",
    "exporter": "79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b",
    "hook": "e3eb5228be0b17580f7313cac7d234f326f7e00c2a7fd027ba853ef6d01f4bf2",
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


class ProducerMaterializationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hashes_before = {name: sha256(path) for name, path in PATHS.items()}
        for name, expected in EXPECTED_FROZEN_HASHES.items():
            if cls.hashes_before[name] != expected:
                raise AssertionError(
                    f"Frozen hash mismatch for {name}: {cls.hashes_before[name]} != {expected}"
                )

        cls.static = read_csv(PATHS["round11"], dtype={"record_id": str})
        network = cls.static.loc[
            cls.static["record_type"].eq("R1_NETWORK_ASSET")
        ].copy()
        cls.r1_ids = sorted(network["record_id"].astype(str).unique())
        cls.r1_hash = hash_frozen_r1_ids(cls.r1_ids)
        if len(cls.r1_ids) != 310:
            raise AssertionError(f"Expected 310 frozen R1 IDs, got {len(cls.r1_ids)}")

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

    @classmethod
    def provenance(
        cls, source_time_unit: str = "dimensionless_qa_index", **overrides: object
    ) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "trajectory_id": "fixture__strategy__realization_0007",
            "producer_file": "retained_or_synthetic_fixture",
            "producer_function": "fixture_segment_supplier",
            "effective_state_semantics": EFFECTIVE_STATE_SEMANTICS,
            "frozen_R1_ID_hash": cls.r1_hash,
            "source_time_unit": source_time_unit,
            "source_scenario_identifier": "fixture_scenario",
            "producer_code_hash": "fixture_no_scientific_execution",
            "scenario_id": "fixture_scenario",
            "strategy_id": "fixture_strategy",
            "realization_id": "0007",
            "trajectory_scope": "realization",
        }
        result.update(overrides)
        return result

    def new_materializer(
        self,
        *,
        source_time: list[object] | None = None,
        source_time_unit: str = "dimensionless_qa_index",
        frozen_ids: list[str] | None = None,
        provenance: dict[str, object] | None = None,
    ) -> R1RealizationMaterializer:
        result = create_r1_realization_materializer(
            enabled=True,
            frozen_r1_ids=self.r1_ids if frozen_ids is None else frozen_ids,
            source_time=list(self.state.index) if source_time is None else source_time,
            source_time_unit=source_time_unit,
            provenance=(
                self.provenance(source_time_unit)
                if provenance is None
                else provenance
            ),
        )
        self.assertIsInstance(result, R1RealizationMaterializer)
        return result

    def segment(self, start: int, stop: int) -> tuple[pd.DataFrame, pd.DataFrame]:
        return self.state.iloc[start:stop].copy(), self.mask.iloc[start:stop].copy()

    def test_01_default_factory_is_inactive_without_allocating_inputs(self) -> None:
        self.assertIsNone(create_r1_realization_materializer())
        self.assertIsNone(
            create_r1_realization_materializer(
                enabled=False,
                frozen_r1_ids=None,
                source_time=None,
                source_time_unit=None,
                provenance=None,
            )
        )

    def test_02_round13_three_segment_chain_is_exact(self) -> None:
        materializer = self.new_materializer()
        for start, stop in [(0, 1), (1, 3), (3, 5)]:
            state, mask = self.segment(start, stop)
            if (start, stop) == (1, 3):
                reversed_ids = list(reversed(self.r1_ids))
                state = state.reindex(columns=reversed_ids)
                mask = mask.reindex(columns=reversed_ids)
            materializer.append_segment(start, stop, state, mask)
        produced = materializer.finalize()

        assert_frame_equal(
            produced.effective_state,
            self.state.rename_axis(index="source_time", columns="R1_station_id"),
            check_exact=True,
        )
        assert_frame_equal(
            produced.state_identified,
            self.mask.rename_axis(index="source_time", columns="R1_station_id"),
            check_exact=True,
        )

        hook = R1EffectiveStateExportHook(
            enabled=True, callback=export_r1_effective_state_trajectory
        )
        exported = maybe_export_r1_effective_state(
            hook=hook,
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
        self.assertEqual(
            exported.trajectory.groupby("time_index", sort=True)["source_time"].first().tolist(),
            list(self.state.index),
        )
        loaded = load_validate_r1_effective_state_trajectory(
            exported.trajectory, self.r1_ids
        )
        self.assertEqual(loaded.semantic_states.shape, (5, 310))

    def test_03_round11_static_zero_and_missing_are_exact(self) -> None:
        network = self.static.loc[
            self.static["record_type"].eq("R1_NETWORK_ASSET")
        ].copy()
        values = pd.to_numeric(
            network.set_index("record_id")["effective_no_damage_network_state"],
            errors="coerce",
        ).reindex(self.r1_ids)
        state = pd.DataFrame(
            [values.to_numpy()], columns=self.r1_ids, index=["static_fixture"]
        )
        mask = pd.DataFrame(
            [values.notna().to_numpy(dtype=bool)],
            columns=self.r1_ids,
            index=["static_fixture"],
        )
        materializer = self.new_materializer(
            source_time=["static_fixture"],
            source_time_unit="static_snapshot",
            provenance=self.provenance("static_snapshot"),
        )
        materializer.append_segment(0, 1, state, mask)
        produced = materializer.finalize()
        row = produced.effective_state.iloc[0]
        identified = produced.state_identified.iloc[0]
        self.assertEqual(int(identified.sum()), 306)
        self.assertEqual(int((~identified).sum()), 4)
        self.assertEqual(int((row[identified] == 1.0).sum()), 304)
        self.assertEqual(int((row[identified] == 0.0).sum()), 2)
        self.assertEqual(sorted(row.index[identified & row.eq(0.0)]), ["306980", "309598"])
        self.assertEqual(
            sorted(row.index[~identified]),
            ["301479", "303265", "304137", "305021"],
        )
        self.assertTrue(row.loc[~identified].isna().all())

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
        loaded = load_validate_r1_effective_state_trajectory(
            exported.trajectory, self.r1_ids
        )
        semantic = loaded.semantic_states.iloc[0]
        self.assertEqual(sorted(semantic.index[semantic.eq(0.0)]), ["306980", "309598"])
        self.assertEqual(
            sorted(semantic.index[semantic.isna()]),
            ["301479", "303265", "304137", "305021"],
        )

    def test_04_segment_completeness_and_order_fail_fast(self) -> None:
        cases = []

        def missing_initial() -> None:
            m = self.new_materializer()
            state, mask = self.segment(1, 5)
            m.append_segment(1, 5, state, mask)

        cases.append(("missing_initial", missing_initial))

        def missing_middle() -> None:
            m = self.new_materializer()
            state, mask = self.segment(0, 1)
            m.append_segment(0, 1, state, mask)
            state, mask = self.segment(2, 5)
            m.append_segment(2, 5, state, mask)

        cases.append(("missing_middle", missing_middle))

        def missing_final() -> None:
            m = self.new_materializer()
            state, mask = self.segment(0, 4)
            m.append_segment(0, 4, state, mask)
            m.finalize()

        cases.append(("missing_final", missing_final))

        def overlap() -> None:
            m = self.new_materializer()
            state, mask = self.segment(0, 2)
            m.append_segment(0, 2, state, mask)
            state, mask = self.segment(1, 3)
            m.append_segment(1, 3, state, mask)

        cases.append(("overlap", overlap))

        def duplicate() -> None:
            m = self.new_materializer()
            state, mask = self.segment(0, 1)
            m.append_segment(0, 1, state, mask)
            m.append_segment(0, 1, state, mask)

        cases.append(("duplicate", duplicate))

        def out_of_order() -> None:
            m = self.new_materializer()
            state, mask = self.segment(0, 1)
            m.append_segment(0, 1, state, mask)
            state, mask = self.segment(3, 4)
            m.append_segment(3, 4, state, mask)

        cases.append(("out_of_order", out_of_order))

        def zero_length() -> None:
            m = self.new_materializer()
            m.append_segment(0, 0, self.state.iloc[0:0], self.mask.iloc[0:0])

        cases.append(("zero_length", zero_length))

        def exceeds_t() -> None:
            m = self.new_materializer()
            m.append_segment(0, 6, self.state, self.mask)

        cases.append(("exceeds_T", exceeds_t))

        for name, operation in cases:
            with self.subTest(case=name):
                with self.assertRaises(R1RealizationMaterializationError):
                    operation()

    def test_05_station_and_schema_malformed_inputs_fail_fast(self) -> None:
        state, mask = self.segment(0, 1)
        cases: list[tuple[str, object, object]] = []
        cases.append(("missing_station", state.iloc[:, :-1], mask.iloc[:, :-1]))

        unknown_state = state.copy()
        unknown_state.columns = self.r1_ids[:-1] + ["UNKNOWN_R1"]
        unknown_mask = mask.copy()
        unknown_mask.columns = self.r1_ids[:-1] + ["UNKNOWN_R1"]
        cases.append(("unknown_station", unknown_state, unknown_mask))

        duplicate_state = state.copy()
        duplicate_mask = mask.copy()
        duplicate_columns = self.r1_ids.copy()
        duplicate_columns[-1] = duplicate_columns[0]
        duplicate_state.columns = duplicate_columns
        duplicate_mask.columns = duplicate_columns
        cases.append(("duplicate_station", duplicate_state, duplicate_mask))

        mismatched_mask = mask.rename(columns={self.r1_ids[-1]: "UNKNOWN_R1"})
        cases.append(("state_mask_station_mismatch", state, mismatched_mask))
        cases.append(("state_mask_row_count", state, pd.concat([mask, mask])))

        wrong_index_mask = mask.copy()
        wrong_index_mask.index = [999]
        cases.append(("state_mask_time_mismatch", state, wrong_index_mask))
        cases.append(("unsafe_positional_state", state.to_numpy(), mask))
        cases.append(("unsafe_positional_mask", state, mask.to_numpy()))

        for name, bad_state, bad_mask in cases:
            with self.subTest(case=name):
                m = self.new_materializer()
                with self.assertRaises(R1RealizationMaterializationError):
                    m.append_segment(0, 1, bad_state, bad_mask)

        wrong_ids = self.r1_ids[:-1] + ["999999"]
        with self.assertRaises(R1RealizationMaterializationError):
            self.new_materializer(frozen_ids=wrong_ids)
        with self.assertRaises(R1RealizationMaterializationError):
            self.new_materializer(frozen_ids=self.r1_ids[:-1])

    def test_06_value_and_mask_malformed_inputs_fail_fast(self) -> None:
        base_state, base_mask = self.segment(0, 1)
        target = self.r1_ids[0]
        cases = []

        for name, value in [
            ("identified_nan", np.nan),
            ("identified_inf", np.inf),
            ("identified_negative", -0.01),
            ("identified_above_one", 1.01),
            ("ambiguous_string", "not-a-state"),
        ]:
            state = (
                base_state.astype(object).copy()
                if name == "ambiguous_string"
                else base_state.copy()
            )
            state.loc[state.index[0], target] = value
            cases.append((name, state, base_mask.copy()))

        state = base_state.copy()
        mask = base_mask.copy()
        state.loc[state.index[0], target] = 0.25
        mask.loc[mask.index[0], target] = False
        cases.append(("masked_nonzero", state, mask))

        mask = base_mask.astype(object)
        mask.loc[mask.index[0], target] = "False"
        cases.append(("nonboolean_mask", base_state.copy(), mask))

        for name, state, mask in cases:
            with self.subTest(case=name):
                m = self.new_materializer()
                with self.assertRaises(R1RealizationMaterializationError):
                    m.append_segment(0, 1, state, mask)

    def test_07_identified_zero_fractional_one_and_missing_remain_distinct(self) -> None:
        state, mask = self.segment(0, 1)
        ids = self.r1_ids[:4]
        state.loc[state.index[0], ids] = [0.0, 1.0, 0.375, 0.0]
        mask.loc[mask.index[0], ids] = [True, True, True, False]
        m = self.new_materializer()
        m.append_segment(0, 1, state, mask)
        for start, stop in [(1, 3), (3, 5)]:
            next_state, next_mask = self.segment(start, stop)
            m.append_segment(start, stop, next_state, next_mask)
        produced = m.finalize()
        row_state = produced.effective_state.iloc[0]
        row_mask = produced.state_identified.iloc[0]
        self.assertEqual(row_state.loc[ids].tolist(), [0.0, 1.0, 0.375, 0.0])
        self.assertEqual(row_mask.loc[ids].tolist(), [True, True, True, False])

    def test_08_provenance_and_time_contract_fail_fast(self) -> None:
        bad_provenance = [
            self.provenance(trajectory_scope="mc_mean"),
            self.provenance(trajectory_scope="aggregate"),
            self.provenance(realization_id=""),
            {k: v for k, v in self.provenance().items() if k != "realization_id"},
            self.provenance(source_time_unit="hours_since_event"),
        ]
        for provenance in bad_provenance:
            with self.subTest(provenance=provenance):
                with self.assertRaises(R1RealizationMaterializationError):
                    self.new_materializer(provenance=provenance)

        for source_time in [[0, 1, 1, 3, 4], [0, 2, 1, 3, 4], [0, 1, None, 3, 4]]:
            with self.subTest(source_time=source_time):
                with self.assertRaises(R1RealizationMaterializationError):
                    self.new_materializer(source_time=source_time)

        state, mask = self.segment(0, 1)
        state.index = [999]
        mask.index = [999]
        m = self.new_materializer()
        with self.assertRaises(R1RealizationMaterializationError):
            m.append_segment(0, 1, state, mask)

    def test_09_finalize_freezes_state(self) -> None:
        m = self.new_materializer()
        state, mask = self.segment(0, 5)
        m.append_segment(0, 5, state, mask)
        m.finalize()
        with self.assertRaises(R1RealizationMaterializationError):
            m.append_segment(0, 5, state, mask)
        with self.assertRaises(R1RealizationMaterializationError):
            m.finalize()

    def test_10_dependency_boundary_and_main_are_frozen(self) -> None:
        source = PATHS["materializer"].read_text(encoding="utf-8")
        tree = ast.parse(source)
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertTrue(
            roots.issubset(
                {"__future__", "dataclasses", "hashlib", "typing", "numpy", "pandas"}
            )
        )
        forbidden_tokens = [
            "keep_mask",
            "apply_source_gate",
            "connected_components",
            "networkx",
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
        for token in forbidden_tokens:
            self.assertNotIn(token.lower(), lowered)
        self.assertEqual(sha256(PATHS["main"]), EXPECTED_FROZEN_HASHES["main"])

    @classmethod
    def tearDownClass(cls) -> None:
        hashes_after = {name: sha256(path) for name, path in PATHS.items()}
        for name in EXPECTED_FROZEN_HASHES:
            if hashes_after[name] != cls.hashes_before[name]:
                raise AssertionError(f"Frozen input changed during test: {name}")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProducerMaterializationTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        summary = {
            "result": "PASS_PRODUCER_MATERIALIZATION_UNIT_VERIFIED",
            "tests": result.testsRun,
            "round13_cells": 1550,
            "round11_identified": 306,
            "round11_missing": 4,
            "segment_completeness_cases": 8,
            "station_schema_cases": 10,
            "value_mask_cases": 7,
            "scientific_runs": 0,
            "main_model_unchanged": True,
        }
        print("\nPRODUCER_MATERIALIZATION_TEST_SUMMARY=" + json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
