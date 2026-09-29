"""Update only the indexed presentation rows changed by the co-author figure pass."""
from __future__ import annotations

import hashlib
from pathlib import Path
import pandas as pd

from la_grid.paths import REPO_ROOT as ROOT

INDEX = ROOT / "results" / "figures" / "FIGURE_INDEX.csv"
FIG = ROOT / "results" / "figures"

UPDATES = {
    "vis_source_reliability_station_map_2pc50": (
        "Spatial source-terminal reliability and alternative-route gain",
        "Supplement",
        "src/la_grid/plotting/render_source_reliability_figures.py",
    ),
    "vis_source_reliability_full_vs_best_path_2pc50": (
        "Full-network versus fixed best-path reliability cross-check",
        "Supplement",
        "src/la_grid/plotting/render_source_reliability_figures.py",
    ),
    "vis_source_reliability_dynamic_redundancy_2pc50": (
        "Time-varying alternative-route contribution during recovery",
        "Main",
        "src/la_grid/plotting/render_source_reliability_figures.py",
    ),
    "vis_source_gate_connected_vs_facility_loading": (
        "SCE planning loading among retained source-reachable facilities",
        "Supplement",
        "src/la_grid/plotting/render_source_gate_electrical_adequacy_figure.py",
    ),
    "vis_sce_capacity_supported_sensitivity": (
        "SCE-supported planning-capacity sensitivity",
        "Supplement",
        "src/la_grid/plotting/render_sce_capacity_sensitivity_figure.py",
    ),
    "Candidate_S18_Equity_Efficiency_Tradeoff": (
        "2pc50 efficiency, Q4 burden, group separation and Gini trade-off",
        "Supplement",
        "src/la_grid/plotting/render_efficiency_distribution_tradeoff.py",
    ),
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    table = pd.read_csv(INDEX)
    required = {
        "file","format","scientific_content","current_status","main_or_supplement",
        "source_authority","source_path","generator","sha256_or_lfs_oid",
        "include_in_final_figure_collection","notes",
    }
    if not required.issubset(table.columns):
        raise ValueError("FIGURE_INDEX schema changed")
    for stem, (content, role, generator) in UPDATES.items():
        for ext in (".png", ".pdf"):
            name = stem + ext
            path = FIG / name
            if not path.is_file():
                raise FileNotFoundError(path)
            mask = table["file"].eq(name)
            if mask.sum() != 1:
                raise ValueError(f"Expected one FIGURE_INDEX row for {name}; got {int(mask.sum())}")
            table.loc[mask, "scientific_content"] = content
            table.loc[mask, "current_status"] = "current final candidate"
            table.loc[mask, "main_or_supplement"] = role
            table.loc[mask, "source_authority"] = "Frozen scientific result tables; presentation-only renderer"
            table.loc[mask, "source_path"] = f"results/figures/{name}"
            table.loc[mask, "generator"] = generator
            table.loc[mask, "sha256_or_lfs_oid"] = digest(path)
            table.loc[mask, "include_in_final_figure_collection"] = True
            table.loc[mask, "notes"] = "Updated from accepted co-author presentation feedback; scientific inputs unchanged."
    table.to_csv(INDEX, index=False)


if __name__ == "__main__":
    main()
