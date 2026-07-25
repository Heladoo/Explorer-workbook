#!/usr/bin/env python3
"""Convenience entry point: ``python generate_workbook.py --destination "Prague"``.

Equivalent to ``python -m src.cli``.
"""

from src.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
