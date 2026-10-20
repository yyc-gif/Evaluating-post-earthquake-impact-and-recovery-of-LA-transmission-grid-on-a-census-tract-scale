"""Compare a freshly downloaded CDC 2022 California tract CSV with retained data.

The official CSV is a read-only external input at data/external_validation/raw;
this script never imputes SVI or changes any frozen tract assignments.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


from la_grid.paths import REPO_ROOT as ROOT
LOCAL = ROOT / "Data/California.csv"
OFFICIAL = ROOT / "data/external_validation/raw/CDC_SVI_2022_California_current.csv"
MAPPING = ROOT / "Data/JULY_UTILITY_CONSTRAINED_92.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"FIPS": str}, low_memory=False)
    frame["FIPS"] = frame.FIPS.str.zfill(11)
    assert frame.FIPS.is_unique
    return frame.set_index("FIPS").sort_index()


def main() -> None:
    assert LOCAL.is_file() and OFFICIAL.is_file() and MAPPING.is_file()
    local, official = load(LOCAL), load(OFFICIAL)
    domain = pd.read_csv(MAPPING, dtype={"tract_id": str}).tract_id.str.zfill(11).unique()
    assert len(domain) == 2315 and set(domain) <= set(local.index) & set(official.index)
    assert set(local.index) == set(official.index)
    assert list(local.columns) == list(official.columns)
    same = local.fillna("<NA>").astype(str).eq(official.fillna("<NA>").astype(str))
    comparison = pd.DataFrame([dict(
        source_url="https://svi.cdc.gov/Documents/Data/2022/csv/states/California.csv",
        download_timestamp_utc=datetime.fromtimestamp(
            OFFICIAL.stat().st_mtime, timezone.utc
        ).isoformat(),
        local_file=str(LOCAL.relative_to(ROOT)),
        official_download_file=str(OFFICIAL.relative_to(ROOT)),
        local_bytes=LOCAL.stat().st_size, official_bytes=OFFICIAL.stat().st_size,
        local_sha256=sha256(LOCAL), official_sha256=sha256(OFFICIAL),
        local_fips_count=len(local), official_fips_count=len(official),
        study_tract_count=len(domain), different_fips_rows=int((~same.all(axis=1)).sum()),
        different_cells=int((~same).to_numpy().sum()),
        byte_identical=sha256(LOCAL) == sha256(OFFICIAL),
    )])
    local_score = pd.to_numeric(local.loc[domain, "RPL_THEMES"], errors="coerce")
    missing = sorted(local_score.index[local_score.isna() | local_score.eq(-999)])
    assert len(missing) == 24, (len(missing), missing)
    raw_cols = [c for c in official if c.startswith(("E_", "EP_"))]
    rows = []
    for fips in missing:
        record = official.loc[fips]
        pop = pd.to_numeric(record.E_TOTPOP, errors="coerce")
        source_missing = [c for c in raw_cols if pd.isna(pd.to_numeric(record[c], errors="coerce"))
                          or float(record[c]) == -999]
        fields = {field: record[field] for field in
                  ["RPL_THEME1", "RPL_THEME2", "RPL_THEME3", "RPL_THEME4",
                   "E_TOTPOP", "SPL_THEME1", "SPL_THEME2", "SPL_THEME3",
                   "SPL_THEME4", "SPL_THEMES"]}
        official_score = pd.to_numeric(record.RPL_THEMES, errors="coerce")
        if pop == 0:
            status = "zero_population_excluded_from_CDC_ranking"
        elif pop > 0 and (pd.isna(official_score) or official_score == -999):
            status = ("positive_population_official_SVI_unavailable_with_missing_source_fields"
                      if source_missing else
                      "positive_population_official_SVI_unavailable_no_raw_sentinel_detected")
        else:
            status = "official_score_now_available"
        rows.append(dict(FIPS=fips, local_RPL_THEMES=local.loc[fips, "RPL_THEMES"],
                         current_official_RPL_THEMES=record.RPL_THEMES,
                         E_TOTPOP=fields.pop("E_TOTPOP"), **fields,
                         missing_source_fields=";".join(source_missing),
                         current_status=status))
    out = pd.DataFrame(rows)
    assert len(out) == 24 and out.FIPS.is_unique
    comparison["study_missing_rpl_count"] = len(out)
    comparison["study_missing_zero_population"] = int(out.E_TOTPOP.eq(0).sum())
    comparison["study_missing_positive_population"] = int(out.E_TOTPOP.gt(0).sum())
    comparison.to_csv(ROOT / "results" / "diagnostics" / "CDC_SVI_CURRENT_SOURCE_CHECK.csv", index=False)
    out.to_csv(ROOT / "results" / "vulnerability" / "CDC_SVI_MISSING_24_EXACT.csv", index=False)
    print(comparison.to_string(index=False))
    print(out.current_status.value_counts().to_string())
    print(out[["FIPS", "E_TOTPOP", "missing_source_fields", "current_status"]].to_string(index=False))


if __name__ == "__main__":
    main()
