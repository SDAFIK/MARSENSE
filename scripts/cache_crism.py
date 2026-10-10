"""Bounded, hash-checked reproduction of official processed CRISM products."""

from backend.config import ROOT
from scripts.cache_cameras import verify


def main() -> None:
    verify(ROOT / 'data/nasa/crism/source.json')


if __name__ == '__main__':
    main()
