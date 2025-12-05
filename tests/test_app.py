"""
Tests for Flask application routes and functionality (ADR-003, ADR-124).

Uses mongomock for database testing without requiring a real MongoDB instance.
"""

from __future__ import annotations

import json
import os
import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

if TYPE_CHECKING:
    from flask.testing import FlaskClient


class TestIndexRoute:
    """Tests for the index/dashboard route."""

    def test_index_returns_200(self, client: FlaskClient) -> None:
        """Test that index page returns 200 status."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_contains_dashboard(self, client: FlaskClient) -> None:
        """Test that index page contains dashboard content."""
        response = client.get("/")
        assert b"Dashboard" in response.data or b"dashboard" in response.data.lower()


class TestConversationsRoute:
    """Tests for conversations browser route."""

    def test_conversations_page_returns_200(self, client: FlaskClient) -> None:
        """Test that conversations page returns 200 status."""
        response = client.get("/conversations")
        assert response.status_code == 200


class TestProjectsRoute:
    """Tests for projects browser route."""

    def test_projects_page_returns_200(self, client: FlaskClient) -> None:
        """Test that projects page returns 200 status."""
        response = client.get("/projects")
        assert response.status_code == 200

    def test_projects_pagination_params(self, client: FlaskClient) -> None:
        """Test projects page accepts pagination parameters."""
        response = client.get("/projects?page=1&type=all")
        assert response.status_code == 200

    def test_projects_search_param(self, client: FlaskClient) -> None:
        """Test projects page accepts search parameter."""
        response = client.get("/projects?search=test")
        assert response.status_code == 200


class TestUploadRoute:
    """Tests for file upload route."""

    def test_upload_page_get_returns_200(self, client: FlaskClient) -> None:
        """Test that upload page returns 200 on GET."""
        response = client.get("/upload")
        assert response.status_code == 200

    def test_upload_no_file_shows_error(self, client: FlaskClient) -> None:
        """Test that upload with no file shows error."""
        response = client.post("/upload", data={})
        # Should redirect back with flash message
        assert response.status_code in [200, 302]


class TestSearchConversationsAPI:
    """Tests for conversation search API."""

    def test_search_returns_json(self, client: FlaskClient) -> None:
        """Test that search endpoint returns JSON."""
        response = client.post(
            "/api/search/conversations",
            json={"query": "", "page": 1},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_search_returns_pagination_info(self, client: FlaskClient) -> None:
        """Test that search returns pagination information."""
        response = client.post(
            "/api/search/conversations",
            json={"query": "", "page": 1, "per_page": 10},
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert "pagination" in data
        assert "page" in data["pagination"]
        assert "per_page" in data["pagination"]
        assert "total_count" in data["pagination"]

    def test_search_returns_sort_info(self, client: FlaskClient) -> None:
        """Test that search returns sort information."""
        response = client.post(
            "/api/search/conversations",
            json={"query": "", "sort_by": "created_at", "sort_order": "desc"},
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert "sort_info" in data
        assert data["sort_info"]["sort_by"] == "created_at"
        assert data["sort_info"]["sort_order"] == "desc"


class TestStatsAPI:
    """Tests for statistics API."""

    def test_stats_returns_json(self, client: FlaskClient) -> None:
        """Test that stats endpoint returns JSON."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_stats_contains_counts(self, client: FlaskClient) -> None:
        """Test that stats contains expected count fields."""
        response = client.get("/api/stats")
        data = json.loads(response.data)
        assert "total_conversations" in data
        assert "total_users" in data
        assert "total_projects" in data
        assert "total_imports" in data


class TestAccountsAPI:
    """Tests for accounts API."""

    def test_accounts_returns_list(self, client: FlaskClient) -> None:
        """Test that accounts endpoint returns a list."""
        response = client.get("/api/accounts")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)


class TestConversationDetailAPI:
    """Tests for single conversation API."""

    def test_nonexistent_conversation_returns_404(self, client: FlaskClient) -> None:
        """Test that requesting non-existent conversation returns 404."""
        response = client.get("/api/conversation/nonexistent-uuid")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data


class TestProjectDetailAPI:
    """Tests for single project API."""

    def test_nonexistent_project_returns_404(self, client: FlaskClient) -> None:
        """Test that requesting non-existent project returns 404."""
        response = client.get("/api/project/nonexistent-uuid")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data


class TestRecentItemsAPI:
    """Tests for recent items API."""

    def test_recent_conversations(self, client: FlaskClient) -> None:
        """Test getting recent conversations."""
        response = client.get("/api/recent/conversations")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "items" in data
        assert "pagination" in data

    def test_recent_projects(self, client: FlaskClient) -> None:
        """Test getting recent projects."""
        response = client.get("/api/recent/projects")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "items" in data

    def test_recent_invalid_collection(self, client: FlaskClient) -> None:
        """Test that invalid collection name returns 400."""
        response = client.get("/api/recent/invalid_collection")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestAttachmentAPI:
    """Tests for attachment download API."""

    def test_attachment_nonexistent_conversation(self, client: FlaskClient) -> None:
        """Test attachment from non-existent conversation returns 404."""
        response = client.get("/api/attachment/nonexistent-uuid/0/0")
        assert response.status_code == 404


class TestArtifactAPI:
    """Tests for artifact API."""

    def test_artifact_nonexistent_conversation(self, client: FlaskClient) -> None:
        """Test artifact from non-existent conversation returns 404."""
        response = client.get("/api/artifact/nonexistent-uuid/0/0")
        assert response.status_code == 404


class TestExportAPI:
    """Tests for export API."""

    def test_export_nonexistent_conversation(self, client: FlaskClient) -> None:
        """Test exporting non-existent conversation returns 404."""
        response = client.get("/api/export/conversation/nonexistent-uuid")
        assert response.status_code == 404


class TestAnalyticsRoute:
    """Tests for analytics route."""

    def test_analytics_returns_200(self, client: FlaskClient) -> None:
        """Test that analytics page returns 200."""
        response = client.get("/analytics")
        assert response.status_code == 200


class TestExportRoute:
    """Tests for export page route."""

    def test_export_page_returns_200(self, client: FlaskClient) -> None:
        """Test that export page returns 200."""
        response = client.get("/export")
        assert response.status_code == 200

