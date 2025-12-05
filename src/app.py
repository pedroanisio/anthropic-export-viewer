#!/usr/bin/env python3
"""
Anthropic Data Manager.

Complete application for loading and managing Anthropic data exports.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from flask import (
    Flask,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask.wrappers import Response
from flask_cors import CORS
from pymongo import ASCENDING, TEXT, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from werkzeug.utils import secure_filename

from config import get_settings
from models import Attachment, ContentBlock, ContentBlockType

if TYPE_CHECKING:
    import pandas as pd
    from pymongo.results import UpdateResult

# Configure structured logging (ADR-013)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()
        if get_settings().log_format == "console"
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Load settings
settings = get_settings()

# Flask app configuration
app = Flask(__name__)
app.config["SECRET_KEY"] = settings.secret_key
app.config["UPLOAD_FOLDER"] = settings.upload_folder
app.config["MAX_CONTENT_LENGTH"] = settings.max_content_length
app.config["MONGO_URI"] = settings.mongo_uri
app.config["DB_NAME"] = settings.db_name

CORS(app)


# Jinja2 template filters for human-readable display
@app.template_filter("humandate")
def humandate_filter(value: datetime | str | None) -> str:
    """Convert datetime to human-readable format (e.g., 'Dec 2, 2025')."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    return value.strftime("%b %d, %Y")


@app.template_filter("relativedate")
def relativedate_filter(value: datetime | str | None) -> str:
    """Convert datetime to relative format (e.g., '2 days ago')."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value

    now = datetime.now(value.tzinfo) if value.tzinfo else datetime.now()
    diff = now - value

    if diff.days == 0:
        if diff.seconds < 60:
            return "just now"
        if diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes} min{'s' if minutes != 1 else ''} ago"
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if diff.days == 1:
        return "yesterday"
    if diff.days < 7:
        return f"{diff.days} days ago"
    if diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    if diff.days < 365:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    years = diff.days // 365
    return f"{years} year{'s' if years != 1 else ''} ago"


@app.template_filter("truncate_uuid")
def truncate_uuid_filter(value: str | None, length: int = 8) -> str:
    """Truncate UUID to first N characters with ellipsis."""
    if value is None:
        return ""
    if len(value) <= length:
        return value
    return f"{value[:length]}..."


# Ensure upload directory exists
Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

# MongoDB setup
mongo_client: MongoClient[dict[str, Any]] = MongoClient(app.config["MONGO_URI"])
db: Database[dict[str, Any]] = mongo_client[app.config["DB_NAME"]]


class DataProcessor:
    """Handles processing of Anthropic data exports."""

    @staticmethod
    def setup_indexes() -> None:
        """Create MongoDB indexes for optimal performance."""
        # Conversations indexes
        db.conversations.create_index([("uuid", ASCENDING)], unique=True)
        db.conversations.create_index([("account.uuid", ASCENDING)])
        db.conversations.create_index([("created_at", ASCENDING)])
        db.conversations.create_index([("name", TEXT)])

        # Users indexes
        db.users.create_index([("uuid", ASCENDING)], unique=True)
        db.users.create_index([("email", ASCENDING)], sparse=True)

        # Projects indexes
        db.projects.create_index([("uuid", ASCENDING)], unique=True)
        db.projects.create_index([("name", TEXT)])

        # Import history indexes
        db.import_history.create_index([("import_id", ASCENDING)])
        db.import_history.create_index([("timestamp", ASCENDING)])

        logger.info("database_indexes_created")

    @staticmethod
    def process_zip(filepath: str, account_name: str | None = None) -> dict[str, Any]:
        """Process uploaded zip file."""
        import_id = hashlib.md5(f"{filepath}{datetime.now()}".encode()).hexdigest()[:12]
        temp_dir = f"{app.config['UPLOAD_FOLDER']}/temp_{import_id}"

        try:
            # Extract zip file
            os.makedirs(temp_dir, exist_ok=True)
            with zipfile.ZipFile(filepath, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find JSON files
            json_files = list(Path(temp_dir).rglob("*.json"))
            results: dict[str, Any] = {
                "import_id": import_id,
                "account_name": account_name or "Unknown",
                "timestamp": datetime.now(),
                "files_found": len(json_files),
                "conversations": {"loaded": 0, "duplicates": 0},
                "users": {"loaded": 0, "duplicates": 0},
                "projects": {"loaded": 0, "duplicates": 0},
            }

            # Process each JSON file
            for json_file in json_files:
                filename = json_file.name.lower()

                if "conversation" in filename:
                    stats = DataProcessor._load_conversations(
                        str(json_file), import_id, account_name or "Unknown"
                    )
                    results["conversations"] = stats
                elif "user" in filename:
                    stats = DataProcessor._load_users(
                        str(json_file), import_id, account_name or "Unknown"
                    )
                    results["users"] = stats
                elif "project" in filename:
                    stats = DataProcessor._load_projects(
                        str(json_file), import_id, account_name or "Unknown"
                    )
                    results["projects"] = stats

            # Record import history
            db.import_history.insert_one(results)

            return results

        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    @staticmethod
    def _load_conversations(
        filepath: str, import_id: str, account_name: str
    ) -> dict[str, int]:
        """Load conversations with deduplication."""
        with open(filepath) as f:
            data: list[dict[str, Any]] = json.load(f)

        loaded = 0
        duplicates = 0

        for conv in data:
            # Add metadata
            conv["_import_id"] = import_id
            conv["_account_name"] = account_name
            conv["_imported_at"] = datetime.now()

            # Upsert to prevent duplicates
            result: UpdateResult = db.conversations.update_one(
                {"uuid": conv["uuid"]},
                {"$set": conv, "$addToSet": {"_import_ids": import_id}},
                upsert=True,
            )

            if result.upserted_id:
                loaded += 1
            else:
                duplicates += 1

        return {"loaded": loaded, "duplicates": duplicates}

    @staticmethod
    def _load_users(
        filepath: str, import_id: str, account_name: str
    ) -> dict[str, int]:
        """Load users with deduplication."""
        with open(filepath) as f:
            data: list[dict[str, Any]] = json.load(f)

        loaded = 0
        duplicates = 0

        for user in data:
            user["_import_id"] = import_id
            user["_account_name"] = account_name
            user["_imported_at"] = datetime.now()

            result: UpdateResult = db.users.update_one(
                {"uuid": user.get("uuid", user.get("id"))},
                {"$set": user, "$addToSet": {"_import_ids": import_id}},
                upsert=True,
            )

            if result.upserted_id:
                loaded += 1
            else:
                duplicates += 1

        return {"loaded": loaded, "duplicates": duplicates}

    @staticmethod
    def _load_projects(
        filepath: str, import_id: str, account_name: str
    ) -> dict[str, int]:
        """Load projects with deduplication."""
        with open(filepath) as f:
            data: list[dict[str, Any]] = json.load(f)

        loaded = 0
        duplicates = 0

        for project in data:
            project["_import_id"] = import_id
            project["_account_name"] = account_name
            project["_imported_at"] = datetime.now()

            result: UpdateResult = db.projects.update_one(
                {"uuid": project["uuid"]},
                {"$set": project, "$addToSet": {"_import_ids": import_id}},
                upsert=True,
            )

            if result.upserted_id:
                loaded += 1
            else:
                duplicates += 1

        return {"loaded": loaded, "duplicates": duplicates}


# API Routes
@app.route("/")
def index() -> str:
    """Main dashboard."""
    stats: dict[str, Any] = {
        "conversations": db.conversations.count_documents({}),
        "users": db.users.count_documents({}),
        "projects": db.projects.count_documents({}),
        "imports": db.import_history.count_documents({}),
        "recent_imports": list(db.import_history.find().sort("timestamp", -1).limit(5)),
    }
    now = datetime.now().strftime("%b %d, %Y %H:%M")
    return render_template("index.html", stats=stats, now=now)


@app.route("/conversations")
def conversations() -> str:
    """Conversations browser page."""
    return render_template("conversations.html")


@app.route("/projects")
def projects() -> str:
    """Enhanced projects browser page with pagination and filtering."""
    page = max(1, int(request.args.get("page", 1)))
    per_page = 12  # Reduced for card layout
    project_type = request.args.get("type", "all")  # all, private, public, starter
    search_query = request.args.get("search", "")

    # Build query filters
    mongo_query: dict[str, Any] = {}
    if project_type == "private":
        mongo_query["is_private"] = True
    elif project_type == "public":
        mongo_query["is_private"] = {"$ne": True}
    elif project_type == "starter":
        mongo_query["is_starter_project"] = True

    if search_query:
        mongo_query["$or"] = [
            {"name": {"$regex": search_query, "$options": "i"}},
            {"description": {"$regex": search_query, "$options": "i"}},
        ]

    total_count = db.projects.count_documents(mongo_query)
    total_pages = (total_count + per_page - 1) // per_page
    skip = (page - 1) * per_page

    projects_list = list(
        db.projects.find(mongo_query, {"_id": 0})
        .skip(skip)
        .limit(per_page)
        .sort("created_at", -1)
    )

    # Enhance projects with computed counts
    for project in projects_list:
        # Count documents and templates
        project["docs_count"] = len(project.get("docs", []))
        project["templates_count"] = len(project.get("prompt_template", []))

        # Count related conversations and their artifacts (attachments)
        if project.get("name"):
            related_conversations = list(
                db.conversations.find(
                    {
                        "$or": [
                            {"name": {"$regex": project["name"], "$options": "i"}},
                            {
                                "chat_messages.text": {
                                    "$regex": project["name"],
                                    "$options": "i",
                                }
                            },
                        ]
                    },
                    {"_id": 1, "chat_messages.attachments": 1},
                )
            )

            project["related_conversations_count"] = len(related_conversations)

            # Count total artifacts (attachments) in related conversations
            total_artifacts = 0
            for conv in related_conversations:
                for message in conv.get("chat_messages", []):
                    total_artifacts += len(message.get("attachments", []))

            project["artifacts_count"] = total_artifacts
        else:
            project["related_conversations_count"] = 0
            project["artifacts_count"] = 0

    # Get project type counts for filter badges
    type_counts = {
        "all": db.projects.count_documents({}),
        "private": db.projects.count_documents({"is_private": True}),
        "public": db.projects.count_documents({"is_private": {"$ne": True}}),
        "starter": db.projects.count_documents({"is_starter_project": True}),
    }

    pagination = {
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }

    stats: dict[str, Any] = {
        "total_projects": total_count,
        "projects": projects_list,
        "pagination": pagination,
        "type_counts": type_counts,
        "current_type": project_type,
        "search_query": search_query,
    }
    return render_template("projects.html", stats=stats)


@app.route("/api/project/<uuid>")
def get_project_details(uuid: str) -> tuple[Response, int] | Response:
    """Get detailed project information."""
    project = db.projects.find_one({"uuid": uuid}, {"_id": 0})

    if not project:
        return jsonify({"error": "Project not found"}), 404

    # Find related conversations for this project (if any reference exists)
    related_conversations = list(
        db.conversations.find(
            {
                "$or": [
                    {"name": {"$regex": project.get("name", ""), "$options": "i"}},
                    {
                        "chat_messages.text": {
                            "$regex": project.get("name", ""),
                            "$options": "i",
                        }
                    },
                ]
            },
            {"_id": 0, "uuid": 1, "name": 1, "created_at": 1, "_account_name": 1},
        ).limit(5)
    )

    project["related_conversations"] = related_conversations
    return jsonify(project)


@app.route("/analytics")
def analytics() -> str:
    """Analytics dashboard page."""
    return render_template("analytics.html")


@app.route("/export")
def export_page() -> str:
    """Export tools page."""
    return render_template("export.html")


@app.route("/upload", methods=["GET", "POST"])
def upload() -> str | Response:
    """Handle file uploads."""
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)

        file = request.files["file"]
        account_name = request.form.get("account_name", "Unknown")

        if file.filename == "":
            flash("No file selected", "error")
            return redirect(request.url)

        if file and file.filename and file.filename.endswith(".zip"):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            try:
                # Process the zip file
                results = DataProcessor.process_zip(filepath, account_name)

                flash(
                    f"Import successful! Loaded {results['conversations']['loaded']} conversations, "
                    f"{results['users']['loaded']} users, {results['projects']['loaded']} projects",
                    "success",
                )

                # Clean up uploaded file
                os.remove(filepath)

                return redirect(url_for("index"))

            except Exception as e:
                logger.error("upload_processing_error", error=str(e))
                flash(f"Error processing file: {e!s}", "error")
                return redirect(request.url)

    return render_template("upload.html")


@app.route("/api/search/conversations", methods=["POST"])
def search_conversations() -> Response:
    """Search conversations API with pagination and sorting."""
    data: dict[str, Any] = request.json or {}
    query = data.get("query", "")
    filters: dict[str, Any] = data.get("filters", {})
    page = max(1, data.get("page", 1))
    per_page = min(100, max(10, data.get("per_page", 20)))
    sort_by = data.get("sort_by", "created_at")
    sort_order = data.get("sort_order", "desc")

    # Build MongoDB query
    mongo_query: dict[str, Any] = {}

    if query:
        mongo_query["$text"] = {"$search": query}

    if filters.get("account"):
        mongo_query["_account_name"] = filters["account"]

    if filters.get("date_from"):
        mongo_query["created_at"] = {"$gte": filters["date_from"]}

    if filters.get("has_attachments"):
        mongo_query["chat_messages.attachments.0"] = {"$exists": True}

    # Build aggregation pipeline for sorting by computed fields
    pipeline: list[dict[str, Any]] = [{"$match": mongo_query}]

    # Add computed fields for sorting
    pipeline.append(
        {
            "$addFields": {
                "message_count": {"$size": {"$ifNull": ["$chat_messages", []]}},
                # Count user attachments (files uploaded by users)
                "attachment_count": {
                    "$sum": {
                        "$map": {
                            "input": {"$ifNull": ["$chat_messages", []]},
                            "as": "message",
                            "in": {"$size": {"$ifNull": ["$$message.attachments", []]}},
                        }
                    }
                },
                # Count assistant artifacts (content generated by AI)
                "artifact_count": {
                    "$sum": {
                        "$map": {
                            "input": {"$ifNull": ["$chat_messages", []]},
                            "as": "message",
                            "in": {
                                "$cond": {
                                    "if": {"$eq": ["$$message.sender", "assistant"]},
                                    "then": {
                                        "$size": {"$ifNull": ["$$message.content", []]}
                                    },
                                    "else": 0,
                                }
                            },
                        }
                    }
                },
                "user_message_count": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$chat_messages", []]},
                            "as": "message",
                            "cond": {"$eq": ["$$message.sender", "human"]},
                        }
                    }
                },
                "assistant_message_count": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$chat_messages", []]},
                            "as": "message",
                            "cond": {"$eq": ["$$message.sender", "assistant"]},
                        }
                    }
                },
            }
        }
    )

    # Determine sort direction
    sort_direction = -1 if sort_order == "desc" else 1

    # Handle different sort fields
    if sort_by in ["message_count", "attachment_count"]:
        pipeline.append({"$sort": {sort_by: sort_direction, "created_at": -1}})
    elif sort_by == "name":
        pipeline.append({"$sort": {sort_by: sort_direction, "created_at": -1}})
    else:  # created_at, updated_at, or other date fields
        pipeline.append({"$sort": {sort_by: sort_direction}})

    # Add pagination
    pipeline.extend([{"$skip": (page - 1) * per_page}, {"$limit": per_page}])

    # Include only the fields we need (excluding chat_messages for performance)
    pipeline.append(
        {
            "$project": {
                "_id": 1,
                "uuid": 1,
                "name": 1,
                "created_at": 1,
                "updated_at": 1,
                "_account_name": 1,
                "message_count": 1,
                "attachment_count": 1,
                "artifact_count": 1,
                "user_message_count": 1,
                "assistant_message_count": 1,
            }
        }
    )

    # Get total count using separate aggregation
    count_pipeline: list[dict[str, Any]] = [
        {"$match": mongo_query},
        {"$count": "total"},
    ]
    count_result = list(db.conversations.aggregate(count_pipeline))
    total_count = count_result[0]["total"] if count_result else 0
    total_pages = (total_count + per_page - 1) // per_page

    # Execute main query
    conversations_result = list(db.conversations.aggregate(pipeline))

    # Convert ObjectId to string for JSON serialization
    for conv in conversations_result:
        conv["_id"] = str(conv["_id"])

    return jsonify(
        {
            "conversations": conversations_result,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages,
            },
            "sort_info": {"sort_by": sort_by, "sort_order": sort_order},
        }
    )


@app.route("/api/conversation/<uuid>")
def get_conversation(uuid: str) -> tuple[Response, int] | Response:
    """Get full conversation details."""
    conversation = db.conversations.find_one({"uuid": uuid})

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    conversation["_id"] = str(conversation["_id"])
    return jsonify(conversation)


@app.route("/api/export/conversation/<uuid>")
def export_conversation(uuid: str) -> tuple[Response, int] | Response:
    """Export single conversation as JSON."""
    conversation = db.conversations.find_one({"uuid": uuid}, {"_id": 0})

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    # Create JSON file in memory
    output = BytesIO()
    output.write(json.dumps(conversation, indent=2, default=str).encode())
    output.seek(0)

    return send_file(
        output,
        mimetype="application/json",
        as_attachment=True,
        download_name=f"conversation_{uuid}.json",
    )


@app.route("/api/export/messages", methods=["POST"])
def export_messages() -> tuple[Response, int] | Response:
    """Export selected messages as JSON or CSV."""
    import pandas as pd

    data: dict[str, Any] = request.json or {}
    conversation_uuid = data.get("conversation_uuid")
    message_indices: list[int] = data.get("message_indices", [])
    export_format = data.get("format", "json")

    conversation = db.conversations.find_one({"uuid": conversation_uuid})

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    # Extract selected messages
    messages: list[dict[str, Any]] = []
    chat_messages: list[dict[str, Any]] = conversation.get("chat_messages", [])
    for idx in message_indices:
        if idx < len(chat_messages):
            msg = chat_messages[idx].copy()
            msg["conversation_uuid"] = conversation_uuid
            msg["conversation_name"] = conversation.get("name", "")
            messages.append(msg)

    if export_format == "csv":
        # Convert to CSV
        df: pd.DataFrame = pd.DataFrame(messages)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"messages_{conversation_uuid}.csv",
        )
    else:
        # Export as JSON
        output = BytesIO()
        output.write(json.dumps(messages, indent=2, default=str).encode())
        output.seek(0)

        return send_file(
            output,
            mimetype="application/json",
            as_attachment=True,
            download_name=f"messages_{conversation_uuid}.json",
        )


@app.route("/api/stats")
def get_stats() -> Response:
    """Get database statistics."""
    date_range_result = list(
        db.conversations.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "earliest": {"$min": "$created_at"},
                        "latest": {"$max": "$updated_at"},
                    }
                }
            ]
        )
    )

    stats: dict[str, Any] = {
        "total_conversations": db.conversations.count_documents({}),
        "total_users": db.users.count_documents({}),
        "total_projects": db.projects.count_documents({}),
        "total_imports": db.import_history.count_documents({}),
        "accounts": db.conversations.distinct("_account_name"),
        "date_range": date_range_result[0] if date_range_result else {},
        "messages_by_sender": list(
            db.conversations.aggregate(
                [
                    {"$unwind": "$chat_messages"},
                    {"$group": {"_id": "$chat_messages.sender", "count": {"$sum": 1}}},
                ]
            )
        ),
    }

    return jsonify(stats)


@app.route("/api/accounts")
def get_accounts() -> Response:
    """Get list of imported accounts."""
    accounts: list[str] = db.conversations.distinct("_account_name")
    return jsonify(accounts)


@app.route(
    "/api/attachment/<conversation_uuid>/<int:message_index>/<int:attachment_index>"
)
def download_attachment(
    conversation_uuid: str, message_index: int, attachment_index: int
) -> tuple[Response, int] | Response:
    """Download a specific user attachment from a conversation message."""
    conversation = db.conversations.find_one({"uuid": conversation_uuid})

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    chat_messages: list[dict[str, Any]] = conversation.get("chat_messages", [])
    if message_index >= len(chat_messages):
        return jsonify({"error": "Message not found"}), 404

    message = chat_messages[message_index]
    attachments: list[dict[str, Any]] = message.get("attachments", [])

    if attachment_index >= len(attachments):
        return jsonify({"error": "Attachment not found"}), 404

    attachment = attachments[attachment_index]

    # Use Attachment model for proper structure
    try:
        attachment_obj = Attachment(**attachment)
        response_data: dict[str, Any] = {
            "filename": attachment_obj.file_name or f"attachment_{attachment_index}",
            "content_type": (
                "text/plain; charset=utf-8"
                if attachment_obj.file_type == "txt"
                else "application/octet-stream"
            ),
            "size": attachment_obj.file_size or 0,
            "data": attachment_obj.extracted_content or "",
            "file_type": attachment_obj.file_type,
            "is_user_attachment": True,
            "download_url": (
                f"/api/attachment/{conversation_uuid}/{message_index}/{attachment_index}/download"
            ),
        }
    except Exception as e:
        logger.error("attachment_processing_error", error=str(e))
        # Fallback to raw data
        response_data = {
            "filename": attachment.get("file_name", f"attachment_{attachment_index}"),
            "content_type": (
                "text/plain; charset=utf-8"
                if attachment.get("file_type") == "txt"
                else "application/octet-stream"
            ),
            "size": attachment.get("file_size", 0),
            "data": attachment.get("extracted_content", ""),
            "file_type": attachment.get("file_type"),
            "is_user_attachment": True,
            "download_url": (
                f"/api/attachment/{conversation_uuid}/{message_index}/{attachment_index}/download"
            ),
        }

    return jsonify(response_data)


@app.route(
    "/api/artifact/<conversation_uuid>/<int:message_index>/<int:content_index>"
)
def get_artifact(
    conversation_uuid: str, message_index: int, content_index: int
) -> tuple[Response, int] | Response:
    """Get a specific assistant artifact from a conversation message content."""
    conversation = db.conversations.find_one({"uuid": conversation_uuid})

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    chat_messages: list[dict[str, Any]] = conversation.get("chat_messages", [])
    if message_index >= len(chat_messages):
        return jsonify({"error": "Message not found"}), 404

    message = chat_messages[message_index]

    # Only assistant messages have artifacts in content blocks
    if message.get("sender") != "assistant":
        return jsonify({"error": "Only assistant messages contain artifacts"}), 400

    content_blocks: list[dict[str, Any]] = message.get("content", [])

    if content_index >= len(content_blocks):
        return jsonify({"error": "Content block not found"}), 404

    content_block = content_blocks[content_index]

    # Use ContentBlock model for proper structure
    try:
        content_obj = ContentBlock(**content_block)

        # Extract content based on type
        if content_obj.type == ContentBlockType.TEXT:
            content_data = content_obj.text or ""
            content_type = "text/plain; charset=utf-8"
            filename = f"assistant_response_{content_index}.txt"
        elif content_obj.type == ContentBlockType.THINKING:
            content_data = content_obj.thinking or ""
            content_type = "text/plain; charset=utf-8"
            filename = f"assistant_thinking_{content_index}.txt"
        else:
            content_data = content_obj.data or content_obj.text or ""
            content_type = "text/plain; charset=utf-8"
            filename = f"assistant_artifact_{content_index}.txt"

        response_data: dict[str, Any] = {
            "filename": filename,
            "content_type": content_type,
            "size": len(content_data.encode("utf-8")) if content_data else 0,
            "data": content_data,
            "artifact_type": content_obj.type.value,
            "is_assistant_artifact": True,
            "summaries": content_obj.summaries or [],
            "start_timestamp": content_obj.start_timestamp,
            "stop_timestamp": content_obj.stop_timestamp,
            "citations": content_obj.citations or [],
        }

    except Exception as e:
        logger.error("content_block_processing_error", error=str(e))
        # Fallback to raw data
        response_data = {
            "filename": f"assistant_artifact_{content_index}.txt",
            "content_type": "text/plain; charset=utf-8",
            "size": len(str(content_block).encode("utf-8")),
            "data": str(content_block),
            "artifact_type": content_block.get("type", "unknown"),
            "is_assistant_artifact": True,
            "summaries": content_block.get("summaries", []),
            "start_timestamp": content_block.get("start_timestamp"),
            "stop_timestamp": content_block.get("stop_timestamp"),
            "citations": content_block.get("citations", []),
        }

    return jsonify(response_data)


@app.route(
    "/api/attachment/<conversation_uuid>/<int:message_index>/<int:attachment_index>/download"
)
def download_attachment_file(
    conversation_uuid: str, message_index: int, attachment_index: int
) -> tuple[Response, int] | Response:
    """Download the actual attachment file."""
    conversation = db.conversations.find_one({"uuid": conversation_uuid})

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    chat_messages: list[dict[str, Any]] = conversation.get("chat_messages", [])
    if message_index >= len(chat_messages):
        return jsonify({"error": "Message not found"}), 404

    message = chat_messages[message_index]
    attachments: list[dict[str, Any]] = message.get("attachments", [])

    if attachment_index >= len(attachments):
        return jsonify({"error": "Attachment not found"}), 404

    attachment = attachments[attachment_index]

    # Get attachment data using the Attachment model
    try:
        attachment_obj = Attachment(**attachment)

        # Prepare file data
        filename = attachment_obj.file_name or f"attachment_{attachment_index}"
        content = attachment_obj.extracted_content or ""
        file_type = attachment_obj.file_type or "txt"

        # Ensure filename has extension
        if "." not in filename and file_type:
            filename = f"{filename}.{file_type}"

        # Create response with proper headers for download
        response = make_response(content)
        response.headers.set("Content-Disposition", "attachment", filename=filename)
        response.headers.set(
            "Content-Type",
            "text/plain; charset=utf-8" if file_type == "txt" else "application/octet-stream",
        )
        response.headers.set("Content-Length", str(len(content.encode("utf-8"))))

        return response

    except Exception as e:
        logger.error("download_response_error", error=str(e))
        return jsonify({"error": "Failed to prepare download"}), 500


@app.route("/api/recent/<collection_name>")
def get_recent_items(collection_name: str) -> tuple[Response, int] | Response:
    """Get recent items from a collection with pagination."""
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, max(5, int(request.args.get("per_page", 10))))

    # Validate collection name
    valid_collections = ["conversations", "projects", "users", "import_history"]
    if collection_name not in valid_collections:
        return jsonify({"error": "Invalid collection"}), 400

    collection: Collection[dict[str, Any]] = getattr(db, collection_name)

    # Get total count
    total_count = collection.count_documents({})
    total_pages = (total_count + per_page - 1) // per_page
    skip = (page - 1) * per_page

    # Get items based on collection
    items: list[dict[str, Any]]
    if collection_name == "conversations":
        items = list(
            collection.find({}, {"chat_messages": 0, "_id": 0})
            .sort("created_at", -1)
            .skip(skip)
            .limit(per_page)
        )
    elif collection_name == "import_history":
        items = list(
            collection.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .skip(skip)
            .limit(per_page)
        )
    elif collection_name == "projects":
        items = list(
            collection.find({}, {"_id": 0})
            .sort("created_at", -1)
            .skip(skip)
            .limit(per_page)
        )

        # Enhance projects with computed counts
        for project in items:
            project["docs_count"] = len(project.get("docs", []))
            project["templates_count"] = len(project.get("prompt_template", []))

            if project.get("name"):
                related_conversations = list(
                    db.conversations.find(
                        {
                            "$or": [
                                {"name": {"$regex": project["name"], "$options": "i"}},
                                {
                                    "chat_messages.text": {
                                        "$regex": project["name"],
                                        "$options": "i",
                                    }
                                },
                            ]
                        },
                        {"_id": 1, "chat_messages.attachments": 1},
                    )
                )

                project["related_conversations_count"] = len(related_conversations)

                total_artifacts = 0
                for conv in related_conversations:
                    for msg in conv.get("chat_messages", []):
                        total_artifacts += len(msg.get("attachments", []))

                project["artifacts_count"] = total_artifacts
            else:
                project["related_conversations_count"] = 0
                project["artifacts_count"] = 0
    else:
        items = list(
            collection.find({}, {"_id": 0})
            .sort("created_at", -1)
            .skip(skip)
            .limit(per_page)
        )

    return jsonify(
        {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages,
            },
        }
    )


# Initialize database on startup
with app.app_context():
    DataProcessor.setup_indexes()


if __name__ == "__main__":
    app.run(host=settings.host, debug=settings.debug, port=settings.port)
