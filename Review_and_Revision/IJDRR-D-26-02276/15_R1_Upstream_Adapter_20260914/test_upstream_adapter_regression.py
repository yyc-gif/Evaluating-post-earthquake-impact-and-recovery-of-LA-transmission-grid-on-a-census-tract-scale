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

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROUND14))

from r1_effective_state_adapter import (  # noqa: E402
    R1EffectiveStateAdapterError,
    adapt_native_r1_effective_state_envelope,
    load_native_r1_effective_state_csv,
    native_schema_sha256,
)
from service_layer_interface import (  # noqa: E402
    ATTACHMENT_C,
    evaluate_service_layer_trajectory,
    load_validate_r1_effective_state_trajectory,
)


PATHS = {
    "real_upstream": ROUND11 / "SERVICE_NODE_BASELINE_QA.csv",
    "t0_nodes": ROUND11 / "SERVICE_NODE_BASELINE_QA.csv",
    "nodes": ROUND10 / "SCE_SERVICE_NODES_196.csv",
    "attachments": ROUND10 / "SERVICE_UPSTREAM_ATTACHMENT_LEDGER.csv",
    "w1": ROUND10 / "SCE_TRACT_SERVICE_W1.csv",
    "tract_metadata": ROUND10 / "SERVICE_LAYER_COVERAGE_QA.csv",
    "original_trajectory": ROUND13 / "EXTERNAL_R1_EFFECTIVE_STATE_TRAJECTORY.csv",
    "golden_service": ROUND13 / "SERVICE_NODE_TIME_QA.csv",
    "golden_tract": ROUND13 / "TRACT_TIME_INTERVAL_QA.csv",
    "native_fixture": HERE / "GOLDEN_NATIVE_SCHEMA_FIXTURE.csv",
    "production_module": ROUND14 / "service_layer_interface.py",
    "adapter_module": HERE / "r1_effective_state_adapter.py",
    "adapter_contract": HERE / "R1_UPSTREAM_ADAPTER_CONTRACT.md",
}

EXPECTED_HASHES = {
    "real_upstream": "a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384",
    "t0_nodes": "a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384",
    "nodes": "ccf9e08b40a0df1326e7eb9f62addd92d9fa348f65a43dd4afc6a743845f2080",
    "attachments": "b1a7ad8e6f162bed06fb88694a0393aa0d1fc7d4ef515ba628ede242e809ed9e",
    "w1": "a21b583338a4583e2362aba70667ac8c443abe0cf3a732b98f022175cf4f6221",
    "tract_metadata": "4658c4f439a1ae41d77a5d5d14e6a8cbb950f1f71f123f2edd9190fa7a992f8b",
    "original_trajectory": "b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6",
    "golden_service": "8d7b55f660717753c1a715a4792dde2f429faf4d42b567a03eb68ec2aa6a95cb",
    "golden_tract": "5cf3fb759bea519f6f3fbaee4cdffb422261b1a9a4157c296c8be7bd58c3009d",
    "native_fixture": "b52605805f02cf12a959df50bee2fa7a34f5f1d6e8333015a79d74b4a2965249",
    "production_module": "d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514",
}
TOLERANCE = 1e-12


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


def bool_value(values: pd.Series) -> pd.Series:
    return values.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


def canonical_standard_hash(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(
        index=False,
        lineterminator="\n",
        float_format="%.17g",
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def serialize_round13_to_native_envelope(original: pd.DataFrame) -> pd.DataFrame:
    """Test-only serializer; it changes representation and no state or mask."""

    identified = bool_value(original["state_identified"])
    state_text = pd.to_numeric(original["effective_state_value"]).map(
        lambda value: format(float(value), ".17g")
    )
    return pd.DataFrame(
        {
            "native_snapshot_time_index": pd.to_numeric(original["time_index"]),
            "source_time": pd.to_numeric(original["time_index"]),
            "source_time_unit": "dimensionless_qa_index",
            "record_type": "R1_NETWORK_ASSET",
            "record_id": original["R1_station_id"].astype(str).str.strip(),
            "effective_no_damage_network_state": state_text.where(identified, ""),
        }
    )


class UpstreamAdapterRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hashes_before = {name: sha256(path) for name, path in PATHS.items()}
        for name, expected in EXPECTED_HASHES.items():
            if cls.hashes_before[name] != expected:
                raise AssertionError(
                    f"Frozen hash mismatch for {name}: {cls.hashes_before[name]} != {expected}"
                )

        cls.real = read_csv(PATHS["real_upstream"], dtype={"record_id": str})
        cls.t0_nodes = cls.real.copy(deep=True)
        cls.nodes = read_csv(PATHS["nodes"], dtype={"upstream_R1_station_id": str})
        cls.attachments = read_csv(
            PATHS["attachments"], dtype={"selected_upstream_R1_id": str}
        )
        cls.w1 = read_csv(PATHS["w1"], dtype={"tract_id": str})
        cls.tract_metadata = read_csv(PATHS["tract_metadata"], dtype={"tract_id": str})
        cls.original = read_csv(
            PATHS["original_trajectory"], dtype={"R1_station_id": str}
        )
        cls.fixture = read_csv(PATHS["native_fixture"], dtype={"record_id": str})
        cls.golden_service = read_csv(
            PATHS["golden_service"],
            dtype={"service_node_id": str, "upstream_R1_id": str},
        )
        cls.golden_tract = read_csv(PATHS["golden_tract"], dtype={"tract_id": str})

        network_rows = cls.t0_nodes.loc[
            cls.t0_nodes["record_type"].eq("R1_NETWORK_ASSET")
        ].copy()
        cls.r1_ids = sorted(network_rows["record_id"].astype(str).unique())
        cls.service_ids = sorted(cls.nodes["service_node_id"].astype(str).unique())
        cls.expected_mask = (
            pd.to_numeric(
                network_rows.set_index("record_id")["effective_no_damage_network_state"],
                errors="coerce",
            )
            .reindex(cls.r1_ids)
            .notna()
        )
        cls.restored = adapt_native_r1_effective_state_envelope(cls.fixture, cls.r1_ids)
        cls.restored_hash = canonical_standard_hash(cls.restored)
        cls.schema_hash = native_schema_sha256()

    def evaluate_restored(self):
        return evaluate_service_layer_trajectory(
            self.restored,
            self.attachments,
            self.w1,
            self.tract_metadata[["tract_id", "population"]],
            self.r1_ids,
            self.service_ids,
            expected_identified_mask=self.expected_mask,
            tolerance=TOLERANCE,
        )

    def test_01_real_existing_artifact_schema_acceptance_only(self) -> None:
        real_before = self.real.copy(deep=True)
        adapted = load_native_r1_effective_state_csv(
            safe(PATHS["real_upstream"]),
            self.r1_ids,
            time_index=0,
            source_time="reference_no_damage_snapshot",
            source_time_unit="static_snapshot",
        )
        self.assertEqual(len(adapted), 310)
        validated = load_validate_r1_effective_state_trajectory(
            adapted,
            self.r1_ids,
            expected_identified_mask=self.expected_mask,
        )
        self.assertEqual(int(validated.identified_mask.to_numpy().sum()), 306)
        self.assertEqual(int(validated.semantic_states.isna().to_numpy().sum()), 4)
        state = validated.semantic_states.iloc[0]
        self.assertEqual(int(state.eq(1.0).sum()), 304)
        self.assertEqual(int(state.eq(0.0).sum()), 2)
        self.assertEqual(sorted(state.index[state.eq(0.0)]), ["306980", "309598"])
        self.assertEqual(
            sorted(state.index[state.isna()]),
            ["301479", "303265", "304137", "305021"],
        )
        assert_frame_equal(self.real, real_before, check_exact=True)

    def test_02_test_serializer_matches_checked_in_native_fixture(self) -> None:
        generated = serialize_round13_to_native_envelope(self.original)
        assert_frame_equal(generated, self.fixture, check_exact=True, check_dtype=False)
        self.assertEqual(len(generated), 1550)

    def test_03_native_round_trip_restores_all_state_and_mask_cells(self) -> None:
        original = self.original.copy(deep=True)
        original["R1_station_id"] = original["R1_station_id"].astype(str).str.strip()
        original["time_index"] = pd.to_numeric(original["time_index"])
        original["effective_state_value"] = pd.to_numeric(original["effective_state_value"])
        original["state_identified"] = bool_value(original["state_identified"])
        order = {station_id: position for position, station_id in enumerate(self.r1_ids)}
        original["_station_order"] = original["R1_station_id"].map(order)
        original = original.sort_values(["time_index", "_station_order"], kind="stable")
        original = original.drop(columns="_station_order").reset_index(drop=True)

        self.assertEqual(len(self.restored), 1550)
        self.assertTrue(
            np.array_equal(self.restored["time_index"], original["time_index"])
        )
        self.assertTrue(
            np.array_equal(self.restored["R1_station_id"], original["R1_station_id"])
        )
        self.assertTrue(
            np.array_equal(
                self.restored["effective_state_value"], original["effective_state_value"]
            )
        )
        self.assertTrue(
            np.array_equal(self.restored["state_identified"], original["state_identified"])
        )
        self.assertTrue(
            self.restored["source_time_unit"].eq("dimensionless_qa_index").all()
        )
        self.assertTrue(
            np.array_equal(self.restored["source_time"], original["time_index"])
        )
        load_validate_r1_effective_state_trajectory(
            self.restored,
            self.r1_ids,
            expected_identified_mask=self.expected_mask,
        )

    def test_04_production_golden_regression_through_adapter(self) -> None:
        result = self.evaluate_restored()

        golden_service = self.golden_service.copy()
        golden_service["observed_service_state"] = pd.to_numeric(
            golden_service["observed_service_state"], errors="coerce"
        )
        golden_service_wide = golden_service.pivot(
            index="time_index",
            columns="service_node_id",
            values="observed_service_state",
        ).reindex(index=result.service_trajectory.index, columns=self.service_ids)
        self.assertEqual(result.service_trajectory.size, 980)
        self.assertTrue(
            np.array_equal(
                result.service_trajectory.isna().to_numpy(),
                golden_service_wide.isna().to_numpy(),
            )
        )
        self.assertTrue(
            np.allclose(
                result.service_trajectory.to_numpy(),
                golden_service_wide.to_numpy(),
                atol=TOLERANCE,
                rtol=0.0,
                equal_nan=True,
            )
        )

        production_tract = result.tract_intervals.set_index(
            ["time_index", "tract_id"]
        ).sort_index()
        golden_tract = self.golden_tract.set_index(["time_index", "tract_id"]).sort_index()
        self.assertEqual(len(production_tract), 4085)
        for production_column, golden_column in [
            ("lower", "observed_lower"),
            ("upper", "observed_upper"),
            ("width", "observed_interval_width"),
        ]:
            self.assertTrue(
                np.allclose(
                    production_tract[production_column],
                    pd.to_numeric(golden_tract[golden_column]),
                    atol=TOLERANCE,
                    rtol=0.0,
                )
            )

        golden_aggregate = []
        for time_index, block in golden_tract.reset_index().groupby(
            "time_index", sort=True
        ):
            population = pd.to_numeric(block["population"])
            golden_aggregate.append(
                {
                    "time_index": time_index,
                    "population_weighted_lower": np.average(
                        pd.to_numeric(block["observed_lower"]), weights=population
                    ),
                    "population_weighted_upper": np.average(
                        pd.to_numeric(block["observed_upper"]), weights=population
                    ),
                    "population_weighted_width": np.average(
                        pd.to_numeric(block["observed_interval_width"]), weights=population
                    ),
                }
            )
        golden_aggregate = pd.DataFrame(golden_aggregate).set_index("time_index")
        production_aggregate = result.aggregate_intervals.set_index("time_index")
        self.assertEqual(len(production_aggregate), 5)
        self.assertTrue(
            np.allclose(
                production_aggregate,
                golden_aggregate,
                atol=TOLERANCE,
                rtol=0.0,
            )
        )

        class_c_ids = self.attachments.loc[
            self.attachments["attachment_class"].eq(ATTACHMENT_C), "service_node_id"
        ].tolist()
        self.assertEqual(len(class_c_ids), 12)
        self.assertTrue(result.service_trajectory[class_c_ids].isna().all().all())
        t0 = production_tract.xs(0, level="time_index")
        t4 = production_tract.xs(4, level="time_index")
        self.assertTrue(np.array_equal(t0.to_numpy(), t4.to_numpy(), equal_nan=True))

    def test_05_run1_run2_exact_determinism(self) -> None:
        restored_run2 = adapt_native_r1_effective_state_envelope(
            self.fixture.copy(deep=True), self.r1_ids
        )
        assert_frame_equal(self.restored, restored_run2, check_exact=True)
        run1 = self.evaluate_restored()
        run2 = evaluate_service_layer_trajectory(
            restored_run2,
            self.attachments,
            self.w1,
            self.tract_metadata[["tract_id", "population"]],
            self.r1_ids,
            self.service_ids,
            expected_identified_mask=self.expected_mask,
            tolerance=TOLERANCE,
        )
        assert_frame_equal(run1.network_trajectory, run2.network_trajectory, check_exact=True)
        assert_frame_equal(run1.network_identified_mask, run2.network_identified_mask, check_exact=True)
        assert_frame_equal(run1.service_trajectory, run2.service_trajectory, check_exact=True)
        assert_frame_equal(run1.tract_intervals, run2.tract_intervals, check_exact=True)
        assert_frame_equal(run1.aggregate_intervals, run2.aggregate_intervals, check_exact=True)

    def test_06_fail_fast_native_contract_cases(self) -> None:
        first_time = self.fixture["native_snapshot_time_index"].min()
        first_id = self.r1_ids[0]

        missing_station = self.fixture.drop(
            self.fixture[
                self.fixture["native_snapshot_time_index"].eq(first_time)
                & self.fixture["record_id"].eq(first_id)
            ].index
        )
        with self.assertRaises(R1EffectiveStateAdapterError):
            adapt_native_r1_effective_state_envelope(missing_station, self.r1_ids)

        unknown_station = self.fixture.copy(deep=True)
        target = unknown_station[
            unknown_station["native_snapshot_time_index"].eq(first_time)
            & unknown_station["record_id"].eq(first_id)
        ].index[0]
        unknown_station.loc[target, "record_id"] = "999999"
        with self.assertRaises(R1EffectiveStateAdapterError):
            adapt_native_r1_effective_state_envelope(unknown_station, self.r1_ids)

        duplicate_station = pd.concat(
            [self.fixture, self.fixture.loc[[target]]], ignore_index=True
        )
        with self.assertRaises(R1EffectiveStateAdapterError):
            adapt_native_r1_effective_state_envelope(duplicate_station, self.r1_ids)

        blocks = {
            time: block.copy()
            for time, block in self.fixture.groupby("native_snapshot_time_index", sort=False)
        }
        unordered = pd.concat(
            [blocks[0], blocks[2], blocks[1], blocks[3], blocks[4]], ignore_index=True
        )
        with self.assertRaises(R1EffectiveStateAdapterError):
            adapt_native_r1_effective_state_envelope(unordered, self.r1_ids)

        duplicate_block = pd.concat(
            [blocks[0], blocks[1], blocks[0], blocks[2], blocks[3], blocks[4]],
            ignore_index=True,
        )
        with self.assertRaises(R1EffectiveStateAdapterError):
            adapt_native_r1_effective_state_envelope(duplicate_block, self.r1_ids)

        out_of_range = self.fixture.copy(deep=True)
        out_of_range.loc[target, "effective_no_damage_network_state"] = "1.01"
        with self.assertRaises(R1EffectiveStateAdapterError):
            adapt_native_r1_effective_state_envelope(out_of_range, self.r1_ids)

        ambiguous_missing = self.fixture.copy(deep=True)
        ambiguous_missing.loc[target, "effective_no_damage_network_state"] = "NA"
        with self.assertRaises(R1EffectiveStateAdapterError):
            adapt_native_r1_effective_state_envelope(ambiguous_missing, self.r1_ids)

        nonnumeric = self.fixture.copy(deep=True)
        nonnumeric.loc[target, "effective_no_damage_network_state"] = "not-a-number"
        with self.assertRaises(R1EffectiveStateAdapterError):
            adapt_native_r1_effective_state_envelope(nonnumeric, self.r1_ids)

        missing_id_mapping = self.fixture.drop(columns="record_id")
        with self.assertRaises(R1EffectiveStateAdapterError):
            adapt_native_r1_effective_state_envelope(missing_id_mapping, self.r1_ids)

    def test_07_adapter_dependency_boundary(self) -> None:
        tree = ast.parse(Path(safe(PATHS["adapter_module"])).read_text(encoding="utf-8"))
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
            "pathlib",
            "typing",
            "numpy",
            "pandas",
        }
        self.assertTrue(imported_roots.issubset(allowed), imported_roots - allowed)

    @classmethod
    def tearDownClass(cls) -> None:
        hashes_after = {name: sha256(path) for name, path in PATHS.items()}
        if hashes_after != cls.hashes_before:
            raise AssertionError("Frozen input, fixture, golden, or production file changed")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(UpstreamAdapterRegression)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        summary = {
            "result": "PASS_UPSTREAM_ADAPTER_CONTRACT_VERIFIED",
            "tests": result.testsRun,
            "negative_contract_cases": 9,
            "real_artifact_rows": 506,
            "real_r1_rows_accepted": 310,
            "real_r1_identified": 306,
            "real_r1_missing": 4,
            "round_trip_state_mask_cells": 1550,
            "service_elements_compared": 980,
            "tract_rows_compared": 4085,
            "aggregate_time_indices_compared": 5,
            "native_schema_sha256": UpstreamAdapterRegression.schema_hash,
            "adapter_restored_trajectory_sha256": UpstreamAdapterRegression.restored_hash,
            "adapter_module_sha256": sha256(PATHS["adapter_module"]),
            "adapter_contract_sha256": sha256(PATHS["adapter_contract"]),
            "frozen_hashes_unchanged": True,
        }
        print("\nADAPTER_REGRESSION_SUMMARY=" + json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
