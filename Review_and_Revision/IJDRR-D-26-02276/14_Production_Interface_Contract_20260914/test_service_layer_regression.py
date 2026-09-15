from __future__ import annotations

import ast
from pathlib import Path
import hashlib
import json
import sys
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from service_layer_interface import (  # noqa: E402
    ATTACHMENT_A,
    ATTACHMENT_B,
    ATTACHMENT_C,
    ServiceLayerContractError,
    evaluate_service_layer_trajectory,
    load_validate_r1_effective_state_trajectory,
    validate_service_attachment_ledger,
    validate_w1,
)


ROOT = HERE.parents[2]
REVIEW = ROOT / "Review_and_Revision" / "IJDRR-D-26-02276"
ROUND10 = REVIEW / "10_SCE_ServiceLayer_Architecture_20260914"
ROUND11 = REVIEW / "11_TwoLayer_Static_QA_20260914"
ROUND13 = REVIEW / "13_TimeIndexed_Interface_QA_20260914"

PATHS = {
    "nodes": ROUND10 / "SCE_SERVICE_NODES_196.csv",
    "attachments": ROUND10 / "SERVICE_UPSTREAM_ATTACHMENT_LEDGER.csv",
    "w1": ROUND10 / "SCE_TRACT_SERVICE_W1.csv",
    "tract_metadata": ROUND10 / "SERVICE_LAYER_COVERAGE_QA.csv",
    "t0_nodes": ROUND11 / "SERVICE_NODE_BASELINE_QA.csv",
    "t0_tracts": ROUND11 / "TRACT_BASELINE_INTERVAL_QA.csv",
    "source_ledger": REVIEW / "08_UtilitySpecific_SetC_20260914" / "R1_SERVICE_ROLE_CROSSWALK.csv",
    "trajectory": ROUND13 / "EXTERNAL_R1_EFFECTIVE_STATE_TRAJECTORY.csv",
    "golden_service": ROUND13 / "SERVICE_NODE_TIME_QA.csv",
    "golden_tract": ROUND13 / "TRACT_TIME_INTERVAL_QA.csv",
}

EXPECTED_FILE_HASHES = {
    "attachments": "b1a7ad8e6f162bed06fb88694a0393aa0d1fc7d4ef515ba628ede242e809ed9e",
    "w1": "a21b583338a4583e2362aba70667ac8c443abe0cf3a732b98f022175cf4f6221",
    "tract_metadata": "4658c4f439a1ae41d77a5d5d14e6a8cbb950f1f71f123f2edd9190fa7a992f8b",
    "t0_nodes": "a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384",
    "t0_tracts": "e285c9bbc8a1ecb9dd7057060ef4f5453edea42f70ffb4b7d42d9c0975e3ed9a",
    "trajectory": "b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6",
    "golden_service": "8d7b55f660717753c1a715a4792dde2f429faf4d42b567a03eb68ec2aa6a95cb",
    "golden_tract": "5cf3fb759bea519f6f3fbaee4cdffb422261b1a9a4157c296c8be7bd58c3009d",
}
EXPECTED_SOURCE_HASH = "c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3"
EXPECTED_R1_ID_HASH = "d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5"
EXPECTED_SERVICE_ID_HASH = "1c2533ea1ba4efd7894910e49c322654c90ec0eca6047908249a4c6e1b5d2f46"
TOL = 1e-12


def safe(path: Path) -> str:
    value = str(path)
    return value if value.startswith("\\\\?\\") else "\\\\?\\" + value


def read(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(safe(path), keep_default_na=False, **kwargs)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(safe(path), "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bool_value(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


class ProductionInterfaceRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hashes_before = {name: sha256(path) for name, path in PATHS.items()}
        for name, expected in EXPECTED_FILE_HASHES.items():
            if cls.hashes_before[name] != expected:
                raise AssertionError(
                    f"Golden hash mismatch for {name}: {cls.hashes_before[name]} != {expected}"
                )

        cls.nodes = read(PATHS["nodes"], dtype={"upstream_R1_station_id": str})
        cls.attachments = read(
            PATHS["attachments"], dtype={"selected_upstream_R1_id": str}
        )
        cls.w1 = read(PATHS["w1"], dtype={"tract_id": str})
        cls.tract_metadata = read(PATHS["tract_metadata"], dtype={"tract_id": str})
        cls.t0_nodes = read(PATHS["t0_nodes"], dtype={"record_id": str})
        cls.source_ledger = read(PATHS["source_ledger"], dtype={"station_id": str})
        cls.trajectory = read(PATHS["trajectory"], dtype={"R1_station_id": str})
        cls.golden_service = read(
            PATHS["golden_service"], dtype={"service_node_id": str, "upstream_R1_id": str}
        )
        cls.golden_tract = read(PATHS["golden_tract"], dtype={"tract_id": str})

        cls.r1_ids = sorted(
            cls.t0_nodes.loc[
                cls.t0_nodes["record_type"].eq("R1_NETWORK_ASSET"), "record_id"
            ].unique()
        )
        cls.service_ids = sorted(cls.nodes["service_node_id"].unique())
        cls.expected_mask = (
            pd.to_numeric(
                cls.t0_nodes.loc[
                    cls.t0_nodes["record_type"].eq("R1_NETWORK_ASSET")
                ].set_index("record_id")["effective_no_damage_network_state"],
                errors="coerce",
            )
            .reindex(cls.r1_ids)
            .notna()
        )

        r1_hash = hashlib.sha256(("\n".join(cls.r1_ids) + "\n").encode()).hexdigest()
        service_hash = hashlib.sha256(
            ("\n".join(cls.service_ids) + "\n").encode()
        ).hexdigest()
        if r1_hash != EXPECTED_R1_ID_HASH or service_hash != EXPECTED_SERVICE_ID_HASH:
            raise AssertionError("Frozen R1 or service ID hash mismatch")

        source_ids = sorted(
            cls.source_ledger.loc[
                cls.source_ledger["SOURCE_SCENARIO_REFERENCE"].map(bool_value), "station_id"
            ]
        )
        source_hash = hashlib.sha256(("\n".join(source_ids) + "\n").encode()).hexdigest()
        if len(source_ids) != 21 or source_hash != EXPECTED_SOURCE_HASH:
            raise AssertionError("Frozen source-scenario identity mismatch")

        canonical_population = "".join(
            f"{row.tract_id},{float(row.population):.15g}\n"
            for row in cls.tract_metadata.sort_values("tract_id").itertuples(index=False)
        )
        cls.tract_population_hash = hashlib.sha256(
            canonical_population.encode("utf-8")
        ).hexdigest()

    def evaluate(self):
        return evaluate_service_layer_trajectory(
            self.trajectory,
            self.attachments,
            self.w1,
            self.tract_metadata[["tract_id", "population"]],
            self.r1_ids,
            self.service_ids,
            expected_identified_mask=self.expected_mask,
            tolerance=TOL,
        )

    def test_01_golden_regression_all_elements(self) -> None:
        w1_before = self.w1.copy(deep=True)
        attachment_before = self.attachments.copy(deep=True)
        result = self.evaluate()

        golden_service = self.golden_service.copy()
        golden_service["observed_service_state"] = pd.to_numeric(
            golden_service["observed_service_state"], errors="coerce"
        )
        golden_service_wide = golden_service.pivot(
            index="time_index", columns="service_node_id", values="observed_service_state"
        ).reindex(index=result.service_trajectory.index, columns=self.service_ids)
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
                atol=TOL,
                rtol=0.0,
                equal_nan=True,
            )
        )
        self.assertEqual(result.service_trajectory.size, 980)

        production_tract = result.tract_intervals.set_index(["time_index", "tract_id"]).sort_index()
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
                    atol=TOL,
                    rtol=0.0,
                ),
                production_column,
            )

        golden_aggregate = []
        for time_index, block in golden_tract.reset_index().groupby("time_index", sort=True):
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
        self.assertTrue(
            np.allclose(
                production_aggregate,
                golden_aggregate,
                atol=TOL,
                rtol=0.0,
            )
        )

        class_c_ids = set(
            self.attachments.loc[
                self.attachments["attachment_class"].eq(ATTACHMENT_C), "service_node_id"
            ]
        )
        self.assertEqual(len(class_c_ids), 12)
        self.assertTrue(result.service_trajectory[list(class_c_ids)].isna().all().all())
        widths = production_tract["width"].unstack("time_index")
        self.assertTrue(widths.eq(widths.iloc[:, 0], axis="index").all().all())
        self.assertTrue(
            np.array_equal(
                result.network_trajectory.iloc[0].to_numpy(),
                result.network_trajectory.iloc[-1].to_numpy(),
                equal_nan=True,
            )
        )
        self.assertTrue(
            np.array_equal(
                result.service_trajectory.iloc[0].to_numpy(),
                result.service_trajectory.iloc[-1].to_numpy(),
                equal_nan=True,
            )
        )
        t0 = production_tract.xs(0, level="time_index")
        t4 = production_tract.xs(4, level="time_index")
        self.assertTrue(np.array_equal(t0.to_numpy(), t4.to_numpy(), equal_nan=True))
        assert_frame_equal(self.w1, w1_before, check_exact=True)
        assert_frame_equal(self.attachments, attachment_before, check_exact=True)

    def test_02_run1_run2_exact_determinism(self) -> None:
        run1 = self.evaluate()
        run2 = self.evaluate()
        assert_frame_equal(run1.network_trajectory, run2.network_trajectory, check_exact=True)
        assert_frame_equal(run1.network_identified_mask, run2.network_identified_mask, check_exact=True)
        assert_frame_equal(run1.service_trajectory, run2.service_trajectory, check_exact=True)
        assert_frame_equal(run1.tract_intervals, run2.tract_intervals, check_exact=True)
        assert_frame_equal(run1.aggregate_intervals, run2.aggregate_intervals, check_exact=True)

    def test_03_fixture_changes_only_center_and_mesa(self) -> None:
        validated = load_validate_r1_effective_state_trajectory(
            self.trajectory, self.r1_ids, expected_identified_mask=self.expected_mask
        )
        t0_values = validated.serialized_values.iloc[0]
        for time_index, row in validated.serialized_values.iterrows():
            non_targets = sorted(set(self.r1_ids) - {"300232", "301541"})
            self.assertTrue(np.array_equal(row[non_targets], t0_values[non_targets]))
        self.assertEqual(
            validated.serialized_values[["300232", "301541"]].to_numpy().tolist(),
            [[1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0], [1.0, 1.0]],
        )

    def test_04_fail_fast_negative_contract_cases(self) -> None:
        missing_id = self.trajectory.drop(
            self.trajectory[
                self.trajectory["time_index"].eq(0)
                & self.trajectory["R1_station_id"].eq(self.r1_ids[0])
            ].index
        )
        with self.assertRaises(ServiceLayerContractError):
            load_validate_r1_effective_state_trajectory(
                missing_id, self.r1_ids, self.expected_mask
            )

        duplicate_id = pd.concat([self.trajectory, self.trajectory.iloc[[0]]], ignore_index=True)
        with self.assertRaises(ServiceLayerContractError):
            load_validate_r1_effective_state_trajectory(
                duplicate_id, self.r1_ids, self.expected_mask
            )

        unknown_attachment = self.attachments.copy(deep=True)
        a_index = unknown_attachment[unknown_attachment["attachment_class"].eq(ATTACHMENT_A)].index[0]
        unknown_attachment.loc[a_index, "selected_upstream_R1_id"] = "999999"
        with self.assertRaises(ServiceLayerContractError):
            validate_service_attachment_ledger(
                unknown_attachment, self.service_ids, self.r1_ids
            )

        multiple_attachment = self.attachments.copy(deep=True)
        multiple_attachment.loc[a_index, "selected_upstream_R1_id"] = "300232|301541"
        with self.assertRaises(ServiceLayerContractError):
            validate_service_attachment_ledger(
                multiple_attachment, self.service_ids, self.r1_ids
            )

        invalid_w1 = self.w1.copy(deep=True)
        first_service = self.service_ids[0]
        invalid_w1.loc[0, first_service] = float(invalid_w1.loc[0, first_service]) + 0.1
        with self.assertRaises(ServiceLayerContractError):
            validate_w1(invalid_w1, self.service_ids)

        out_of_range = self.trajectory.copy(deep=True)
        out_of_range["effective_state_value"] = out_of_range["effective_state_value"].astype(float)
        out_of_range.loc[0, "effective_state_value"] = 1.01
        with self.assertRaises(ServiceLayerContractError):
            load_validate_r1_effective_state_trajectory(
                out_of_range, self.r1_ids, self.expected_mask
            )

        class_c_attachment = self.attachments.copy(deep=True)
        c_index = class_c_attachment[
            class_c_attachment["attachment_class"].eq(ATTACHMENT_C)
        ].index[0]
        class_c_attachment.loc[c_index, "selected_upstream_R1_id"] = "300232"
        with self.assertRaises(ServiceLayerContractError):
            validate_service_attachment_ledger(
                class_c_attachment, self.service_ids, self.r1_ids
            )

    def test_05_production_module_dependency_boundary(self) -> None:
        module_path = HERE / "service_layer_interface.py"
        tree = ast.parse(Path(safe(module_path)).read_text(encoding="utf-8"))
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
        self.assertTrue(imported_roots.issubset({"__future__", "dataclasses", "re", "typing", "numpy", "pandas"}))

    @classmethod
    def tearDownClass(cls) -> None:
        hashes_after = {name: sha256(path) for name, path in PATHS.items()}
        if hashes_after != cls.hashes_before:
            raise AssertionError("Frozen fixture or golden input changed during regression")
if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProductionInterfaceRegression)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        summary = {
            "tests": result.testsRun,
            "negative_contract_cases": 7,
            "service_elements_compared": 980,
            "tract_rows_compared": 4085,
            "aggregate_time_indices_compared": 5,
            "tract_population_hash_sha256": ProductionInterfaceRegression.tract_population_hash,
            "frozen_hashes_unchanged": True,
            "result": "PASS_PRODUCTION_INTERFACE_CONTRACT_FROZEN",
        }
        print("\nREGRESSION_SUMMARY=" + json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
