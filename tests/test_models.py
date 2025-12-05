"""
Tests for Pydantic data models (ADR-003, ADR-012).

Tests validate that models correctly parse and validate Anthropic data structures.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import (
    Account,
    Artifact,
    Attachment,
    ClaudeExport,
    ContentBlock,
    ContentBlockType,
    Conversation,
    ExportMetadata,
    Message,
    MessageRole,
)


class TestContentBlockType:
    """Tests for ContentBlockType enum."""

    def test_text_type_exists(self) -> None:
        """Verify TEXT type is available."""
        assert ContentBlockType.TEXT.value == "text"

    def test_thinking_type_exists(self) -> None:
        """Verify THINKING type is available."""
        assert ContentBlockType.THINKING.value == "thinking"

    def test_all_expected_types_present(self) -> None:
        """Verify all expected content block types exist."""
        expected_types = {"text", "thinking", "p", "pre", "image", "document"}
        actual_types = {t.value for t in ContentBlockType}
        assert expected_types.issubset(actual_types)


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_human_role(self) -> None:
        """Verify HUMAN role value."""
        assert MessageRole.HUMAN.value == "human"

    def test_assistant_role(self) -> None:
        """Verify ASSISTANT role value."""
        assert MessageRole.ASSISTANT.value == "assistant"


class TestContentBlock:
    """Tests for ContentBlock model."""

    def test_text_content_block(self) -> None:
        """Test creating a text content block."""
        block = ContentBlock(type=ContentBlockType.TEXT, text="Hello, world!")
        assert block.type == ContentBlockType.TEXT
        assert block.text == "Hello, world!"

    def test_thinking_content_block(self) -> None:
        """Test creating a thinking content block."""
        block = ContentBlock(
            type=ContentBlockType.THINKING,
            thinking="Let me analyze this...",
        )
        assert block.type == ContentBlockType.THINKING
        assert block.thinking == "Let me analyze this..."

    def test_content_block_with_timestamps(self) -> None:
        """Test content block with timing information."""
        block = ContentBlock(
            type=ContentBlockType.TEXT,
            text="Response text",
            start_timestamp="2024-01-15T10:00:00Z",
            stop_timestamp="2024-01-15T10:00:05Z",
        )
        assert block.start_timestamp == "2024-01-15T10:00:00Z"
        assert block.stop_timestamp == "2024-01-15T10:00:05Z"

    def test_content_block_with_summaries(self) -> None:
        """Test content block with AI summaries."""
        block = ContentBlock(
            type=ContentBlockType.TEXT,
            text="Detailed response",
            summaries=[{"summary": "Brief summary of the response"}],
        )
        assert len(block.summaries or []) == 1
        assert block.summaries[0]["summary"] == "Brief summary of the response"

    def test_content_block_allows_extra_fields(self) -> None:
        """Test that content block allows extra fields for extensibility."""
        block = ContentBlock(
            type=ContentBlockType.TEXT,
            text="Text",
            custom_field="custom_value",
        )
        assert block.text == "Text"


class TestAttachment:
    """Tests for Attachment model."""

    def test_basic_attachment(self) -> None:
        """Test creating a basic attachment."""
        attachment = Attachment(
            file_name="document.txt",
            file_type="txt",
            file_size=1024,
        )
        assert attachment.file_name == "document.txt"
        assert attachment.file_type == "txt"
        assert attachment.file_size == 1024

    def test_attachment_with_extracted_content(self) -> None:
        """Test attachment with extracted text content."""
        attachment = Attachment(
            file_name="readme.md",
            file_type="md",
            file_size=2048,
            extracted_content="# README\n\nThis is the content.",
        )
        assert attachment.extracted_content is not None
        assert "README" in attachment.extracted_content

    def test_attachment_minimal_fields(self) -> None:
        """Test attachment with minimal fields (all optional)."""
        attachment = Attachment()
        assert attachment.file_name is None
        assert attachment.file_type is None


class TestMessage:
    """Tests for Message model."""

    def test_human_message(self) -> None:
        """Test creating a human message."""
        message = Message(
            uuid="msg-123",
            sender="human",
            text="Hello, Claude!",
            created_at="2024-01-15T10:00:00Z",
        )
        assert message.sender == "human"
        assert message.text == "Hello, Claude!"
        assert message.sender_role == "human"

    def test_assistant_message_with_content(self) -> None:
        """Test creating an assistant message with content blocks."""
        message = Message(
            uuid="msg-456",
            sender="assistant",
            text="Hello! How can I help?",
            content=[
                ContentBlock(type=ContentBlockType.TEXT, text="Hello! How can I help?")
            ],
        )
        assert message.sender == "assistant"
        assert message.content is not None
        assert len(message.content) == 1
        assert message.content[0].type == ContentBlockType.TEXT

    def test_message_with_attachments(self) -> None:
        """Test message with file attachments."""
        message = Message(
            uuid="msg-789",
            sender="human",
            text="Please analyze this file.",
            attachments=[
                Attachment(file_name="data.csv", file_type="csv", file_size=5000)
            ],
        )
        assert message.attachments is not None
        assert len(message.attachments) == 1
        assert message.attachments[0].file_name == "data.csv"

    def test_sender_role_property_with_role_field(self) -> None:
        """Test sender_role property when role field is used instead of sender."""
        message = Message(
            uuid="msg-000",
            role=MessageRole.ASSISTANT,
            text="Response text",
        )
        assert message.sender_role == "assistant"


class TestConversation:
    """Tests for Conversation model."""

    def test_basic_conversation(self) -> None:
        """Test creating a basic conversation."""
        conversation = Conversation(
            uuid="conv-123",
            name="Test Conversation",
            created_at="2024-01-15T10:00:00Z",
        )
        assert conversation.uuid == "conv-123"
        assert conversation.display_name == "Test Conversation"

    def test_conversation_with_messages(self) -> None:
        """Test conversation with chat messages."""
        conversation = Conversation(
            uuid="conv-456",
            name="Chat with Claude",
            chat_messages=[
                Message(sender="human", text="Hi"),
                Message(sender="assistant", text="Hello!"),
            ],
        )
        assert len(conversation.all_messages) == 2

    def test_conversation_display_name_fallback(self) -> None:
        """Test display_name falls back to title field."""
        conversation = Conversation(
            uuid="conv-789",
            title="Title Field Value",
        )
        assert conversation.display_name == "Title Field Value"

    def test_conversation_all_messages_with_alternative_fields(self) -> None:
        """Test all_messages works with alternative field names."""
        conversation = Conversation(
            uuid="conv-000",
            messages=[
                Message(sender="human", text="Message 1"),
            ],
        )
        assert len(conversation.all_messages) == 1


class TestClaudeExport:
    """Tests for ClaudeExport model."""

    def test_export_with_conversations(self) -> None:
        """Test export containing conversations."""
        export = ClaudeExport(
            conversations=[
                Conversation(uuid="conv-1", name="Conversation 1"),
                Conversation(uuid="conv-2", name="Conversation 2"),
            ]
        )
        assert len(export.all_conversations) == 2

    def test_export_with_data_field(self) -> None:
        """Test export using alternative 'data' field name."""
        export = ClaudeExport(
            data=[
                Conversation(uuid="conv-1", name="Conversation 1"),
            ]
        )
        assert len(export.all_conversations) == 1

    def test_get_conversation_by_title(self) -> None:
        """Test finding conversation by title."""
        export = ClaudeExport(
            conversations=[
                Conversation(uuid="conv-1", name="First Chat"),
                Conversation(uuid="conv-2", name="Second Chat"),
            ]
        )
        found = export.get_conversation_by_title("First Chat")
        assert found is not None
        assert found.uuid == "conv-1"

    def test_get_total_message_count(self) -> None:
        """Test counting total messages across conversations."""
        export = ClaudeExport(
            conversations=[
                Conversation(
                    uuid="conv-1",
                    chat_messages=[
                        Message(sender="human", text="Hi"),
                        Message(sender="assistant", text="Hello"),
                    ],
                ),
                Conversation(
                    uuid="conv-2",
                    chat_messages=[
                        Message(sender="human", text="Question"),
                    ],
                ),
            ]
        )
        assert export.get_total_message_count() == 3


class TestArtifact:
    """Tests for Artifact model."""

    def test_code_artifact(self) -> None:
        """Test creating a code artifact."""
        artifact = Artifact(
            id="artifact-123",
            type="code",
            title="Python Script",
            content="print('Hello, World!')",
            language="python",
        )
        assert artifact.type == "code"
        assert artifact.language == "python"

    def test_document_artifact(self) -> None:
        """Test creating a document artifact."""
        artifact = Artifact(
            id="artifact-456",
            type="document",
            title="Analysis Report",
            content="# Report\n\nFindings...",
            mime_type="text/markdown",
        )
        assert artifact.type == "document"
        assert artifact.mime_type == "text/markdown"


class TestAccount:
    """Tests for Account model."""

    def test_account_with_uuid(self) -> None:
        """Test creating account with UUID."""
        account = Account(uuid="account-uuid-123")
        assert account.uuid == "account-uuid-123"

    def test_account_allows_extra_fields(self) -> None:
        """Test account allows extra fields."""
        account = Account(uuid="account-123", extra_field="value")
        assert account.uuid == "account-123"


class TestExportMetadata:
    """Tests for ExportMetadata model."""

    def test_export_metadata(self) -> None:
        """Test creating export metadata."""
        from datetime import datetime

        metadata = ExportMetadata(
            exported_at=datetime.now(),
            export_version="1.0",
            user_id="user-123",
            total_conversations=42,
        )
        assert metadata.export_version == "1.0"
        assert metadata.total_conversations == 42

