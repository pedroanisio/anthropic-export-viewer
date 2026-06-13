"""
Regression tests for API response contracts (drift-risk Finding #1).

The frontend templates read API response fields by bare key. Nothing links
those reads to the dicts ``app.py`` passes to ``jsonify(...)``, so a renamed or
dropped backend field silently breaks the UI. These tests pin each consumed
endpoint's JSON shape to a ``response_models`` contract (``extra="forbid"``):
if the backend response gains, loses, or retypes a field, ``model_validate``
raises and the test fails — converting silent drift into a loud test failure.

See ``src/response_models.py`` for the contracts and ``drift-risk-map.md``
Finding #1 for the rationale.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from response_models import (
    HeatmapResponse,
    SearchConversationsResponse,
    TimeseriesResponse,
)

if TYPE_CHECKING:
    import mongomock
    from flask.testing import FlaskClient


class TestTimeseriesContract:
    """Contract for ``GET /api/stats/timeseries``."""

    def test_timeseries_with_data_matches_contract(
        self, client: FlaskClient, populated_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Populated, all-time timeseries output conforms to the contract."""
        # days=0 disables the date filter so the 2024 sample data is included.
        response = client.get("/api/stats/timeseries?days=0")
        assert response.status_code == 200
        # Raises ValidationError (test failure) on any added/renamed/dropped key.
        TimeseriesResponse.model_validate(response.get_json())

    def test_timeseries_empty_db_matches_contract(self, client: FlaskClient) -> None:
        """Empty-database timeseries output still conforms to the contract."""
        response = client.get("/api/stats/timeseries?days=30")
        assert response.status_code == 200
        TimeseriesResponse.model_validate(response.get_json())


class TestHeatmapContract:
    """Contract for ``GET /api/stats/heatmap``."""

    def test_heatmap_with_data_matches_contract(
        self, client: FlaskClient, populated_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Heatmap for a year containing sample data conforms to the contract."""
        response = client.get("/api/stats/heatmap?year=2024")
        assert response.status_code == 200
        model = HeatmapResponse.model_validate(response.get_json())
        assert model.year == 2024

    def test_heatmap_empty_year_matches_contract(
        self, client: FlaskClient, populated_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Heatmap for a year with no data still conforms (zero branch)."""
        response = client.get("/api/stats/heatmap?year=1999")
        assert response.status_code == 200
        model = HeatmapResponse.model_validate(response.get_json())
        assert model.stats.active_days == 0


class TestSearchConversationsContract:
    """Contract for ``POST /api/search/conversations``."""

    def test_search_with_data_matches_contract(
        self, client: FlaskClient, populated_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Populated search output conforms to the contract."""
        response = client.post(
            "/api/search/conversations",
            json={"query": "", "page": 1, "per_page": 20},
            content_type="application/json",
        )
        assert response.status_code == 200
        model = SearchConversationsResponse.model_validate(response.get_json())
        assert model.pagination.total_count == len(model.conversations)

    def test_search_empty_db_matches_contract(self, client: FlaskClient) -> None:
        """Empty-database search output still conforms to the contract."""
        response = client.post(
            "/api/search/conversations",
            json={"query": "", "page": 1},
            content_type="application/json",
        )
        assert response.status_code == 200
        model = SearchConversationsResponse.model_validate(response.get_json())
        assert model.conversations == []


@pytest.mark.parametrize(
    "field",
    [
        "summary",
        "time_series",
        "message_distribution",
        "account_distribution",
        "length_distribution",
    ],
)
def test_timeseries_contract_rejects_renamed_field(client: FlaskClient, field: str) -> None:
    """
    The contract is strict: dropping/renaming a top-level field must fail.

    This guards the guard — it proves ``extra="forbid"`` plus required fields
    actually reject the drift scenario from Finding #1 (a renamed response key),
    rather than silently accepting it.
    """
    payload = client.get("/api/stats/timeseries?days=0").get_json()
    # Simulate the backend renaming/dropping a field the frontend depends on.
    payload.pop(field)
    payload["renamed_" + field] = None
    with pytest.raises(ValidationError):
        TimeseriesResponse.model_validate(payload)
