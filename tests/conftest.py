"""
Pytest fixtures and configuration (ADR-003, ADR-121, ADR-122).

This module provides shared fixtures for all tests.
Uses mongomock for database testing without requiring a real MongoDB instance.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import zipfile
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generator
from unittest.mock import MagicMock, patch

import mongomock
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


@pytest.fixture(scope="session")
def mock_mongo_client() -> Generator[mongomock.MongoClient[dict[str, Any]], None, None]:
    """Create a mock MongoDB client for testing."""
    client: mongomock.MongoClient[dict[str, Any]] = mongomock.MongoClient()
    yield client
    client.close()


@pytest.fixture
def mock_db(
    mock_mongo_client: mongomock.MongoClient[dict[str, Any]],
) -> Generator[mongomock.Database[dict[str, Any]], None, None]:
    """Create a fresh mock database for each test."""
    db = mock_mongo_client["test_anthropic_data"]
    yield db
    # Clean up after each test
    mock_mongo_client.drop_database("test_anthropic_data")


@pytest.fixture
def app(mock_db: mongomock.Database[dict[str, Any]]) -> Generator[Flask, None, None]:
    """Create Flask application for testing."""
    # Patch MongoDB before importing app
    with patch("app.MongoClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__getitem__ = MagicMock(return_value=mock_db)
        mock_client_class.return_value = mock_client

        # Also patch the db global
        with patch("app.db", mock_db):
            from app import app as flask_app

            flask_app.config.update(
                {
                    "TESTING": True,
                    "SECRET_KEY": "test-secret-key",
                    "UPLOAD_FOLDER": tempfile.mkdtemp(),
                }
            )

            yield flask_app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client for Flask application."""
    return app.test_client()


@pytest.fixture
def sample_conversation() -> dict[str, Any]:
    """Create a sample conversation for testing."""
    return {
        "uuid": "test-conv-uuid-123",
        "name": "Test Conversation",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z",
        "account": {"uuid": "test-account-uuid"},
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "human",
                "text": "Hello, Claude!",
                "created_at": "2024-01-15T10:00:00Z",
                "attachments": [],
            },
            {
                "uuid": "msg-2",
                "sender": "assistant",
                "text": "Hello! How can I help you today?",
                "created_at": "2024-01-15T10:00:05Z",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello! How can I help you today?",
                    }
                ],
            },
        ],
    }


@pytest.fixture
def sample_conversation_with_attachments() -> dict[str, Any]:
    """Create a sample conversation with attachments for testing."""
    return {
        "uuid": "test-conv-attach-uuid-456",
        "name": "Conversation with Attachments",
        "created_at": "2024-01-20T14:00:00Z",
        "updated_at": "2024-01-20T16:00:00Z",
        "account": {"uuid": "test-account-uuid"},
        "chat_messages": [
            {
                "uuid": "msg-1",
                "sender": "human",
                "text": "Here is a file for analysis.",
                "created_at": "2024-01-20T14:00:00Z",
                "attachments": [
                    {
                        "file_name": "test_file.txt",
                        "file_type": "txt",
                        "file_size": 1024,
                        "extracted_content": "This is the content of the test file.",
                    }
                ],
            },
            {
                "uuid": "msg-2",
                "sender": "assistant",
                "text": "I've analyzed your file.",
                "created_at": "2024-01-20T14:01:00Z",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "Let me analyze this file...",
                    },
                    {
                        "type": "text",
                        "text": "I've analyzed your file and found...",
                        "summaries": [{"summary": "File analysis complete"}],
                    },
                ],
            },
        ],
    }


@pytest.fixture
def sample_project() -> dict[str, Any]:
    """Create a sample project for testing."""
    return {
        "uuid": "test-project-uuid-789",
        "name": "Test Project",
        "description": "A test project for unit tests",
        "creator": "test-user",
        "is_private": False,
        "is_starter_project": False,
        "created_at": "2024-01-10T08:00:00Z",
        "updated_at": "2024-01-10T08:00:00Z",
        "docs": [
            {
                "uuid": "doc-1",
                "filename": "README.md",
                "content": "# Test Project\n\nThis is a test.",
            }
        ],
        "prompt_template": [
            {
                "uuid": "template-1",
                "filename": "main_template.txt",
                "content": "You are a helpful assistant.",
            }
        ],
    }


@pytest.fixture
def sample_user() -> dict[str, Any]:
    """Create a sample user for testing."""
    return {
        "uuid": "test-user-uuid-001",
        "email": "test@example.com",
        "name": "Test User",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_zip_file(
    sample_conversation: dict[str, Any],
    sample_project: dict[str, Any],
    sample_user: dict[str, Any],
) -> Generator[str, None, None]:
    """Create a sample ZIP file for upload testing."""
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        with zipfile.ZipFile(tmp.name, "w") as zf:
            # Add conversations.json
            zf.writestr(
                "conversations.json",
                json.dumps([sample_conversation]),
            )
            # Add projects.json
            zf.writestr(
                "projects.json",
                json.dumps([sample_project]),
            )
            # Add users.json
            zf.writestr(
                "users.json",
                json.dumps([sample_user]),
            )

        yield tmp.name

    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture
def populated_db(
    mock_db: mongomock.Database[dict[str, Any]],
    sample_conversation: dict[str, Any],
    sample_conversation_with_attachments: dict[str, Any],
    sample_project: dict[str, Any],
    sample_user: dict[str, Any],
) -> mongomock.Database[dict[str, Any]]:
    """Create a database populated with sample data."""
    # Add metadata
    sample_conversation["_account_name"] = "Test Account"
    sample_conversation["_import_id"] = "test-import-001"
    sample_conversation["_imported_at"] = datetime.now()

    sample_conversation_with_attachments["_account_name"] = "Test Account"
    sample_conversation_with_attachments["_import_id"] = "test-import-001"
    sample_conversation_with_attachments["_imported_at"] = datetime.now()

    sample_project["_account_name"] = "Test Account"
    sample_project["_import_id"] = "test-import-001"
    sample_project["_imported_at"] = datetime.now()

    sample_user["_account_name"] = "Test Account"
    sample_user["_import_id"] = "test-import-001"
    sample_user["_imported_at"] = datetime.now()

    # Insert data
    mock_db.conversations.insert_many(
        [sample_conversation, sample_conversation_with_attachments]
    )
    mock_db.projects.insert_one(sample_project)
    mock_db.users.insert_one(sample_user)
    mock_db.import_history.insert_one(
        {
            "import_id": "test-import-001",
            "account_name": "Test Account",
            "timestamp": datetime.now(),
            "conversations": {"loaded": 2, "duplicates": 0},
            "projects": {"loaded": 1, "duplicates": 0},
            "users": {"loaded": 1, "duplicates": 0},
        }
    )

    return mock_db

