"""
Pydantic data models for Anthropic conversation exports (ADR-012).

These models validate and parse data from Claude conversation exports.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Enum for message roles (based on actual MongoDB data)."""

    HUMAN = "human"  # User messages in actual data
    ASSISTANT = "assistant"  # Assistant messages
    # Legacy/alternative values that might appear
    USER = "user"
    PROMPT = "prompt"
    RESPONSE = "response"


class ContentBlockType(str, Enum):
    """Enum for content block types (based on actual MongoDB data)."""

    # Core types found in actual data
    TEXT = "text"  # Assistant response text
    THINKING = "thinking"  # Assistant thinking process
    # Legacy/HTML-based types that might appear
    PARAGRAPH = "p"
    CODE = "pre"
    IMAGE = "image"
    DOCUMENT = "document"
    ARTIFACT = "artifact"
    LIST = "ul"
    LIST_ITEM = "li"
    HEADING = "h1"
    HEADING2 = "h2"
    HEADING3 = "h3"
    BLOCKQUOTE = "blockquote"
    TABLE = "table"


class ContentBlock(BaseModel):
    """
    Individual content block within assistant messages.

    Based on actual MongoDB data structure from Anthropic conversations.
    """

    type: ContentBlockType = Field(
        ..., description="Type of content block: 'text' or 'thinking'"
    )

    # Core content fields (based on type)
    text: str | None = Field(None, description="Response text content (for type='text')")
    thinking: str | None = Field(
        None, description="Thinking process content (for type='thinking')"
    )

    # Metadata fields found in actual data
    citations: list[dict[str, Any]] | None = Field(
        default_factory=list, description="Citation references"
    )
    summaries: list[dict[str, str]] | None = Field(
        default_factory=list, description="AI-generated summaries"
    )
    start_timestamp: str | None = Field(
        None, description="When content generation started"
    )
    stop_timestamp: str | None = Field(
        None, description="When content generation ended"
    )
    cut_off: bool | None = Field(None, description="Whether content was cut off")
    flags: Any | None = Field(None, description="Content flags (usually null)")

    # Legacy fields that might appear in other formats
    data: str | None = Field(None, description="Alternative content field")
    language: str | None = Field(
        None, description="Programming language for code blocks"
    )
    source: dict[str, Any] | None = Field(
        None, description="Source info for images/documents"
    )
    title: str | None = Field(None, description="Title for artifacts or documents")
    id: str | None = Field(None, description="Unique identifier for artifacts")
    mime_type: str | None = Field(None, description="MIME type for artifacts")

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields for extensibility


class Attachment(BaseModel):
    """
    Model for user-uploaded files/documents in conversations.

    Based on actual MongoDB field names.
    """

    # Actual MongoDB fields
    file_name: str | None = Field(None, description="Name of the file")
    file_type: str | None = Field(None, description="Type/extension of file")
    file_size: int | None = Field(None, description="File size in bytes")
    extracted_content: str | None = Field(
        None, description="Extracted text content from documents"
    )

    # Legacy fields that might appear in other formats
    file_id: str | None = Field(None, description="Unique file identifier")
    media_type: str | None = Field(None, description="MIME type")
    size: int | None = Field(None, description="Alternative size field")
    extracted_text: str | None = Field(
        None, description="Alternative extracted content field"
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"


class Message(BaseModel):
    """
    Individual message in a conversation from MongoDB chat_messages.

    Based on actual Anthropic conversation data structure.
    """

    # Core fields from actual MongoDB data
    uuid: str | None = Field(None, description="Unique message identifier")
    sender: str | None = Field(
        None, description="Message sender: 'human' or 'assistant'"
    )
    text: str | None = Field(None, description="Plain text version of the message")
    content: list[ContentBlock] | None = Field(
        None, description="Array of structured content blocks"
    )
    attachments: list[Attachment] | None = Field(
        default_factory=list, description="User-uploaded files attached to this message"
    )
    files: list[dict[str, Any]] | None = Field(
        default_factory=list, description="Files array (related to attachments)"
    )
    created_at: str | None = Field(
        None, description="When message was created (ISO string)"
    )
    updated_at: str | None = Field(
        None, description="When message was last updated (ISO string)"
    )

    # Legacy/alternative fields that might appear
    index: int | None = Field(None, description="Sequential index of the message")
    type: str | None = Field(None, description="Message type (prompt/response)")
    role: MessageRole | None = Field(None, description="Role (user/assistant)")
    message: list[ContentBlock] | None = Field(
        None, description="Alternative content blocks field"
    )
    timestamp: datetime | None = Field(None, description="Alternative timestamp field")

    class Config:
        """Pydantic configuration."""

        extra = "allow"

    @property
    def sender_role(self) -> str | None:
        """Get the sender role, checking multiple possible fields."""
        return self.sender or (self.role.value if self.role else None)


class Artifact(BaseModel):
    """Artifact created during conversation (code, documents, etc.)."""

    id: str = Field(..., description="Unique artifact identifier")
    type: str = Field(..., description="Artifact type (code, document, etc.)")
    title: str | None = Field(None, description="Artifact title")
    content: str = Field(..., description="Artifact content")
    language: str | None = Field(None, description="Programming language if code")
    mime_type: str | None = Field(None, description="MIME type of artifact")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        extra = "allow"


class Account(BaseModel):
    """Account information embedded in conversations."""

    uuid: str | None = Field(None, description="Account UUID")

    class Config:
        """Pydantic configuration."""

        extra = "allow"


class Conversation(BaseModel):
    """
    Complete conversation/chat session with Claude from MongoDB.

    Based on actual Anthropic conversation data structure.
    """

    # Core fields from actual MongoDB data
    uuid: str | None = Field(None, description="Unique conversation UUID")
    name: str | None = Field(None, description="Conversation title/name")
    account: Account | None = Field(None, description="Account information")
    chat_messages: list[Message] | None = Field(
        None, description="Array of messages in conversation"
    )
    created_at: str | None = Field(
        None, description="When conversation started (ISO string)"
    )
    updated_at: str | None = Field(None, description="Last update time (ISO string)")

    # MongoDB internal/import fields (using aliases for underscore fields)
    mongo_id: str | None = Field(
        None, alias="_id", description="MongoDB document ID"
    )
    account_name: str | None = Field(
        None, alias="_account_name", description="Account name for indexing"
    )
    import_id: str | None = Field(
        None, alias="_import_id", description="Import batch identifier"
    )
    import_ids: list[str] | None = Field(
        None, alias="_import_ids", description="List of import IDs"
    )
    imported_at: str | None = Field(
        None, alias="_imported_at", description="When conversation was imported"
    )

    # Legacy/alternative fields that might appear in other formats
    id: str | None = Field(None, description="Alternative unique identifier")
    title: str | None = Field(None, description="Alternative title field")
    messages: list[Message] | None = Field(
        None, description="Alternative messages field"
    )
    chats: list[Message] | None = Field(
        None, description="Another alternative messages field"
    )

    # Additional metadata
    summary: str | None = Field(None, description="AI-generated summary")
    model: str | None = Field(None, description="Claude model used")
    artifacts: list[Artifact] | None = Field(
        default_factory=list, description="Artifacts created in this conversation"
    )
    project_id: str | None = Field(None, description="Associated project ID if any")
    is_deleted: bool | None = Field(
        False, description="Whether conversation was deleted"
    )
    tags: list[str] | None = Field(default_factory=list, description="User tags")

    class Config:
        """Pydantic configuration."""

        extra = "allow"
        populate_by_name = True  # Allow using both field name and alias

    @property
    def all_messages(self) -> list[Message]:
        """Get messages regardless of field name used."""
        return self.chat_messages or self.messages or self.chats or []

    @property
    def display_name(self) -> str | None:
        """Get display name, checking multiple possible fields."""
        return self.name or self.title


class ExportMetadata(BaseModel):
    """Metadata about the export itself."""

    exported_at: datetime | None = Field(None, description="When export was created")
    export_version: str | None = Field(None, description="Export format version")
    user_id: str | None = Field(None, description="User identifier")
    total_conversations: int | None = Field(
        None, description="Total conversation count"
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"


class ClaudeExport(BaseModel):
    """
    Complete Claude export data model.

    This represents the structure of conversations.json file.
    """

    conversations: list[Conversation] | None = Field(
        None, description="Array of all conversations"
    )
    # Some exports might structure it differently
    data: list[Conversation] | None = Field(
        None, description="Alternative field name"
    )

    metadata: ExportMetadata | None = Field(None, description="Export metadata")
    meta: dict[str, Any] | None = Field(
        None, description="Alternative metadata field"
    )

    # User information (if included)
    user: dict[str, Any] | None = Field(
        None, description="User account information"
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"

    @property
    def all_conversations(self) -> list[Conversation]:
        """Get conversations regardless of field name used."""
        return self.conversations or self.data or []

    def get_conversation_by_title(self, title: str) -> Conversation | None:
        """Find a conversation by its title."""
        for conv in self.all_conversations:
            if conv.title == title or conv.name == title:
                return conv
        return None

    def get_total_message_count(self) -> int:
        """Get total number of messages across all conversations."""
        total = 0
        for conv in self.all_conversations:
            total += len(conv.all_messages)
        return total

    def get_artifacts(self) -> list[Artifact]:
        """Extract all artifacts from all conversations."""
        artifacts: list[Artifact] = []
        for conv in self.all_conversations:
            if conv.artifacts:
                artifacts.extend(conv.artifacts)
        return artifacts
