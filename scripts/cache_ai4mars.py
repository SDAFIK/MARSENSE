"""Bounded extraction from the NASA-linked AI4Mars 0.6 release using its saved index."""

import argparse
import hashlib
import json
import re
import struct
import zipfile
import zlib
from pathlib import Path

from backend.config import ROOT
from scripts.range_archive import RangeArchive

URL = "https://zenodo.org/api/records/15995036/files/ai4mars-dataset-merged-0.6.zip/content"
SIZE = 16232481989


def extract(reader: RangeArchive, entry: dict, destination: Path) -> dict:
    reader.seek(entry["offset"])
    header = reader.read(30)
    fields = struct.unpack("<4s5H3I2H", header)
    if fields[0] != b"PK\x03\x04" or fields[3] not in (0, 8) or fields[2] & 1:
        raise ValueError("Unsupported ZIP entry header")
    name_length, extra_length = fields[-2:]
    name = reader.read(name_length).decode("utf-8")
    if name != entry["name"]:
        raise ValueError("Archive index/header filename mismatch")
    reader.seek(extra_length, 1)
    compressed = reader.read(entry["compressed"])
    content = zlib.decompress(compressed, -15) if fields[3] == 8 else compressed
    if len(content) != entry["size"]:
        raise ValueError("Archive entry length mismatch")
    if not fields[2] & 8 and zlib.crc32(content) != fields[6]:
        raise ValueError("Archive entry CRC mismatch")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return {
        "archive_entry": name,
        "file": destination.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", action="store_true")
    parser.add_argument("--index", action="store_true", help="Rebuild bounded ZIP index")
    parser.add_argument("--fresh-evaluation", action="store_true")
    args = parser.parse_args()
    index_path = ROOT / "data/nasa/ai4mars/archive-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if args.index:
        remote = RangeArchive(
            URL, SIZE, ROOT / "data/nasa/ai4mars/index-ranges", budget=40 * 1024 * 1024
        )
        with zipfile.ZipFile(remote) as archive:
            index = [
                {
                    "name": item.filename,
                    "offset": item.header_offset,
                    "compressed": item.compress_size,
                    "size": item.file_size,
                    "crc32": item.CRC,
                }
                for item in archive.infolist()
            ]
        index_path.write_text(json.dumps(index))
    elif not index_path.is_file():
        existing = ROOT / ".tmp/ai4mars-index.json"
        if not existing.is_file():
            raise ValueError("Archive index missing; run with --index first")
        index_path.write_bytes(existing.read_bytes())
    index = json.loads(index_path.read_text())
    reader = RangeArchive(URL, SIZE, ROOT / "data/nasa/ai4mars/ranges")
    records = []
    for suffix in ("info.md", "label_keys.json", "changelog.md"):
        entry = next(e for e in index if e["name"].endswith("/" + suffix))
        records.append(extract(reader, entry, ROOT / "data/nasa/ai4mars" / suffix))
    metadata = {
        "source": URL,
        "record": "https://zenodo.org/records/15995036",
        "version": "merged-0.6",
        "doi": "10.5281/zenodo.15995036",
        "license": "CC-BY-4.0 (publisher release-record.json)",
        "archive_size_bytes": SIZE,
        "archive_index_sha256": hashlib.sha256(index_path.read_bytes()).hexdigest(),
        "files": records,
        "ranges": reader.ranges,
    }
    (ROOT / "data/nasa/ai4mars/source.json").write_text(json.dumps(metadata, indent=2))
    if args.subset:
        acquire_subset(reader, index, metadata, fresh_evaluation=args.fresh_evaluation)
    print(json.dumps({"extracted_files": len(records), "range_bytes": reader.requested_bytes}))


def acquire_subset(
    reader: RangeArchive, index: list[dict], metadata: dict, fresh_evaluation: bool = False
) -> None:
    images = {
        Path(e["name"]).stem: e
        for e in index
        if "/images/" in e["name"] and e["name"].lower().endswith((".jpg", ".jpeg"))
    }
    masks = [e for e in index if "/msl/ncam/labels/" in e["name"] and e["name"].endswith(".png")]

    def group(e: dict) -> str:
        match = re.search(r"_F(\d{3})", e["name"])
        if not match:
            raise ValueError("MSL site grouping unavailable")
        return "msl-site-" + match[1]

    test = [e for e in masks if "/test/masked-gold-min1-100agree/" in e["name"]]
    test_groups = {group(e) for e in test}
    train = [e for e in masks if "/train/" in e["name"] and group(e) not in test_groups]
    partitions = {
        "train": [e for e in train if int(hashlib.sha256(group(e).encode()).hexdigest(), 16) % 4],
        "validation": [
            e for e in train if not int(hashlib.sha256(group(e).encode()).hexdigest(), 16) % 4
        ],
        "test": test,
        "transfer": [
            e for e in index if "/m2020/labels/NAV/" in e["name"] and e["name"].endswith(".png")
        ],
    }
    limits = {"train": 48, "validation": 16, "test": 16, "transfer": 8}
    manifest = {}
    base = ROOT / "data/nasa/ai4mars"
    excluded = {}
    existing_manifest = None
    if (base / "subset.json").is_file():
        existing_manifest = json.loads((base / "subset.json").read_text())
    if fresh_evaluation:
        original = existing_manifest
        if original is None:
            raise ValueError("Fresh evaluation requires an existing baseline manifest")
        history = base / "manifests"
        history.mkdir(exist_ok=True)
        raw_manifest = (base / "subset.json").read_bytes()
        (history / (hashlib.sha256(raw_manifest).hexdigest() + ".json")).write_bytes(raw_manifest)
        if not (base / "baseline-v1-subset.json").exists():
            (base / "baseline-v1-subset.json").write_text(json.dumps(original, indent=2))
        excluded = {key: {row["group"] for row in original[key]} for key in ("test", "transfer")}
        for recorded in [*history.glob("*.json"), base / "baseline-v1-subset.json"]:
            prior = json.loads(recorded.read_text())
            for key in excluded:
                excluded[key].update(row["group"] for row in prior[key])
    for split, candidates in partitions.items():
        selected = []
        counts: dict[str, int] = {}
        for mask in sorted(
            candidates, key=lambda e: hashlib.sha256(e["name"].encode()).hexdigest()
        ):
            stem = re.sub(r"_merged\d*$", "", Path(mask["name"]).stem)
            if stem not in images:
                continue
            if (
                existing_manifest
                and not fresh_evaluation
                and stem not in {Path(row["image"]).stem for row in existing_manifest[split]}
            ):
                continue
            episode = group(mask) if split != "transfer" else "m2020-sol-" + stem.split("_")[1]
            if episode in excluded.get(split, set()):
                continue
            if counts.get(episode, 0) >= (4 if split == "test" else 2):
                continue
            counts[episode] = counts.get(episode, 0) + 1
            image = images[stem]
            image_path = base / "subset" / split / Path(image["name"]).name
            mask_path = base / "subset" / split / (stem + "-mask.png")
            image_record = extract(reader, image, image_path)
            mask_record = extract(reader, mask, mask_path)
            selected.append(
                {
                    "image": image_path.relative_to(base).as_posix(),
                    "mask": mask_path.relative_to(base).as_posix(),
                    "group": episode,
                    "image_sha256": image_record["sha256"],
                    "mask_sha256": mask_record["sha256"],
                }
            )
            metadata["files"].extend([image_record, mask_record])
            print(f"{split}: {len(selected)}/{limits[split]}", flush=True)
            if len(selected) == limits[split]:
                break
        if not selected:
            raise ValueError(f"No accessible image/label pairs for {split}")
        manifest[split] = selected
    metadata["ranges"] = reader.ranges
    metadata["subset_counts"] = {key: len(value) for key, value in manifest.items()}
    metadata["reserved_evaluation_groups_excluded"] = {
        key: sorted(values) for key, values in excluded.items()
    }
    metadata["split_policy"] = (
        "Disjoint MSL sites; all expert-test sites excluded from train/validation; "
        "Perseverance transfer never trained"
    )
    manifest["source_metadata"] = "source.json"
    (base / "subset.json").write_text(json.dumps(manifest, indent=2))
    (base / "source.json").write_text(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
