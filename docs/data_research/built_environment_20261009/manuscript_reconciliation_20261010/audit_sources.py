"""Read-only manuscript discovery and stable OOXML paragraph inventory."""
import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
NS = {"w": W[1:-1]}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_of(element, deleted=False):
    # Report current visible text separately from deleted revision text.
    def visit(node):
        if node.tag == W + "del" and not deleted:
            return ""
        if node.tag in (W + "t", W + "delText", M + "t"):
            return node.text or ""
        if node.tag == W + "tab":
            return "\t"
        if node.tag in (W + "br", W + "cr"):
            return "\n"
        return "".join(visit(child) for child in node)
    return visit(element)


def read_docx(path):
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        body = root.find("w:body", NS)
        core = ET.fromstring(archive.read("docProps/core.xml"))
        metadata = {node.tag.split("}")[-1]: node.text for node in core}
        records = []
        pnum = tnum = 0
        section = "Front matter"
        for bnum, block in enumerate(body, 1):
            if block.tag == W + "p":
                pnum += 1
                value = text_of(block).strip()
                style_node = block.find("w:pPr/w:pStyle", NS)
                style = style_node.get(W + "val", "") if style_node is not None else ""
                if value and ("heading" in style.lower() or re.match(r"^\d+(?:\.\d+)*\.?\s+[A-Z]", value)) and len(value) < 180:
                    section = value
                records.append({"location": f"P{pnum:04d} / body block {bnum}", "kind": "paragraph", "section": section,
                                "style": style, "text": value, "all_revision_text": text_of(block, True),
                                "drawings": len(block.findall(".//w:drawing", NS)),
                                "insertions": len(block.findall(".//w:ins", NS)), "deletions": len(block.findall(".//w:del", NS))})
            elif block.tag == W + "tbl":
                tnum += 1
                for rnum, row in enumerate(block.findall("w:tr", NS), 1):
                    for cnum, cell in enumerate(row.findall("w:tc", NS), 1):
                        records.append({"location": f"T{tnum}R{rnum}C{cnum} / body block {bnum}", "kind": "table_cell",
                                        "section": section, "style": "", "text": text_of(cell).strip(),
                                        "all_revision_text": text_of(cell, True), "drawings": len(cell.findall(".//w:drawing", NS))})
        for name in archive.namelist():
            if re.match(r"word/(?:header\d+|footer\d+|footnotes|endnotes|comments)\.xml$", name):
                part = ET.fromstring(archive.read(name))
                for i, p in enumerate(part.findall(".//w:p", NS), 1):
                    records.append({"location": f"{name}:P{i}", "kind": "ancillary", "section": name, "style": "", "text": text_of(p).strip()})
        visible = "\n".join(r["text"] for r in records)
        title = next((r["text"] for r in records if r["text"]), "")
        return {"metadata": metadata, "title": title, "records": records, "text_sha256": hashlib.sha256(visible.encode()).hexdigest(),
                "words": len(visible.split()), "body_paragraphs": pnum, "tables": tnum,
                "media_files": len([n for n in archive.namelist() if n.startswith("word/media/")]),
                "tracked_insertions": len(root.findall(".//w:ins", NS)), "tracked_deletions": len(root.findall(".//w:del", NS))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--local-root", type=Path, required=True)
    ap.add_argument("--downloads", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    extracts = a.out / "source_extracts"
    extracts.mkdir(exist_ok=True)
    paths = set()
    for folder in [a.project / "00_Project_Deliverables/Manuscript_Working_Files",
                   a.project / "00_Project_Deliverables/Course_Submission_2025",
                   a.project / "00_Project_Deliverables/Development_Drafts",
                   a.project / "LA_grid_manuscript_rebuild", a.repo / "docs/meeting"]:
        paths.update(folder.glob("*.docx"))
    for folder in [a.project / "99_Archive/_publication_repository_backups/20260722_204812/Submission_Package",
                   a.project / "LA_grid_manuscript_rebuild/Submission_Package",
                   a.project / "Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale/Submission_Package",
                   a.repo / "provenance/legacy_outputs/Submission_Package", a.local_root / "Submission_Package"]:
        paths.update(folder.glob("*Manuscript*.docx"))
    paths.update(a.downloads.glob("LA*Grid*.docx"))
    paths.update(a.downloads.glob("LA*Grid*.pdf"))
    paths.update((a.project / "00_Project_Deliverables/Manuscript_Working_Files").glob("*.pdf"))
    inventory = []
    for i, path in enumerate(sorted(paths), 1):
        if path.name.startswith("~$"):
            continue
        sid = f"S{i:02d}"
        record = {"source_id": sid, "path": str(path.resolve()), "sha256": sha(path), "bytes": path.stat().st_size,
                  "filesystem_mtime": path.stat().st_mtime, "authority_from_mtime": False}
        if path.suffix.lower() == ".docx":
            record.update(read_docx(path))
        else:
            from pypdf import PdfReader
            pdf = PdfReader(str(path))
            record.update({"title": str((pdf.metadata or {}).get("/Title", "")), "metadata": {str(k): str(v) for k, v in (pdf.metadata or {}).items()},
                           "records": [{"location": f"PDF page {p + 1}", "kind": "page", "section": "Unassigned PDF section", "text": (page.extract_text() or "").encode("utf-16", "surrogatepass").decode("utf-16", "replace")} for p, page in enumerate(pdf.pages)]})
            record["pdf_text_caution"] = "PDF extraction normalizes surrogate pairs and replaces invalid isolated surrogates; equations and layout require visual review."
            visible = "\n".join(r["text"] for r in record["records"])
            record["text_sha256"] = hashlib.sha256(visible.encode()).hexdigest()
            record["words"] = len(visible.split())
        content = [f"# {sid} {path.name}", f"Source: {path.resolve()}", f"SHA256: {record['sha256']}"]
        for r in record["records"]:
            if r["text"]:
                content.extend([f"\n## {r['location']} | {r['section']}", r["text"]])
        (extracts / f"{sid}.md").write_text("\n\n".join(content) + "\n", encoding="utf-8")
        inventory.append(record)
    groups = defaultdict(list)
    for r in inventory:
        groups[r["sha256"]].append(r["source_id"])
    for r in inventory:
        r["identical_byte_sources"] = groups[r["sha256"]]
    git_history = []
    known = {r["sha256"]: r["source_id"] for r in inventory}
    refs = ["3466ba2", "63e8ace", "b95ef8a", "84e7865", "HEAD", "84d7ac6"]
    def git(*args):
        return subprocess.check_output(["git", "-c", "filter.lfs.process=", "-c", "filter.lfs.smudge=", "-c", "filter.lfs.required=false", "-C", str(a.repo), *args])
    for ref in refs:
        full_commit = git("rev-parse", ref).decode().strip()
        names = git("ls-tree", "-r", "--name-only", ref).decode().splitlines()
        for name in names:
            if not re.search(r"(?:REVISED_MANUSCRIPT\.(?:md|docx)|LA_Grid_Manuscript_Resubmission_Rebuild\.docx|Manuscript_IJDRR\.docx)$", name):
                continue
            data = git("show", f"{ref}:{name}")
            blob_sha = hashlib.sha256(data).hexdigest()
            if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
                fields = dict(line.split(" ", 1) for line in data.decode().splitlines())
                oid = fields["oid"].split(":")[-1]
                common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip())
                data = (common / "lfs/objects" / oid[:2] / oid[2:4] / oid).read_bytes()
                assert hashlib.sha256(data).hexdigest() == oid and len(data) == int(fields["size"])
            digest = hashlib.sha256(data).hexdigest()
            if digest not in known:
                sid = f"S{len(inventory) + 1:02d}"
                record = {"source_id": sid, "path": f"git:{full_commit}:{name}", "sha256": digest, "git_blob_sha256": blob_sha, "bytes": len(data), "authority_from_mtime": False}
                if name.endswith(".docx"):
                    record.update(read_docx(io.BytesIO(data)))
                else:
                    value = data.decode("utf-8-sig")
                    record.update({"title": value.splitlines()[0], "metadata": {"commit": full_commit}, "words": len(value.split()), "text_sha256": digest,
                                   "records": [{"location": f"MD paragraph {i + 1}", "kind": "markdown", "section": "Historical Markdown", "text": p} for i, p in enumerate(value.split("\n\n")) if p.strip()]})
                record["identical_byte_sources"] = [sid]
                inventory.append(record)
                known[digest] = sid
                (extracts / f"{sid}.md").write_text("\n\n".join([f"# {sid} {name}", f"Source: {record['path']}", f"SHA256: {digest}"] + [f"## {p['location']} | {p['section']}\n\n{p['text']}" for p in record["records"] if p["text"]]) + "\n", encoding="utf-8")
            git_history.append({"commit": full_commit, "repository_path": name, "payload_sha256": digest, "git_blob_sha256": blob_sha, "matches_source": known[digest],
                                "last_change": git("log", "-1", "--format=%H %aI %s", ref, "--", name).decode().strip()})
    (a.out / "MANUSCRIPT_GIT_HISTORY.json").write_text(json.dumps(git_history, indent=2) + "\n", encoding="utf-8")
    (a.out / "MANUSCRIPT_SOURCE_INVENTORY.json").write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fields = ["source_id", "path", "sha256", "text_sha256", "bytes", "title", "words", "body_paragraphs", "tables", "media_files", "tracked_insertions", "tracked_deletions"]
    with (a.out / "MANUSCRIPT_SOURCE_INVENTORY.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(inventory)
    print(json.dumps([{k: r.get(k) for k in ["source_id", "path", "title", "words", "sha256", "identical_byte_sources"]} for r in inventory], indent=2))


if __name__ == "__main__":
    main()
