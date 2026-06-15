"""
Tests for Flask application routes and functionality (ADR-003, ADR-124).

Uses mongomock for database testing without requiring a real MongoDB instance.
"""

from __future__ import annotations

import json
import os
import sys
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

if TYPE_CHECKING:
    from flask.testing import FlaskClient
    from pytest import MonkeyPatch


def _app_module() -> Any:
    import app as app_module

    return app_module


class TestIndexRoute:
    """Tests for the index/dashboard route."""

    def test_index_returns_200(self, client: FlaskClient) -> None:
        """Test that index page returns 200 status."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_contains_dashboard(self, client: FlaskClient) -> None:
        """Test that index page contains workspace content."""
        response = client.get("/")
        assert b"Archive Workbench" in response.data


class TestHealthRoute:
    """Tests for the health check route."""

    def test_health_returns_200(self, client: FlaskClient) -> None:
        """Test that health endpoint returns 200 when the database responds."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_503_when_database_ping_fails(
        self,
        client: FlaskClient,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test health endpoint reports database failures."""

        class FailingDb:
            def command(self, _command: str) -> None:
                raise RuntimeError("database down")

        monkeypatch.setattr(_app_module(), "db", FailingDb())

        response = client.get("/health")

        assert response.status_code == 503
        assert response.json == {"status": "unhealthy", "database": "unavailable"}


class TestProductionAuthentication:
    """Tests for app-wide production Basic Auth."""

    def test_production_requires_basic_auth(
        self,
        client: FlaskClient,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test that production mode rejects unauthenticated requests."""
        monkeypatch.setattr(
            _app_module(),
            "settings",
            SimpleNamespace(
                is_production=True,
                app_basic_auth_username="admin",
                app_basic_auth_password="strong-production-password",
            ),
        )

        response = client.get("/")

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == 'Basic realm="Anthropic Export Viewer"'

    def test_health_bypasses_production_basic_auth(
        self,
        client: FlaskClient,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test that health checks do not require Basic Auth."""
        monkeypatch.setattr(
            _app_module(),
            "settings",
            SimpleNamespace(
                is_production=True,
                app_basic_auth_username="admin",
                app_basic_auth_password="strong-production-password",
            ),
        )

        response = client.get("/health")

        assert response.status_code == 200

    def test_production_allows_valid_basic_auth(
        self,
        client: FlaskClient,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test that production mode accepts valid Basic Auth credentials."""
        monkeypatch.setattr(
            _app_module(),
            "settings",
            SimpleNamespace(
                is_production=True,
                app_basic_auth_username="admin",
                app_basic_auth_password="strong-production-password",
            ),
        )

        response = client.get(
            "/",
            headers={"Authorization": "Basic YWRtaW46c3Ryb25nLXByb2R1Y3Rpb24tcGFzc3dvcmQ="},
        )

        assert response.status_code == 200


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

    def test_projects_filters_with_data(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test project list filters and computed project counts."""
        public_response = client.get("/projects?type=public&search=Test&page=1")
        private_response = client.get("/projects?type=private")
        starter_response = client.get("/projects?type=starter")

        assert public_response.status_code == 200
        assert private_response.status_code == 200
        assert starter_response.status_code == 200


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

    def test_upload_empty_filename_redirects(self, client: FlaskClient) -> None:
        """Test upload rejects empty filenames."""
        response = client.post(
            "/upload",
            data={"file": (BytesIO(b""), ""), "account_name": "Test"},
            content_type="multipart/form-data",
        )

        assert response.status_code == 302

    def test_upload_non_zip_renders_page(self, client: FlaskClient) -> None:
        """Test upload ignores unsupported file types and renders the page."""
        response = client.post(
            "/upload",
            data={"file": (BytesIO(b"not zip"), "export.txt"), "account_name": "Test"},
            content_type="multipart/form-data",
        )

        assert response.status_code == 200

    def test_upload_zip_success_redirects(self, client: FlaskClient) -> None:
        """Test successful ZIP upload delegates processing and removes the upload."""
        with patch.object(
            _app_module().DataProcessor,
            "process_zip",
            return_value={
                "conversations": {"loaded": 1},
                "users": {"loaded": 2},
                "projects": {"loaded": 3},
            },
        ) as process_zip:
            response = client.post(
                "/upload",
                data={"file": (BytesIO(b"fake zip bytes"), "export.zip"), "account_name": "Work"},
                content_type="multipart/form-data",
            )

        assert response.status_code == 302
        process_zip.assert_called_once()

    def test_upload_zip_processing_error_redirects(self, client: FlaskClient) -> None:
        """Test upload processing failures redirect back to upload."""
        with patch.object(
            _app_module().DataProcessor,
            "process_zip",
            side_effect=ValueError("bad zip"),
        ):
            response = client.post(
                "/upload",
                data={"file": (BytesIO(b"fake zip bytes"), "export.zip"), "account_name": "Work"},
                content_type="multipart/form-data",
            )

        assert response.status_code == 302


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

    def test_search_filters_and_sort_variants(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test search filters, pagination bounds, and computed sort fields."""
        response = client.post(
            "/api/search/conversations",
            json={
                "query": "",
                "filters": {
                    "account": "Test Account",
                    "date_from": "2024-01-15",
                    "date_to": "2024-01-15",
                    "has_attachments": True,
                },
                "page": -10,
                "per_page": 1000,
                "sort_by": "message_count",
                "sort_order": "asc",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 100
        assert data["sort_info"] == {"sort_by": "message_count", "sort_order": "asc"}

    def test_search_date_range_and_name_sort(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test date-range and name sort branches."""
        response = client.post(
            "/api/search/conversations",
            json={
                "filters": {"date_from": "2024-01-01", "date_to": "2024-01-31"},
                "sort_by": "name",
                "sort_order": "desc",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        assert json.loads(response.data)["sort_info"]["sort_by"] == "name"

    def test_search_single_start_date_filter(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test open-ended date filter branch."""
        response = client.post(
            "/api/search/conversations",
            json={"filters": {"date_from": "2024-01-01"}, "sort_by": "updated_at"},
            content_type="application/json",
        )

        assert response.status_code == 200


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

    def test_stats_with_populated_database(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test statistics aggregation with existing data."""
        response = client.get("/api/stats")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["total_conversations"] == 2
        assert "Test Account" in data["accounts"]

    def test_timeseries_all_time_with_data(
        self,
        client: FlaskClient,
        populated_db: Any,
        mock_db: Any,
    ) -> None:
        """Test time-series statistics with valid, invalid, and datetime dates."""
        mock_db.conversations.insert_one(
            {
                "uuid": "datetime-conv",
                "name": "Datetime",
                "created_at": datetime(2024, 2, 1, 8, 30),
                "updated_at": datetime(2024, 2, 1, 8, 40),
                "_account_name": "Other",
                "chat_messages": [
                    {"sender": "human", "text": "Hi"},
                    {"sender": "assistant", "text": "Hello"},
                ],
            }
        )
        mock_db.conversations.insert_one(
            {
                "uuid": "invalid-date",
                "name": "Invalid",
                "created_at": "not-a-date",
                "updated_at": "not-a-date",
                "_account_name": "Other",
                "chat_messages": [{"sender": "system", "text": "ignored"}],
            }
        )

        response = client.get("/api/stats/timeseries?days=0")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["summary"]["total_conversations"] == 4
        assert data["message_distribution"]["human"] >= 2
        assert data["time_series"]["day"]
        assert data["time_series"]["week"]
        assert data["time_series"]["month"]

    def test_timeseries_trend_with_previous_period(
        self,
        client: FlaskClient,
        mock_db: Any,
    ) -> None:
        """Test finite-period trend branch."""
        now = datetime.now()
        mock_db.conversations.insert_many(
            [
                {
                    "uuid": "current",
                    "created_at": (now - timedelta(days=1)).isoformat(),
                    "updated_at": now.isoformat(),
                    "_account_name": "Current",
                    "chat_messages": [{"sender": "human"}],
                },
                {
                    "uuid": "previous",
                    "created_at": (now - timedelta(days=8)).isoformat(),
                    "updated_at": (now - timedelta(days=8)).isoformat(),
                    "_account_name": "Previous",
                    "chat_messages": [{"sender": "assistant"}],
                },
            ]
        )

        response = client.get("/api/stats/timeseries?days=7")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["summary"]["conversation_trend"] == 0

    def test_heatmap_with_and_without_data(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test heatmap calculations and empty-year fallback."""
        populated = client.get("/api/stats/heatmap?year=2024")
        empty = client.get("/api/stats/heatmap?year=1999")

        assert populated.status_code == 200
        assert json.loads(populated.data)["stats"]["total_conversations"] >= 2
        assert empty.status_code == 200
        assert json.loads(empty.data)["stats"]["total_conversations"] == 0


class TestAccountsAPI:
    """Tests for accounts API."""

    def test_accounts_returns_list(self, client: FlaskClient) -> None:
        """Test that accounts endpoint returns a list."""
        response = client.get("/api/accounts")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_accounts_returns_distinct_accounts(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test account list includes imported account names."""
        response = client.get("/api/accounts")

        assert "Test Account" in json.loads(response.data)


class TestConversationDetailAPI:
    """Tests for single conversation API."""

    def test_nonexistent_conversation_returns_404(self, client: FlaskClient) -> None:
        """Test that requesting non-existent conversation returns 404."""
        response = client.get("/api/conversation/nonexistent-uuid")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    def test_existing_conversation_returns_json(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test retrieving a complete conversation."""
        response = client.get("/api/conversation/test-conv-uuid-123")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["uuid"] == "test-conv-uuid-123"
        assert isinstance(data["_id"], str)


class TestProjectDetailAPI:
    """Tests for single project API."""

    def test_nonexistent_project_returns_404(self, client: FlaskClient) -> None:
        """Test that requesting non-existent project returns 404."""
        response = client.get("/api/project/nonexistent-uuid")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    def test_existing_project_returns_related_conversations(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test project detail includes related conversations."""
        response = client.get("/api/project/test-project-uuid-789")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["uuid"] == "test-project-uuid-789"
        assert "related_conversations" in data


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

    def test_recent_collection_variants(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test recent item branches for all valid collections."""
        for collection in ["conversations", "projects", "users", "import_history"]:
            response = client.get(f"/api/recent/{collection}?page=0&per_page=999")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["pagination"]["page"] == 1
            assert data["pagination"]["per_page"] == 50

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

    def test_attachment_error_branches(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test attachment message and index error branches."""
        missing_message = client.get("/api/attachment/test-conv-uuid-123/99/0")
        missing_attachment = client.get("/api/attachment/test-conv-uuid-123/0/99")

        assert missing_message.status_code == 404
        assert missing_attachment.status_code == 404

    def test_attachment_metadata_and_download(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test attachment metadata and file download response."""
        metadata = client.get("/api/attachment/test-conv-attach-uuid-456/0/0")
        download = client.get("/api/attachment/test-conv-attach-uuid-456/0/0/download")

        assert metadata.status_code == 200
        assert json.loads(metadata.data)["filename"] == "test_file.txt"
        assert download.status_code == 200
        assert download.data == b"This is the content of the test file."
        assert "attachment" in download.headers["Content-Disposition"]

    def test_attachment_download_error_branches(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test attachment download missing-resource branches."""
        assert client.get("/api/attachment/missing/0/0/download").status_code == 404
        assert client.get("/api/attachment/test-conv-uuid-123/99/0/download").status_code == 404
        assert client.get("/api/attachment/test-conv-uuid-123/0/99/download").status_code == 404


class TestArtifactAPI:
    """Tests for artifact API."""

    def test_artifact_nonexistent_conversation(self, client: FlaskClient) -> None:
        """Test artifact from non-existent conversation returns 404."""
        response = client.get("/api/artifact/nonexistent-uuid/0/0")
        assert response.status_code == 404

    def test_artifact_error_branches(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test artifact message, sender, and content-index errors."""
        assert client.get("/api/artifact/test-conv-attach-uuid-456/99/0").status_code == 404
        assert client.get("/api/artifact/test-conv-attach-uuid-456/0/0").status_code == 400
        assert client.get("/api/artifact/test-conv-attach-uuid-456/1/99").status_code == 404

    def test_artifact_text_and_thinking_blocks(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test artifact responses for thinking and text content blocks."""
        thinking = client.get("/api/artifact/test-conv-attach-uuid-456/1/0")
        text = client.get("/api/artifact/test-conv-attach-uuid-456/1/1")

        assert thinking.status_code == 200
        assert json.loads(thinking.data)["artifact_type"] == "thinking"
        assert text.status_code == 200
        assert json.loads(text.data)["artifact_type"] == "text"


class TestExportAPI:
    """Tests for export API."""

    def test_export_nonexistent_conversation(self, client: FlaskClient) -> None:
        """Test exporting non-existent conversation returns 404."""
        response = client.get("/api/export/conversation/nonexistent-uuid")
        assert response.status_code == 404

    def test_export_nonexistent_conversation_zip(self, client: FlaskClient) -> None:
        """Test ZIP export for non-existent conversation returns 404."""
        response = client.get("/api/export/conversation/nonexistent-uuid/zip")
        assert response.status_code == 404

    def test_export_existing_conversation(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test exporting one conversation as JSON."""
        response = client.get("/api/export/conversation/test-conv-uuid-123")

        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert b"test-conv-uuid-123" in response.data

    def test_export_conversation_zip_includes_files(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test conversation ZIP includes JSON, attachments, artifacts, and manifest."""
        response = client.get("/api/export/conversation/test-conv-attach-uuid-456/zip")

        assert response.status_code == 200
        assert response.mimetype == "application/zip"

        with zipfile.ZipFile(BytesIO(response.data)) as bundle:
            names = set(bundle.namelist())
            manifest = json.loads(bundle.read("manifest.json"))

            assert "conversation.json" in names
            assert "attachments/message_0000/test_file.txt" in names
            assert "artifacts/message_0001/assistant_thinking_0.txt" in names
            assert "artifacts/message_0001/assistant_response_1.txt" in names
            assert bundle.read("attachments/message_0000/test_file.txt").decode() == (
                "This is the content of the test file."
            )
            assert manifest["conversation_uuid"] == "test-conv-attach-uuid-456"
            assert {entry["kind"] for entry in manifest["files"]} == {
                "conversation_json",
                "user_attachment",
                "assistant_artifact",
            }

    def test_export_messages_json_and_csv(
        self,
        client: FlaskClient,
        populated_db: Any,
    ) -> None:
        """Test selected-message export formats."""
        json_response = client.post(
            "/api/export/messages",
            json={
                "conversation_uuid": "test-conv-uuid-123",
                "message_indices": [0, 99],
                "format": "json",
            },
        )
        csv_response = client.post(
            "/api/export/messages",
            json={
                "conversation_uuid": "test-conv-uuid-123",
                "message_indices": [0],
                "format": "csv",
            },
        )
        missing_response = client.post(
            "/api/export/messages",
            json={"conversation_uuid": "missing", "message_indices": [0]},
        )

        assert json_response.status_code == 200
        assert json.loads(json_response.data)[0]["conversation_uuid"] == "test-conv-uuid-123"
        assert csv_response.status_code == 200
        assert b"conversation_uuid" in csv_response.data
        assert missing_response.status_code == 404


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


class TestTemplateFilters:
    """Tests for app template filters."""

    def test_humandate_variants(self) -> None:
        """Test human-readable date filter branches."""
        app_module = _app_module()

        assert app_module.humandate_filter(None) == ""
        assert app_module.humandate_filter("not-a-date") == "not-a-date"
        assert app_module.humandate_filter("2024-01-15T10:00:00Z") == "Jan 15, 2024"
        assert app_module.humandate_filter(datetime(2024, 1, 15, 10, 0)) == "Jan 15, 2024"

    def test_relativedate_variants(self) -> None:
        """Test relative date filter branches."""
        app_module = _app_module()
        now = datetime.now()

        assert app_module.relativedate_filter(None) == ""
        assert app_module.relativedate_filter("bad-date") == "bad-date"
        assert app_module.relativedate_filter(now) == "just now"
        assert app_module.relativedate_filter(now - timedelta(minutes=2)) == "2 mins ago"
        assert app_module.relativedate_filter(now - timedelta(hours=1)) == "1 hour ago"
        assert app_module.relativedate_filter(now - timedelta(days=1)) == "yesterday"
        assert app_module.relativedate_filter(now - timedelta(days=3)) == "3 days ago"
        assert app_module.relativedate_filter(now - timedelta(days=14)) == "2 weeks ago"
        assert app_module.relativedate_filter(now - timedelta(days=60)) == "2 months ago"
        assert app_module.relativedate_filter(now - timedelta(days=730)) == "2 years ago"

    def test_truncate_uuid_variants(self) -> None:
        """Test UUID truncation filter branches."""
        app_module = _app_module()

        assert app_module.truncate_uuid_filter(None) == ""
        assert app_module.truncate_uuid_filter("short") == "short"
        assert app_module.truncate_uuid_filter("1234567890", 4) == "1234..."
