"""The two dataclasses the symbol library is built from.

``SymbolFacets`` is the metadata a library entry carries; ``Symbol`` pairs
that with the same key/label/subject the bank has always had. Keeping facets
optional (``None`` rather than an empty ``SymbolFacets``) is what lets a
symbol *minted* at runtime from destination knowledge — which has no facets
at all — share the same type as a library entry.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolFacets:
    """Everything about a symbol that isn't its name or its drawing prompt.

    Every set-valued field defaults to empty, meaning "no restriction" — an
    empty ``environments`` is findable anywhere, an empty ``regions`` claims
    no particular place. Only ``topic``, ``ubiquity`` and ``status`` are
    required: every entry needs exactly one diversity bucket, one findability
    tier, and an honest statement of whether it has artwork.
    """

    topic: str
    ubiquity: str
    status: str
    environments: tuple[str, ...] = ()
    climate: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    #: English synonyms a knowledge phrase can resolve onto instead of minting
    #: a new, uncached key — "fresh fish" -> the existing ``fish`` entry.
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Symbol:
    """One thing to spot, and how to draw it.

    ``key`` is a stable, language-independent slug: it names the prompt file,
    the generated image, and the cache entry. ``subject`` is always English —
    image prompts are never localized. ``label`` is the English reader-facing
    name; locales translate it under ``symbol.<key>``.
    """

    key: str
    label: str
    subject: str
    #: ``None`` for a symbol minted at runtime from destination knowledge
    #: (see ``destination_symbols()``), which has no facets to carry.
    facets: SymbolFacets | None = None

    @property
    def universal(self) -> bool:
        """Whether ``label`` is the bank's English label, translatable via
        ``symbol.<key>``.

        This is a *localization* fact, not a geography one — tracing every
        consumer shows it is checked only to decide whether to look the label
        up in a locale (``scavenger_hunt.py``, ``matching.py``), never to
        decide findability. Geography lives in ``facets`` instead; keeping
        this name and this meaning means every existing call site, and
        ``workbook.json``'s schema, is unaffected by the library's arrival.
        """
        return self.facets is not None
