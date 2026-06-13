"""
Regression tests that pin the documentation to the code (Findings #2 and #6).

``docs/DATA_DICTIONARY.md`` and ``README.md`` both hand-mirror the route table.
``DATA_DICTIONARY.md`` had already drifted (it omitted ``/stats``,
``/api/stats/timeseries``, ``/api/stats/heatmap`` and several ``Settings``
fields), and the README API table (Finding #6) was structurally unguarded —
correct only by luck — because nothing asserted either doc enumerates what the
code actually exposes.

These tests introspect the live Flask ``url_map`` and the ``Settings`` model and
assert every route is documented in *both* docs and every config field is
documented in the data dictionary. Adding a route or a setting without
documenting it now fails a test — converting silent doc drift into a loud test
failure. See ``drift-risk-map.md`` Findings #2 and #6.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import Settings

if TYPE_CHECKING:
    from flask import Flask

_DOCS_DIR = os.path.dirname(__file__)
_DATA_DICTIONARY_PATH = os.path.join(_DOCS_DIR, "..", "docs", "DATA_DICTIONARY.md")
_README_PATH = os.path.join(_DOCS_DIR, "..", "README.md")


def _read(path: str) -> str:
    """Return the full text of a documentation file."""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _doc_text() -> str:
    """Return the full text of the data dictionary."""
    return _read(_DATA_DICTIONARY_PATH)


def _undocumented_routes(app: Flask, doc: str) -> list[str]:
    """Return the routes whose static prefix does not appear in ``doc``."""
    missing: list[str] = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        prefix = _static_prefix(rule.rule)
        if prefix and prefix not in doc:
            missing.append(rule.rule)
    return missing


def _static_prefix(rule: str) -> str:
    """
    Return the literal portion of a Flask rule, up to its first ``<`` converter.

    This makes the documentation check robust to parameter-name differences
    (the doc may write ``<uuid>`` where the route declares ``<conversation_uuid>``);
    we only require the static path prefix to be documented.
    """
    head = rule.split("<", 1)[0]
    if head == "/":
        return head
    return head.rstrip("/")


def test_every_route_is_documented(app: Flask) -> None:
    """Every non-static Flask route must appear in DATA_DICTIONARY.md (Finding #2)."""
    missing = _undocumented_routes(app, _read(_DATA_DICTIONARY_PATH))
    assert not missing, (
        "Routes missing from docs/DATA_DICTIONARY.md: "
        + ", ".join(sorted(missing))
        + ". Document them (or regenerate the route table) to fix the drift."
    )


def test_every_route_is_documented_in_readme(app: Flask) -> None:
    """Every non-static Flask route must appear in README.md's API table (Finding #6)."""
    missing = _undocumented_routes(app, _read(_README_PATH))
    assert not missing, (
        "Routes missing from README.md API table: "
        + ", ".join(sorted(missing))
        + ". Update the README API Endpoints table to fix the drift."
    )


def test_every_setting_is_documented() -> None:
    """Every Settings field must appear (as its ENV VAR name) in DATA_DICTIONARY.md."""
    doc = _doc_text()
    missing = [name.upper() for name in Settings.model_fields if name.upper() not in doc]
    assert not missing, (
        "Settings fields missing from docs/DATA_DICTIONARY.md: "
        + ", ".join(sorted(missing))
        + ". Add them to the Environment Variables table to fix the drift."
    )
