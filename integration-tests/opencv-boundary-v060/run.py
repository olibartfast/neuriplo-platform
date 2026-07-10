#!/usr/bin/env python3
"""Validate OpenCV-boundary compatibility evidence artifacts."""

from pathlib import Path

SCENARIO = Path(__file__).resolve().parent
REQUIRED = [
    SCENARIO / "evidence.yaml",
    SCENARIO / "reports" / "latest.md",
    SCENARIO / "reports" / "latest.json",
]

def main() -> int:
    missing = [path for path in REQUIRED if not path.is_file()]
    if missing:
        for path in missing:
            print(f"ERROR: missing {path}")
        return 1
    print("opencv-boundary-v060 evidence scaffold ok")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
