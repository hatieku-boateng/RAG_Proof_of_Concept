"""Compatibility shim for the deprecated stdlib 'imghdr' module.

This module provides a minimal implementation of the old standard library
`imghdr` interface so that code which still does ``import imghdr`` continues
to work on Python versions where the original module has been removed
(e.g. Python 3.13+).

Only the public function :func:`what` is implemented, which is what most
libraries use. It can detect a few common image formats based on their
header bytes: JPEG, PNG, GIF, BMP and WebP.
"""

from __future__ import annotations

from typing import BinaryIO, Optional, Union
import os

__all__ = ["what"]

PathLike = Union[str, os.PathLike]


def _read_header(file: Union[PathLike, BinaryIO], length: int = 32) -> bytes:
    """Read up to ``length`` bytes from *file* without changing its position.

    *file* may be a path or a binary file-like object.
    """

    if hasattr(file, "read"):
        f = file  # type: ignore[assignment]
        try:
            pos = f.tell()
        except Exception:
            # If tell/seek are not supported, just read
            return f.read(length) or b""
        try:
            data = f.read(length) or b""
        finally:
            try:
                f.seek(pos)
            except Exception:
                pass
        return data

    # Assume it is a filesystem path
    with open(file, "rb") as f:  # type: ignore[arg-type]
        return f.read(length) or b""


def what(file: Union[PathLike, BinaryIO], h: Optional[bytes] = None) -> Optional[str]:
    """Guess the type of an image.

    This mirrors the interface of the original :mod:`imghdr.what`:

    - *file* may be a path or a binary file-like object.
    - *h* is an optional bytes header; if not provided, it is read from *file*.

    Returns a lower-case string such as ``"jpeg"`` or ``"png"`` if the
    format can be determined, or ``None`` if it cannot.
    """

    if h is None:
        h = _read_header(file)
    if not h:
        return None

    # JPEG: starts with 0xFFD8 (Start Of Image)
    if h[:2] == b"\xff\xd8":
        return "jpeg"

    # PNG: 8-byte fixed signature
    if h[:8] == b"\211PNG\r\n\032\n":
        return "png"

    # GIF87a / GIF89a
    if h[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"

    # BMP: "BM"
    if h[:2] == b"BM":
        return "bmp"

    # WebP: RIFF....WEBP
    if h[:4] == b"RIFF" and h[8:12] == b"WEBP":
        return "webp"

    # Fallback: unknown/unsupported format
    return None
