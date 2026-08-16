"""OpenRouterImageBackend and the runner that drives it over a workbook."""

from __future__ import annotations

import base64
import json

import pytest

from src.image_backends.openrouter import OpenRouterImageBackend
from src.image_backends.runner import generate_images, generate_symbol_images
from src.models.context import WorkbookContext
from src.models.page import Page, SymbolBrief

# A 1x1 transparent PNG, just enough bytes to round-trip through base64.
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _page(
    number: int = 1,
    image_prompt: str = "a friendly camel, storybook style",
    symbols: tuple[SymbolBrief, ...] = (),
) -> Page:
    return Page(
        number=number,
        type="coloring",
        title="Meet a Camel",
        instructions="Color the camel.",
        image_prompt=image_prompt,
        symbols=symbols,
    )


def _symbol(key: str = "stop-sign", prompt: str = "Draw one stop sign.") -> SymbolBrief:
    return SymbolBrief(key=key, label="a stop sign", subject="a stop sign", prompt=prompt)


def _api_response(b64: bytes = None, media_type: str = "image/png") -> str:
    return json.dumps(
        {"data": [{"b64_json": base64.b64encode(b64 or TINY_PNG).decode("ascii"), "media_type": media_type}]}
    )


def test_backend_without_key_raises(tmp_path):
    backend = OpenRouterImageBackend(api_key="")
    with pytest.raises(RuntimeError, match="API key"):
        backend.generate(_page(), WorkbookContext(destination="Prague"), output_dir=tmp_path)


def test_backend_sends_the_prompt_and_writes_the_decoded_image(tmp_path):
    captured: dict[str, object] = {}

    def transport(url, headers, body):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = json.loads(body)
        return _api_response()

    backend = OpenRouterImageBackend(api_key="test-key", transport=transport)
    page = _page()
    path = backend.generate(page, WorkbookContext(destination="Prague"), output_dir=tmp_path)

    assert captured["url"] == "https://openrouter.ai/api/v1/images"
    assert captured["headers"]["authorization"] == "Bearer test-key"
    assert captured["body"]["model"] == "openai/gpt-image-1"
    assert captured["body"]["prompt"] == page.image_prompt
    assert path == tmp_path / "01_coloring.png"
    assert path.read_bytes() == TINY_PNG


def test_backend_attaches_family_photos_as_input_references(tmp_path):
    photo = tmp_path / "noa.jpg"
    photo.write_bytes(b"not a real jpeg, just bytes")
    captured: dict[str, object] = {}

    def transport(url, headers, body):
        captured["body"] = json.loads(body)
        return _api_response()

    backend = OpenRouterImageBackend(api_key="k", transport=transport)
    context = WorkbookContext(destination="Prague", family_photos=(str(photo),))
    backend.generate(_page(), context, output_dir=tmp_path)

    references = captured["body"]["input_references"]
    assert len(references) == 1
    assert references[0]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_backend_skips_a_missing_family_photo(tmp_path):
    def transport(url, headers, body):
        return _api_response()

    backend = OpenRouterImageBackend(api_key="k", transport=transport)
    context = WorkbookContext(destination="Prague", family_photos=(str(tmp_path / "missing.jpg"),))
    # Should not raise, just skip the reference.
    backend.generate(_page(), context, output_dir=tmp_path)


def test_backend_raises_on_an_error_response(tmp_path):
    backend = OpenRouterImageBackend(
        api_key="k", transport=lambda *a: json.dumps({"error": {"message": "bad prompt"}})
    )
    with pytest.raises(RuntimeError, match="bad prompt"):
        backend.generate(_page(), WorkbookContext(destination="Prague"), output_dir=tmp_path)


def test_backend_raises_when_the_transport_fails(tmp_path):
    def transport(*args):
        raise TimeoutError("network down")

    backend = OpenRouterImageBackend(api_key="k", transport=transport)
    with pytest.raises(RuntimeError, match="network down"):
        backend.generate(_page(), WorkbookContext(destination="Prague"), output_dir=tmp_path)


def test_backend_declines_a_page_with_no_prompt(tmp_path):
    backend = OpenRouterImageBackend(api_key="k", transport=lambda *a: _api_response())
    with pytest.raises(ValueError, match="image_prompt"):
        backend.generate(_page(image_prompt=""), WorkbookContext(destination="Prague"), output_dir=tmp_path)


# -- runner ---------------------------------------------------------------


class _StubWorkbook:
    def __init__(self, pages):
        self.pages = pages


def test_runner_collects_paths_per_page(tmp_path):
    class Backend:
        name = "stub"

        def generate(self, page, context, *, output_dir):
            path = output_dir / f"{page.number}.png"
            path.write_bytes(b"img")
            return path

    workbook = _StubWorkbook([_page(1), _page(2)])
    images = generate_images(workbook, WorkbookContext(destination="Prague"), Backend(), output_dir=tmp_path)

    assert set(images) == {1, 2}


def test_runner_skips_a_page_that_fails_and_keeps_going(tmp_path):
    class Backend:
        name = "stub"

        def generate(self, page, context, *, output_dir):
            if page.number == 1:
                raise RuntimeError("boom")
            path = output_dir / f"{page.number}.png"
            path.write_bytes(b"img")
            return path

    workbook = _StubWorkbook([_page(1), _page(2)])
    images = generate_images(workbook, WorkbookContext(destination="Prague"), Backend(), output_dir=tmp_path)

    assert set(images) == {2}


def test_symbols_are_named_by_slug_not_page(tmp_path):
    backend = OpenRouterImageBackend(api_key="k", transport=lambda *a: _api_response())
    path = backend.generate_symbol(
        _symbol(), WorkbookContext(destination="Prague"), output_dir=tmp_path
    )
    assert path == tmp_path / "stop-sign.png"


def test_a_symbol_request_never_attaches_family_photos(tmp_path):
    """A symbol has no people in it, and an identical request everywhere is
    exactly what makes one drawing reusable across books."""
    photo = tmp_path / "noa.jpg"
    photo.write_bytes(b"bytes")
    captured: dict[str, object] = {}

    def transport(url, headers, body):
        captured["body"] = json.loads(body)
        return _api_response()

    backend = OpenRouterImageBackend(api_key="k", transport=transport)
    context = WorkbookContext(destination="Prague", family_photos=(str(photo),))
    backend.generate_symbol(_symbol(), context, output_dir=tmp_path)

    assert "input_references" not in captured["body"]
    assert captured["body"]["prompt"] == "Draw one stop sign."


def test_a_symbol_without_a_prompt_is_refused(tmp_path):
    backend = OpenRouterImageBackend(api_key="k", transport=lambda *a: _api_response())
    with pytest.raises(ValueError, match="no prompt"):
        backend.generate_symbol(
            _symbol(prompt=""), WorkbookContext(destination="Prague"), output_dir=tmp_path
        )


# -- symbol runner --------------------------------------------------------


class _CountingBackend:
    name = "counting"

    def __init__(self):
        self.calls: list[str] = []

    def generate(self, page, context, *, output_dir):
        raise AssertionError("not used in these tests")

    def generate_symbol(self, symbol, context, *, output_dir):
        self.calls.append(symbol.key)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{symbol.key}.png"
        path.write_bytes(b"img")
        return path


def test_a_symbol_repeated_across_pages_is_drawn_once(tmp_path):
    backend = _CountingBackend()
    workbook = _StubWorkbook(
        [
            _page(1, symbols=(_symbol("stop-sign"), _symbol("bridge"))),
            _page(2, symbols=(_symbol("stop-sign"), _symbol("bus"))),
        ]
    )

    images = generate_symbol_images(
        workbook, WorkbookContext(destination="Prague"), backend, output_dir=tmp_path
    )

    assert backend.calls == ["stop-sign", "bridge", "bus"]
    assert set(images) == {"stop-sign", "bridge", "bus"}


def test_an_already_drawn_symbol_is_reused_instead_of_regenerated(tmp_path):
    """The whole point of a shared symbol directory: pay for a stop sign once."""
    existing = tmp_path / "stop-sign.png"
    existing.write_bytes(b"cached")
    backend = _CountingBackend()
    workbook = _StubWorkbook([_page(1, symbols=(_symbol("stop-sign"), _symbol("bridge")))])

    images = generate_symbol_images(
        workbook, WorkbookContext(destination="Prague"), backend, output_dir=tmp_path
    )

    assert backend.calls == ["bridge"], "the cached stop sign must not be regenerated"
    assert images["stop-sign"] == existing
    assert images["stop-sign"].read_bytes() == b"cached"


def test_the_cache_can_be_bypassed(tmp_path):
    (tmp_path / "stop-sign.png").write_bytes(b"cached")
    backend = _CountingBackend()
    workbook = _StubWorkbook([_page(1, symbols=(_symbol("stop-sign"),))])

    generate_symbol_images(
        workbook,
        WorkbookContext(destination="Prague"),
        backend,
        output_dir=tmp_path,
        reuse_existing=False,
    )

    assert backend.calls == ["stop-sign"]


def test_one_failing_symbol_does_not_cost_the_others(tmp_path):
    class Backend(_CountingBackend):
        def generate_symbol(self, symbol, context, *, output_dir):
            if symbol.key == "bridge":
                raise RuntimeError("boom")
            return super().generate_symbol(symbol, context, output_dir=output_dir)

    workbook = _StubWorkbook([_page(1, symbols=(_symbol("bridge"), _symbol("bus")))])
    images = generate_symbol_images(
        workbook, WorkbookContext(destination="Prague"), Backend(), output_dir=tmp_path
    )
    assert set(images) == {"bus"}


def test_a_backend_that_cannot_draw_symbols_is_tolerated(tmp_path):
    class PageOnlyBackend:
        name = "page-only"

        def generate(self, page, context, *, output_dir):
            raise AssertionError("not used here")

    workbook = _StubWorkbook([_page(1, symbols=(_symbol("bus"),))])
    images = generate_symbol_images(
        workbook, WorkbookContext(destination="Prague"), PageOnlyBackend(), output_dir=tmp_path
    )
    assert images == {}


def test_runner_skips_pages_with_no_image_prompt(tmp_path):
    class Backend:
        name = "stub"

        def generate(self, page, context, *, output_dir):
            raise AssertionError("should not be called for a page with no prompt")

    workbook = _StubWorkbook([_page(1, image_prompt="")])
    images = generate_images(workbook, WorkbookContext(destination="Prague"), Backend(), output_dir=tmp_path)

    assert images == {}
