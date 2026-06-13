"""
Regression test for the frontend-path -> backend-route contract (Finding #3).

The template JavaScript restates backend routes as hardcoded ``fetch('/api/...')``
string literals. Nothing links those strings to the Flask ``url_map``: rename or
delete a route and the page 404s at runtime only — no build, type, or test error.

This test extracts every ``/api/...`` path literal from ``src/templates/*.html``
and asserts each one resolves to a registered Flask route. A renamed or removed
route now fails this test instead of silently 404-ing in the browser. See
``drift-risk-map.md`` Finding #3.
"""

from __future__ import annotations

import glob
import os
import re
import sys
from typing import TYPE_CHECKING

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

if TYPE_CHECKING:
    from flask import Flask

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "templates")

# Matches the static portion of an API path up to the first JS interpolation
# (``${...}``), quote, backtick, or whitespace — e.g. ``/api/conversation/`` from
# ``fetch(`/api/conversation/${uuid}`)``.
_API_PATH_RE = re.compile(r"/api/[A-Za-z0-9_/-]+")


def _template_api_paths() -> set[str]:
    """Collect every distinct ``/api/...`` literal referenced in the templates."""
    paths: set[str] = set()
    for html in glob.glob(os.path.join(_TEMPLATES_DIR, "*.html")):
        with open(html, encoding="utf-8") as fh:
            paths.update(_API_PATH_RE.findall(fh.read()))
    return paths


def _route_static_prefixes(app: Flask) -> list[str]:
    """Static prefix (portion before the first ``<`` converter) of every route."""
    prefixes: list[str] = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        prefixes.append(rule.rule.split("<", 1)[0])
    return prefixes


def _resolves(path: str, prefixes: list[str]) -> bool:
    """
    True if a template path is consistent with some registered route.

    A template literal may be a static prefix of a parameterised route
    (``/api/conversation/`` for ``/api/conversation/<uuid>``) or a fully static
    route (``/api/stats/timeseries``). Accept either containment direction so
    partially-built dynamic URLs still match, while a typo'd or removed path
    (matching no route) fails.
    """
    norm = path.rstrip("/")
    for prefix in prefixes:
        pnorm = prefix.rstrip("/")
        if norm == pnorm or norm.startswith(pnorm + "/") or pnorm.startswith(norm + "/"):
            return True
    return False


def test_template_api_paths_resolve_to_routes(app: Flask) -> None:
    """Every ``/api/...`` literal in the templates must map to a Flask route."""
    prefixes = _route_static_prefixes(app)
    template_paths = _template_api_paths()
    assert template_paths, "No /api/ paths found in templates — check the matcher."

    unresolved = sorted(p for p in template_paths if not _resolves(p, prefixes))
    assert not unresolved, (
        "Template /api/ paths with no matching Flask route (silent 404 risk): "
        + ", ".join(unresolved)
        + ". A route was renamed/removed without updating the template fetch() call."
    )
