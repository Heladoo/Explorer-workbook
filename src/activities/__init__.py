"""Activity plugins.

Every module in this package that defines a ``@register_activity`` class is
imported automatically, so dropping a new file in here is all it takes to add
an activity to the system.
"""

from __future__ import annotations

import importlib
import pkgutil

from src.activities.base import (
    ACTIVITY_REGISTRY,
    ActivityGenerator,
    available_activities,
    get_generator,
    register_activity,
)


def load_activities() -> dict[str, type[ActivityGenerator]]:
    """Import every activity module in this package and return the registry.

    Idempotent: modules already in ``sys.modules`` are not re-imported, and the
    registry rejects duplicate activity types.
    """
    for module_info in pkgutil.iter_modules(__path__):
        if module_info.name.startswith("_") or module_info.name == "base":
            continue
        importlib.import_module(f"{__name__}.{module_info.name}")
    return ACTIVITY_REGISTRY


load_activities()

__all__ = [
    "ACTIVITY_REGISTRY",
    "ActivityGenerator",
    "available_activities",
    "get_generator",
    "load_activities",
    "register_activity",
]
