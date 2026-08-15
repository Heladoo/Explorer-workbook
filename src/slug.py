"""Slugification, standalone.

Split out from ``src.models.context`` (which still re-exports ``slugify`` for
every existing import site) so it can be a dependency-free leaf module: both
``src.models.context`` and ``src.symbols`` need it, and ``src.symbols``
depends on nothing from ``src.models`` — putting it here instead of leaving
it in ``context.py`` avoids a circular import between the two.
"""

from __future__ import annotations

import re
import unicodedata


def slugify(value: str) -> str:
    """Return a filesystem- and URL-safe slug for ``value``.

    Accents are folded rather than dropped so that "Český Krumlov" becomes
    ``cesky-krumlov`` instead of ``cesk-krumlov``.
    """
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return slug or "destination"
