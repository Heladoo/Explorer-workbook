"""Concrete ``ImageBackend`` implementations (see ``src/ports.py``).

Empty by default — the MVP ships no image generation. Each module here is one
backend, constructor-injected everywhere it's used so tests never touch the
network.
"""

from __future__ import annotations

from src.image_backends.openrouter import OpenRouterImageBackend

__all__ = ["OpenRouterImageBackend"]
