"""AI Travel Activity Book Generator.

Turns a destination into a printable children's travel activity workbook,
expressed as data: ``workbook.json``, ``workbook.md`` and one image-generation
prompt file per page.

The public entry point is :func:`generate_workbook`.
"""

from src.api import generate_workbook

__all__ = ["generate_workbook"]
