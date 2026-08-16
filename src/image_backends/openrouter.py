"""``ImageBackend`` (see ``src/ports.py``) backed by OpenRouter's unified Image API.

Same shape as ``LLMKnowledgeProvider`` in ``src/agents/destination_agent.py``:
stdlib ``urllib`` only, the transport is injectable so tests never touch the
network, and the API key comes from an environment variable by default.

Default model is ``openai/gpt-image-1`` — OpenAI's image model, reached through
OpenRouter rather than the OpenAI API directly, so swapping to a different
provider's model later is a constructor argument, not a rewrite.
"""

from __future__ import annotations

import base64
import json
import logging
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from src.models.context import WorkbookContext
from src.models.page import Page, SymbolBrief

logger = logging.getLogger(__name__)

OPENROUTER_IMAGES_URL = "https://openrouter.ai/api/v1/images"
DEFAULT_MODEL = "openai/gpt-image-1"

Transport = Callable[[str, dict[str, str], bytes], str]


class OpenRouterImageBackend:
    """Turns a page's ``image_prompt`` into an image via OpenRouter.

    Raises on any failure (missing key, HTTP error, unexpected response shape)
    rather than returning a sentinel — there is no fallback chain for artwork
    the way there is for destination knowledge, so callers decide per-page
    whether a failure should stop the run or just leave that page unillustrated.
    """

    name = "openrouter"

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        transport: Transport | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        quality: str | None = None,
        output_format: str = "png",
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.api_key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
        self.transport = transport or _urllib_transport
        self.aspect_ratio = aspect_ratio
        self.resolution = resolution
        self.quality = quality
        self.output_format = output_format
        self.timeout = timeout

    def generate(self, page: Page, context: WorkbookContext, *, output_dir: Path) -> Path:
        if not page.image_prompt:
            raise ValueError(f"page {page.number} ({page.type}) has no image_prompt to render")
        return self._render(
            page.image_prompt,
            context,
            output_dir=output_dir,
            stem=f"{page.number:02d}_{page.type}",
            label=f"page {page.number}",
        )

    def generate_symbol(
        self, symbol: SymbolBrief, context: WorkbookContext, *, output_dir: Path
    ) -> Path:
        """Render one grid-cell icon, named by its slug.

        Reference photos are deliberately *not* attached: a symbol is a plain
        object with no people in it, and keeping the request identical in every
        book is what lets one drawing be cached and reused everywhere.
        """
        if not symbol.prompt:
            raise ValueError(f"symbol {symbol.key!r} has no prompt to render")
        return self._render(
            symbol.prompt,
            context,
            output_dir=output_dir,
            stem=symbol.key,
            label=f"symbol {symbol.key!r}",
            with_references=False,
        )

    # -- internals -------------------------------------------------------

    def _render(
        self,
        prompt: str,
        context: WorkbookContext,
        *,
        output_dir: Path,
        stem: str,
        label: str,
        with_references: bool = True,
    ) -> Path:
        if not self.api_key:
            raise RuntimeError(
                "OpenRouterImageBackend has no API key; set OPENROUTER_API_KEY or pass api_key="
            )

        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "output_format": self.output_format,
        }
        if self.aspect_ratio:
            body["aspect_ratio"] = self.aspect_ratio
        if self.resolution:
            body["resolution"] = self.resolution
        if self.quality:
            body["quality"] = self.quality
        references = self._input_references(context) if with_references else []
        if references:
            body["input_references"] = references

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}",
        }

        try:
            raw = self.transport(OPENROUTER_IMAGES_URL, headers, json.dumps(body).encode("utf-8"))
        except Exception as exc:  # network, auth, timeout
            raise RuntimeError(f"OpenRouter image request failed for {label}: {exc}") from exc

        image_bytes, media_type = self._extract_image(raw, label)

        output_dir.mkdir(parents=True, exist_ok=True)
        extension = mimetypes.guess_extension(media_type) or f".{self.output_format}"
        path = output_dir / f"{stem}{extension}"
        path.write_bytes(image_bytes)
        return path

    @staticmethod
    def _input_references(context: WorkbookContext) -> list[dict[str, Any]]:
        references = []
        for photo in context.family_photos:
            photo_path = Path(photo)
            if not photo_path.is_file():
                logger.warning("family photo %s not found; skipping as a reference", photo)
                continue
            media_type = mimetypes.guess_type(photo_path.name)[0] or "image/jpeg"
            encoded = base64.b64encode(photo_path.read_bytes()).decode("ascii")
            references.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{encoded}"},
                }
            )
        return references

    @staticmethod
    def _extract_image(raw: str, label: str) -> tuple[bytes, str]:
        try:
            response = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenRouter returned a non-JSON response for {label}") from exc

        if isinstance(response, dict) and response.get("error"):
            raise RuntimeError(f"OpenRouter image error for {label}: {response['error']}")

        data = response.get("data") if isinstance(response, dict) else None
        if not data or not isinstance(data, list):
            raise RuntimeError(f"OpenRouter response for {label} had no image data")

        item = data[0]
        b64 = item.get("b64_json")
        if not b64:
            raise RuntimeError(f"OpenRouter response for {label} had no b64_json field")
        media_type = item.get("media_type", "image/png")
        return base64.b64decode(b64), media_type


def _urllib_transport(url: str, headers: dict[str, str], body: bytes) -> str:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 - fixed API URL
        return response.read().decode("utf-8")
