"""Package standalone current figure PNGs with captions in a separate file."""
from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / "results/figure_review"
OUTPUT = ROOT / "results/drive_upload/2026-10-23"
PACKAGE = OUTPUT / "LA_Grid_Figures_2026-10-23"
ARCHIVE = OUTPUT / "LA_Grid_Figures_2026-10-23.zip"
EXPECTED_FIGURES = 16
ZIP_DATE = (2026, 10, 23, 12, 0, 0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    rows = list(csv.DictReader((SUITE / "FIGURE_MANIFEST.csv").open(encoding="utf-8-sig")))
    rows = [row for row in rows if row["final_name"].lower().endswith(".png")]
    if len(rows) != EXPECTED_FIGURES:
        raise ValueError(f"Expected {EXPECTED_FIGURES} active figure PNGs, found {len(rows)}")

    figure_dir = PACKAGE / "Figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for row in rows:
        source = ROOT / row["mirror_file"]
        data = source.read_bytes()
        expected = row["sha256"].lower()
        if sha256(data) != expected:
            raise ValueError(f"Current figure mirror does not match manifest: {source}")
        target = figure_dir / Path(row["mirror_file"]).name
        target.write_bytes(data)
        with Image.open(target) as image:
            dpi = image.info.get("dpi", (0, 0))
            if image.format != "PNG" or min(dpi) < 599:
                raise ValueError(f"Expected a 600-dpi PNG: {target} ({dpi})")
            records.append({
                "filename": target.name,
                "sha256": expected,
                "bytes": len(data),
                "pixels": list(image.size),
                "dpi": list(dpi),
            })

    caption_source = SUITE / "MANUSCRIPT_FACING_CAPTIONS.md"
    caption_data = caption_source.read_bytes()
    caption_text = caption_data.decode("utf-8")
    caption_count = caption_text.count("\n## ")
    if caption_count != EXPECTED_FIGURES:
        raise ValueError(f"Expected {EXPECTED_FIGURES} separate captions, found {caption_count}")
    (PACKAGE / "CAPTIONS.md").write_bytes(caption_data)
    readme = (
        "# LA Grid figures for coauthor sharing\n\n"
        "This folder contains 16 standalone 600-dpi PNG figure files. Each image is artwork only; "
        "captions are provided separately in `CAPTIONS.md` for manuscript submission.\n\n"
        "The files are numbered as seven main figures and nine supplementary figures. "
        "No process CSVs or combined caption pages are included.\n"
    )
    (PACKAGE / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        files = [(path, path.relative_to(PACKAGE).as_posix())
                 for path in sorted(PACKAGE.rglob("*")) if path.is_file()]
        for path, name in files:
            info = zipfile.ZipInfo(name, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        bad = archive.testzip()
        if bad:
            raise ValueError(f"Corrupt archive member: {bad}")
        if len([name for name in names if name.startswith("Figures/") and name.endswith(".png")]) != EXPECTED_FIGURES:
            raise ValueError("The archive does not contain all 16 standalone figures")
        if "CAPTIONS.md" not in names or any(name.lower().endswith((".pdf", ".csv")) for name in names):
            raise ValueError("The archive must contain separate captions and no PDFs or CSVs")

    print(json.dumps({
        "archive": str(ARCHIVE),
        "archive_sha256": sha256(ARCHIVE.read_bytes()),
        "archive_bytes": ARCHIVE.stat().st_size,
        "figure_count": len(records),
        "caption_count": caption_count,
        "figures": records,
        "zip_test": "PASS",
        "captions_are_separate": True,
        "pdf_or_csv_included": False,
    }, indent=2))


if __name__ == "__main__":
    main()
