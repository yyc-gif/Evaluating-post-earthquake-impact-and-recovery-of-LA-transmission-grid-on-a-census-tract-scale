from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("Formal_Experiment_20260923")
NEW = ROOT / "Stage 7 Output_SOVI_Harmonized"


def test_full_domain_separates_service_coverage_from_residential_typology():
    full = pd.read_csv(NEW / "stage7_full_domain_tract_status.csv", dtype={"tract_id": str})
    clustered = pd.read_csv(NEW / "clusters_labels_final.csv", dtype={"tract_id": str})
    old = pd.read_csv(ROOT / "Stage 7 Output_expanded" / "clusters_labels_final.csv", dtype={"tract_id": str})
    stage5 = pd.read_csv(ROOT / "Stage 5 Output_expanded" / "tract_kpis_2pc50.csv", dtype={"tract_id": str})
    frozen_sovi = pd.read_csv(
        "Data/LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv",
        dtype={"TRACTFIPS": str},
    )
    frozen_sovi["tract_id"] = frozen_sovi.TRACTFIPS.str.lstrip("0")
    assert len(full) == 2315 and full.tract_id.is_unique
    assert full[["SOVI_SCORE", "T50", "T80", "Init_Supply"]].notna().all().all()
    assert np.allclose(
        full.set_index("tract_id").sort_index().SOVI_SCORE.to_numpy(),
        frozen_sovi.set_index("tract_id").loc[sorted(full.tract_id), "SOVI_SCORE"].to_numpy(),
    )
    assert len(clustered) == len(old) == 2291
    assert set(clustered.tract_id) == set(old.tract_id)
    assert full.set_index("tract_id").T80.sort_index().equals(stage5.set_index("tract_id").T80.sort_index())
    assert np.array_equal(
        clustered.set_index("tract_id").sort_index().T80.to_numpy(),
        old.set_index("tract_id").sort_index().T80.to_numpy(),
    )
    status = full.typology_status.value_counts().to_dict()
    assert status == {"residential_typology_eligible": 2291,
                      "zero_housing_units_ratio_undefined": 23,
                      "zero_formal_population": 1}
    structural = full[full.typology_status.eq("zero_housing_units_ratio_undefined")]
    assert structural.Housing_Units_Total.eq(0).all()
    assert structural.Pre_1970_Ratio.isna().all()
    group_quarters = structural[structural.E_TOTPOP.gt(0)]
    assert len(group_quarters) == 7
    assert group_quarters.E_GROUPQ.equals(group_quarters.E_TOTPOP)
