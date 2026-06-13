"""
Regression test for the index <-> query-pattern contract (Finding #8).

``DataProcessor.setup_indexes()`` declares the MongoDB indexes; the route
handlers ``$match``/``$sort``/``distinct`` on specific fields. Nothing ties the
two together, so a hot query field can go unindexed (the report found
``_account_name`` filtered/``distinct``'d in many places with no index) — a
silent performance-only drift that no error surfaces.

This test runs ``setup_indexes()`` against a mock database and asserts every
field the handlers query on has a supporting index. Dropping an index for a
still-queried field now fails this test. See ``drift-risk-map.md`` Finding #8.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

if TYPE_CHECKING:
    import mongomock
    from flask import Flask

# Fields the handlers filter/sort/distinct on, which therefore need an index.
# Derived from the query sites in src/app.py (see drift-risk-map.md Finding #8).
EXPECTED_INDEXED_FIELDS: dict[str, set[str]] = {
    "conversations": {"uuid", "account.uuid", "created_at", "name", "_account_name"},
    "users": {"uuid", "email"},
    "projects": {"uuid", "name", "_account_name"},
    "import_history": {"import_id", "timestamp"},
}


def _indexed_fields(db: mongomock.Database[dict[str, Any]], collection: str) -> set[str]:
    """Return the set of fields covered by any index on a collection."""
    fields: set[str] = set()
    for meta in getattr(db, collection).index_information().values():
        for field, _direction in meta["key"]:
            fields.add(field)
    return fields


def test_setup_indexes_covers_queried_fields(
    app: Flask, mock_db: mongomock.Database[dict[str, Any]]
) -> None:
    """Every field the handlers query on must have a supporting index."""
    # The `app` fixture patches `app.db` to `mock_db`; setup_indexes writes there.
    import app as app_module

    app_module.DataProcessor.setup_indexes()

    missing: dict[str, list[str]] = {}
    for collection, expected in EXPECTED_INDEXED_FIELDS.items():
        gap = expected - _indexed_fields(mock_db, collection)
        if gap:
            missing[collection] = sorted(gap)
    assert not missing, (
        "Queried fields without a supporting index (silent perf drift): "
        + str(missing)
        + ". Add the index in DataProcessor.setup_indexes()."
    )
