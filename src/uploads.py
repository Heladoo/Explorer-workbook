"""Minimal multipart/form-data parsing, for the photo upload on the web form.

``cgi.FieldStorage`` is deprecated and gone in 3.13, and the project takes no
dependencies, so this parses the little of RFC 7578 that a file input needs.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import HTTP

#: Image types we accept, mapped to the extension we save them under. The
#: browser's declared type is a hint; the signature below is what we trust.
IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/gif": ".gif",
}

#: Leading bytes that identify each format, so a renamed file cannot sneak past.
_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
)


class UploadError(ValueError):
    """The submitted body could not be read as a form."""


@dataclass(frozen=True)
class Upload:
    """One uploaded file."""

    field: str
    filename: str
    content_type: str
    data: bytes

    @property
    def extension(self) -> str:
        """The extension to save under, decided by content rather than by name."""
        for signature, suffix in _SIGNATURES:
            if self.data.startswith(signature):
                return suffix
        if self.data[8:12] == b"WEBP":
            return ".webp"
        if self.data[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1"):
            return ".heic"
        return IMAGE_TYPES.get(self.content_type.split(";")[0].strip().lower(), "")

    @property
    def looks_like_an_image(self) -> bool:
        return bool(self.extension)


def parse_multipart(body: bytes, content_type: str) -> tuple[dict[str, list[str]], list[Upload]]:
    """Split a multipart body into text fields and uploaded files.

    Returns the same ``{name: [values]}`` shape as ``urllib.parse.parse_qs`` so
    callers can treat both encodings alike.
    """
    boundary = _boundary(content_type)
    fields: dict[str, list[str]] = {}
    uploads: list[Upload] = []

    delimiter = b"--" + boundary
    for chunk in body.split(delimiter)[1:]:
        if chunk[:2] == b"--":  # closing delimiter, nothing after it matters
            break
        chunk = chunk[2:] if chunk[:2] == b"\r\n" else chunk.lstrip(b"\r\n")
        headers_blob, separator, payload = chunk.partition(b"\r\n\r\n")
        if not separator:
            continue
        if payload.endswith(b"\r\n"):
            payload = payload[:-2]

        headers = BytesParser(policy=HTTP).parsebytes(headers_blob)
        disposition = headers.get("content-disposition", "")
        name = _param(disposition, "name")
        if not name:
            continue
        filename = _param(disposition, "filename")

        if filename is None:
            fields.setdefault(name, []).append(payload.decode("utf-8", "replace"))
        elif payload:  # an empty file input submits a nameless, empty part
            uploads.append(
                Upload(
                    field=name,
                    filename=filename,
                    content_type=headers.get("content-type", ""),
                    data=payload,
                )
            )
    return fields, uploads


def safe_stem(filename: str, fallback: str) -> str:
    """A filename we are willing to write: no paths, no surprises."""
    stem = filename.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    folded = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", folded).strip("-._")
    return cleaned[:40] or fallback


def _boundary(content_type: str) -> bytes:
    match = re.search(r'boundary="?([^";]+)"?', content_type or "", re.IGNORECASE)
    if not match:
        raise UploadError("that form submission was missing its multipart boundary")
    return match.group(1).strip().encode("utf-8")


def _param(header: str, name: str) -> str | None:
    """Read one parameter out of a header value, quoted or not."""
    match = re.search(rf'{name}="([^"]*)"', header) or re.search(
        rf"{name}=([^;]+)", header
    )
    return match.group(1).strip() if match else None
