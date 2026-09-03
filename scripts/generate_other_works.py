#!/usr/bin/env python3
"""Keep the former Other works URL as a redirect to Publications > Reviews."""
from __future__ import annotations

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
TEMPLATE_PATH = ROOT / "templates" / "other_works.template.html"
OUTPUT_PATH = ROOT / "other-works.html"


def main() -> None:
    OUTPUT_PATH.write_text(TEMPLATE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Generated {OUTPUT_PATH.name}: redirect to publications.html#reviews")


if __name__ == "__main__":
    main()
