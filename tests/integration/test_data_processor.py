"""
Integration tests for DataProcessor class (ADR-121).

These tests verify the data processing pipeline works correctly.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import zipfile
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import mongomock
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

if TYPE_CHECKING:
    pass


@pytest.fixture
def data_processor_db() -> mongomock.Database[dict[str, Any]]:
    """Create a mock database for DataProcessor tests."""
    client: mongomock.MongoClient[dict[str, Any]] = mongomock.MongoClient()
    return client["test_data_processor"]


class TestDataProcessorZipProcessing:
    """Integration tests for ZIP file processing."""

    def test_process_zip_creates_import_history(
        self, data_processor_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Test that processing a ZIP creates import history record."""
        # Create test ZIP
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr(
                    "conversations.json",
                    json.dumps(
                        [
                            {
                                "uuid": "conv-1",
                                "name": "Test",
                                "chat_messages": [],
                            }
                        ]
                    ),
                )

            # Patch the db module-level variable
            with patch("app.db", data_processor_db):
                with patch("app.app") as mock_app:
                    mock_app.config = {"UPLOAD_FOLDER": tempfile.gettempdir()}

                    from app import DataProcessor

                    result = DataProcessor.process_zip(tmp.name, "Test Account")

                    assert result["import_id"] is not None
                    assert result["account_name"] == "Test Account"
                    assert result["conversations"]["loaded"] == 1

            os.unlink(tmp.name)

    def test_process_zip_handles_duplicates(
        self, data_processor_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Test that duplicate conversations are detected."""
        # Pre-insert a conversation
        data_processor_db.conversations.insert_one(
            {
                "uuid": "existing-conv",
                "name": "Existing Conversation",
                "_import_ids": ["old-import"],
            }
        )

        # Create ZIP with same UUID
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr(
                    "conversations.json",
                    json.dumps(
                        [
                            {
                                "uuid": "existing-conv",
                                "name": "Updated Name",
                                "chat_messages": [],
                            }
                        ]
                    ),
                )

            with patch("app.db", data_processor_db):
                with patch("app.app") as mock_app:
                    mock_app.config = {"UPLOAD_FOLDER": tempfile.gettempdir()}

                    from app import DataProcessor

                    result = DataProcessor.process_zip(tmp.name, "Test Account")

                    assert result["conversations"]["loaded"] == 0
                    assert result["conversations"]["duplicates"] == 1

            os.unlink(tmp.name)

    def test_process_zip_loads_all_entity_types(
        self, data_processor_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Test that ZIP processing loads conversations, projects, and users."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr(
                    "conversations.json",
                    json.dumps([{"uuid": "conv-1", "name": "Conv", "chat_messages": []}]),
                )
                zf.writestr(
                    "projects.json",
                    json.dumps([{"uuid": "proj-1", "name": "Project"}]),
                )
                zf.writestr(
                    "users.json",
                    json.dumps([{"uuid": "user-1", "email": "test@example.com"}]),
                )

            with patch("app.db", data_processor_db):
                with patch("app.app") as mock_app:
                    mock_app.config = {"UPLOAD_FOLDER": tempfile.gettempdir()}

                    from app import DataProcessor

                    result = DataProcessor.process_zip(tmp.name, "Test Account")

                    assert result["conversations"]["loaded"] == 1
                    assert result["projects"]["loaded"] == 1
                    assert result["users"]["loaded"] == 1

            os.unlink(tmp.name)


class TestDataProcessorIndexes:
    """Tests for database index creation."""

    def test_setup_indexes_creates_conversation_indexes(
        self, data_processor_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Test that conversation indexes are created."""
        with patch("app.db", data_processor_db):
            from app import DataProcessor

            DataProcessor.setup_indexes()

            # Verify indexes exist (mongomock tracks these)
            indexes = list(data_processor_db.conversations.list_indexes())
            index_names = [idx["name"] for idx in indexes]

            # Should have uuid index
            assert any("uuid" in name for name in index_names)

    def test_setup_indexes_creates_project_indexes(
        self, data_processor_db: mongomock.Database[dict[str, Any]]
    ) -> None:
        """Test that project indexes are created."""
        with patch("app.db", data_processor_db):
            from app import DataProcessor

            DataProcessor.setup_indexes()

            indexes = list(data_processor_db.projects.list_indexes())
            index_names = [idx["name"] for idx in indexes]

            assert any("uuid" in name for name in index_names)

