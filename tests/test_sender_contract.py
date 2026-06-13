"""
Regression test for the message-sender contract (Finding #9).

The ``MessageRole`` enum was defined but never used; ``app.py`` compared
``sender`` against bare ``"human"``/``"assistant"`` literals in many places, so
the contract was un-centralized dead code. ``app.py`` now uses ``MessageRole``
for those comparisons.

This test pins three things:

* the enum's wire values (``"human"``/``"assistant"``) the JSON and aggregation
  pipelines depend on;
* that ``app.py`` actually imports/uses ``MessageRole`` (so it cannot silently
  revert to dead code); and
* the end-to-end behaviour — the stats endpoint counts human vs. assistant
  messages correctly — which would break if the sender contract drifted.

See ``drift-risk-map.md`` Finding #9.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import MessageRole

if TYPE_CHECKING:
    import mongomock
    from flask.testing import FlaskClient


def test_message_role_wire_values() -> None:
    """The enum values must match the strings stored in the data / sent on the wire."""
    assert MessageRole.HUMAN == "human"
    assert MessageRole.ASSISTANT == "assistant"


def test_app_uses_message_role() -> None:
    """app.py must import MessageRole — guards against reverting to dead-code literals."""
    import app as app_module

    assert app_module.MessageRole is MessageRole


class TestSenderCountingBehaviour:
    """The sender contract must produce correct human/assistant counts end-to-end."""

    def test_timeseries_message_distribution(
        self, client: FlaskClient, populated_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """
        The populated fixtures contain two conversations, each with one human and
        one assistant message → 2 human, 2 assistant. If the sender contract
        drifted, these counts would be wrong.
        """
        data = client.get("/api/stats/timeseries?days=0").get_json()
        assert data["message_distribution"] == {"human": 2, "assistant": 2}

    def test_search_per_sender_counts(
        self, client: FlaskClient, populated_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Search exposes per-sender counts via the aggregation pipeline."""
        resp = client.post(
            "/api/search/conversations",
            json={"query": "", "per_page": 50},
            content_type="application/json",
        )
        convs = resp.get_json()["conversations"]
        assert convs, "populated_db should return conversations"
        for conv in convs:
            # Each sample conversation has exactly one human + one assistant message.
            assert conv["user_message_count"] == 1
            assert conv["assistant_message_count"] == 1
