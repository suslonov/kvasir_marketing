"""Hub path normalization (mount prefix stripping)."""

from __future__ import annotations

from src.hub_module import normalize_hub_rel_path


def test_no_prefix_passthrough() -> None:
    assert normalize_hub_rel_path("", "/api/re-render") == "/api/re-render"
    assert normalize_hub_rel_path("", "/mods/x/index.html") == "/mods/x/index.html"


def test_strip_prefix_for_api() -> None:
    assert normalize_hub_rel_path("/mods/scanner", "/mods/scanner/api/re-render") == "/api/re-render"


def test_mount_root_maps_to_slash() -> None:
    assert normalize_hub_rel_path("/mods/scanner", "/mods/scanner") == "/"
    assert normalize_hub_rel_path("/mods/scanner", "/mods/scanner/") == "/"

