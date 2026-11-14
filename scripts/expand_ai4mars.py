"""Build a bounded, fresh cross-rover research dataset from the official AI4Mars ZIP.

No release data or old manifests are rewritten. Whole-archive download is prohibited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from ai.research_gate import audit_manifest
from backend.config import ROOT
from scripts.cache_ai4mars import SIZE, URL, extract
from scripts.range_archive import RangeArchive

BASE = ROOT / "data/nasa/ai4mars"
FROZEN = BASE / "manifests/6ec2a90869202f2719ce0fc33084ef094436371df271b163241251869ce8468e.json"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def stem(name: str) -> str:
    return re.sub(r"_merged\d*$", "", Path(name).stem)


def msl_group(name: str) -> str:
    match = re.search(r"_F(\d{3})", name)
    if not match:
        raise ValueError("MSL site not available")
    return "msl-site-" + match[1]


def mars2020_site(name: str) -> str | None:
    # RMC site component of N###ddddNCAM; grouping by complete site
    # keeps multiple sols/drives from the same rover site in one split.
    match = re.search(r"_N(\d{3})\d{4}NCAM", name)
    return "m2020-site-" + match[1] if match else None


def build(output: Path) -> dict:
    index = json.loads((BASE / "archive-index.json").read_text())
    old = json.loads(FROZEN.read_text())
    prior = [old]
    prior.extend(json.loads(p.read_text()) for p in (BASE / "manifests").glob("*.json"))
    used_names = {
        stem(row["image"]) for m in prior
        for split in ("train", "validation", "test", "transfer") for row in m[split]
    }
    old_test_sites = {row["group"] for m in prior for row in m["test"]}
    old_transfer_sites = {
        mars2020_site(row["image"]) for m in prior for row in m["transfer"]
    } - {None}
    expert_sites = {
        msl_group(e["name"]) for e in index
        if "/msl/ncam/labels/test/masked-gold-min1-100agree/" in e["name"]
        and e["name"].endswith(".png")
    }
    images = {
        Path(e["name"]).stem: e for e in index
        if "/images/" in e["name"] and e["name"].lower().endswith((".jpg", ".jpeg"))
    }
    old_val_sites = {row["group"] for row in old["validation"]}
    msl_train = [
        e for e in index if "/msl/ncam/labels/train/" in e["name"]
        and e["name"].endswith(".png") and stem(e["name"]) in images
        and stem(e["name"]) not in used_names
        and msl_group(e["name"]) not in expert_sites | old_val_sites
    ]
    msl_test = [
        e for e in index if "/msl/ncam/labels/test/masked-gold-min1-100agree/" in e["name"]
        and e["name"].endswith(".png") and stem(e["name"]) in images
        and stem(e["name"]) not in used_names and msl_group(e["name"]) not in old_test_sites
    ]
    mars2020 = [
        e for e in index if "/m2020/labels/NAV/" in e["name"]
        and e["name"].endswith(".png") and stem(e["name"]) in images
        and stem(e["name"]) not in used_names and mars2020_site(e["name"])
    ]
    sites = sorted({mars2020_site(e["name"]) for e in mars2020} - {None})
    new_sites = sorted(set(sites) - old_transfer_sites, key=digest)
    if len(new_sites) < 2:
        raise ValueError("Insufficient new Perseverance sites for independent train/test split")
    transfer_sites = {new_sites[0]}
    training_sites = set(new_sites[1:])
    # Previously evaluated sites stay out of both new training and fresh transfer.
    mars_train = [e for e in mars2020 if mars2020_site(e["name"]) in training_sites]
    mars_test = [e for e in mars2020 if mars2020_site(e["name"]) in transfer_sites]
    manifest = {"train": list(old["train"]), "validation": list(old["validation"]),
                "test": [], "transfer": []}
    reader = RangeArchive(URL, SIZE, BASE / "expanded-ranges", budget=192 * 1024 * 1024)
    provenance = []

    def acquire(candidates: list[dict], split: str, limit: int, rover: str) -> None:
        group_for = msl_group if rover == "msl" else mars2020_site
        counts: Counter = Counter()
        selected: set[str] = set()
        # Train sampling may prioritize rock-bearing masks; evaluation is fixed
        # by filename hash and never selected on measured model performance.
        ordered = sorted(candidates, key=lambda e: digest(e["name"]))
        if split == "train":
            ordered = ordered[:limit * 3]
        pending = []
        for entry in ordered:
            key = stem(entry["name"])
            group = group_for(entry["name"])
            if key in selected or counts[group] >= (6 if rover == "msl" else 32):
                continue
            selected.add(key)
            mask_path = BASE / "expanded" / split / (key + "-mask.png")
            record = extract(reader, entry, mask_path)
            with Image.open(mask_path) as image:
                mask = np.asarray(image)
                if mask.ndim != 2 or not np.isin(mask, [0, 1, 2, 3, 255]).all():
                    raise ValueError("Unexpected NAV mask class mapping")
                rocks = float((mask == 3).mean())
            pending.append((rocks, key, group, mask_path, record))
            if split != "train":
                counts[group] += 1
                if len(pending) == limit:
                    break
        if split == "train":
            # Half rock-prioritized, half filename-hash sampled; all from train sites.
            rare = sorted(pending, key=lambda item: (-item[0], digest(item[1])))
            head = rare[:limit // 2]
            taken = {item[1] for item in head}
            pending = head + [item for item in pending if item[1] not in taken]
        counts.clear()
        added = 0
        for _, key, group, mask_path, record in pending:
            if counts[group] >= (6 if rover == "msl" else 32):
                continue
            image = images[key]
            image_path = BASE / "expanded" / split / Path(image["name"]).name
            image_record = extract(reader, image, image_path)
            with Image.open(image_path) as rgb, Image.open(mask_path) as mask:
                iw, ih = rgb.size
                mw, mh = mask.size
                if abs(iw * mh - ih * mw) / max(iw * mh, ih * mw) > 0.01:
                    raise ValueError("Image/label aspect mismatch in fixed sample")
            manifest[split].append({
                "image": image_path.relative_to(BASE).as_posix(),
                "mask": mask_path.relative_to(BASE).as_posix(),
                "group": group, "image_sha256": image_record["sha256"],
                "mask_sha256": record["sha256"],
            })
            provenance.extend([image_record, record])
            counts[group] += 1
            added += 1
            print(f"{rover} {split}: {added}/{limit}", flush=True)
            if added == limit:
                break
        if added != limit:
            raise ValueError(f"Insufficient independent {rover} {split} samples: {added}")

    acquire(msl_train, "train", 48, "msl")
    acquire(mars_train, "train", 32, "m2020")
    acquire(msl_test, "test", 16, "msl")
    acquire(mars_test, "transfer", 24, "m2020")
    manifest["source_metadata"] = "source.json"
    manifest["selection_policy"] = (
        "MSL expert sites excluded from training; fresh MSL expert holdout; "
        "whole Perseverance sites held out, prior evaluated sites excluded; "
        "rock-prioritized training only; evaluation fixed by filename hash"
    )
    manifest["archive_records"] = provenance
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2))
    audit = audit_manifest(output)
    print(json.dumps({"audit": audit, "range_bytes": reader.requested_bytes}, indent=2))
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BASE / "expanded-v3.json")
    args = parser.parse_args()
    build(args.output)
