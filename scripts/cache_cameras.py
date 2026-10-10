"""Reproduce frozen PDS camera/PLACES inputs with bounded, hash-checked downloads."""

import hashlib
import json
import urllib.request
from pathlib import Path

from backend.config import ROOT


def verify(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text())
    for source in manifest['files']:
        path = ROOT / source['file']
        if path.exists():
            raw = path.read_bytes()
        else:
            with urllib.request.urlopen(source['url'], timeout=45) as response:
                raw = response.read(source['bytes'] + 1)
            if len(raw) != source['bytes']:
                raise ValueError('Unexpected PDS product size; refusing changed archive')
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError('Changed PDS source bytes; retain existing frozen release')
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix(path.suffix+'.partial')
            partial.write_bytes(raw)
            partial.replace(path)
    print(f"Verified {len(manifest['files'])} frozen source files")


def main() -> None:
    verify(ROOT / 'data/nasa/cameras/source.json')


if __name__ == '__main__':
    main()
