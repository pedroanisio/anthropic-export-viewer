"""
Schema-contract regression tests (drift-risk Findings #4 and #5).

Finding #4 — ``app.py`` reads conversation/message/project/user data as raw
dicts; the Pydantic models are a parallel, unenforced restatement of the same
shape. Finding #5 — the ``conftest.py`` ``sample_*`` fixtures hand-mirror the
export schema, so they cannot detect a schema change (they *are* the assumed
schema).

These tests tie the three restatements together:

* **Fixtures ↔ models** — every ``sample_*`` fixture must validate against its
  Pydantic model. If a fixture is edited into a shape the model rejects (or a
  model field is retyped), validation fails (Finding #5).
* **Models ↔ consumers** — each model must declare the fields ``app.py`` /
  templates actually read. Removing or renaming such a field on the model fails
  the relevant test, flagging that a consumer would start reading ``None``
  (Finding #4).

The consumed-field sets below are derived from the real access sites in
``src/app.py`` and ``src/templates/*.html`` (see ``drift-risk-map.md``).
"""

from __future__ import annotations

import os
import sys
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import (
    Attachment,
    ContentBlock,
    Conversation,
    Message,
    Project,
    User,
)


def _declared_names(model: type[BaseModel]) -> set[str]:
    """Return every field's name *and* its serialization alias for a model."""
    names: set[str] = set()
    for field_name, info in model.model_fields.items():
        names.add(field_name)
        if info.alias:
            names.add(info.alias)
    return names


# Fields each model must keep, because app.py / the templates read them by key.
CONSUMED_FIELDS: dict[type[BaseModel], set[str]] = {
    Conversation: {
        "uuid",
        "name",
        "chat_messages",
        "created_at",
        "updated_at",
        "account",
        "_account_name",
    },
    Message: {"uuid", "sender", "text", "content", "attachments", "created_at"},
    ContentBlock: {"type", "text", "thinking"},
    Attachment: {"file_name", "file_type", "file_size", "extracted_content"},
    Project: {
        "uuid",
        "name",
        "description",
        "is_private",
        "is_starter_project",
        "docs",
        "prompt_template",
    },
    User: {"uuid", "id", "email"},
}


class TestConsumedFieldsArePinned:
    """Models must declare every field their consumers read (Finding #4)."""

    def test_all_consumed_fields_present(self) -> None:
        """No model may drop a field that app.py / templates depend on."""
        violations: list[str] = []
        for model, consumed in CONSUMED_FIELDS.items():
            missing = consumed - _declared_names(model)
            if missing:
                violations.append(f"{model.__name__}: missing {sorted(missing)}")
        assert not violations, (
            "Models dropped fields that consumers still read (silent None risk): "
            + "; ".join(violations)
        )


class TestFixturesValidateAgainstModels:
    """conftest sample_* fixtures must conform to their models (Finding #5)."""

    def test_sample_conversation_is_valid(self, sample_conversation: dict[str, Any]) -> None:
        """The basic conversation fixture parses as a Conversation."""
        conv = Conversation.model_validate(sample_conversation)
        assert conv.uuid == sample_conversation["uuid"]
        assert conv.all_messages, "fixture should yield messages through the model"

    def test_sample_conversation_with_attachments_is_valid(
        self, sample_conversation_with_attachments: dict[str, Any]
    ) -> None:
        """The attachment-bearing fixture parses, incl. nested blocks/attachments."""
        conv = Conversation.model_validate(sample_conversation_with_attachments)
        # Drill into the nested models so a nested-shape change is caught too.
        attachments = [a for m in conv.all_messages for a in (m.attachments or [])]
        assert any(a.file_name for a in attachments)
        block_types = {b.type for m in conv.all_messages for b in (m.content or [])}
        assert ContentBlock.model_validate({"type": "text"}).type in block_types

    def test_sample_project_is_valid(self, sample_project: dict[str, Any]) -> None:
        """The project fixture parses as a Project."""
        project = Project.model_validate(sample_project)
        assert project.uuid == sample_project["uuid"]
        assert project.is_private == sample_project["is_private"]

    def test_sample_user_is_valid(self, sample_user: dict[str, Any]) -> None:
        """The user fixture parses as a User."""
        user = User.model_validate(sample_user)
        assert user.uuid == sample_user["uuid"]
        assert user.email == sample_user["email"]


class TestModelsRejectShapeViolations:
    """The models still enforce types, so a corrupted shape is caught."""

    def test_wrong_type_is_rejected(self) -> None:
        """A type violation on a pinned field fails validation."""
        bad = {"uuid": "p1", "is_private": "not-a-bool-or-none-ish", "docs": "should-be-list"}
        with pytest.raises(ValidationError):
            Project.model_validate(bad)
