"""Cross-platform entrypoint for `python -m juben`."""

from __future__ import annotations

import sys
from pathlib import Path


ALIASES = {
    "extract": "extract-book",
    "map": "map-book",
    "review": "batch-review-done",
}


def _normalize_argv(argv: list[str]) -> list[str]:
    if len(argv) <= 1:
        return argv
    normalized = list(argv)
    normalized[1] = ALIASES.get(normalized[1], normalized[1])
    return normalized


def main() -> int:
    ops_dir = Path(__file__).resolve().parent / "_ops"
    sys.path.insert(0, str(ops_dir))

    from ._ops import controller

    original_argv = sys.argv
    try:
        sys.argv = _normalize_argv(sys.argv)
        return controller.main()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    raise SystemExit(main())
