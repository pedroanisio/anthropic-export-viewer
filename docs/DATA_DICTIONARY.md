# Anthropic Data Manager - Data Dictionary

> **Project Overview**: Complete application for managing Anthropic data exports from multiple accounts with deduplication, search, and visualization capabilities.

---

## 📋 Table of Contents
- [Core Data Models](#core-data-models)
- [Database Collections](#database-collections)
- [API Endpoints](#api-endpoints)
- [System Components](#system-components)
- [User Interface Concepts](#user-interface-concepts)
- [Configuration & Deployment](#configuration--deployment)
- [Data Flow & Processing](#data-flow--processing)

---

## 🎯 Core Data Models

### 1. Conversation
**Primary entity representing a chat session with Claude AI**

| Field | Type | Description | Source |
|-------|------|-------------|---------|
| `uuid` | `string` | Unique conversation identifier | MongoDB |
| `name` | `string` | User-assigned conversation title | MongoDB |
| `account` | `Account` | Associated account information | MongoDB |
| `chat_messages` | `List[Message]` | Array of messages in conversation | MongoDB |
| `created_at` | `string` | ISO timestamp of conversation start | MongoDB |
| `updated_at` | `string` | ISO timestamp of last update | MongoDB |
| `_account_name` | `string` | Account name for indexing | Import System |
| `_import_id` | `string` | Import batch identifier | Import System |
| `_import_ids` | `List[string]` | List of all import IDs | Import System |
| `_imported_at` | `string` | Import timestamp | Import System |
| `summary` | `string` | AI-generated summary | Optional |
| `model` | `string` | Claude model used | Optional |
| `artifacts` | `List[Artifact]` | Generated artifacts | Optional |
| `project_id` | `string` | Associated project ID | Optional |
| `is_deleted` | `boolean` | Soft deletion flag | Optional |
| `tags` | `List[string]` | User-assigned tags | Optional |

### 2. Message
**Individual message within a conversation**

| Field | Type | Description | Source |
|-------|------|-------------|---------|
| `uuid` | `string` | Unique message identifier | MongoDB |
| `sender` | `string` | Message sender: 'human' or 'assistant' | MongoDB |
| `text` | `string` | Plain text version of message | MongoDB |
| `content` | `List[ContentBlock]` | Structured content blocks | MongoDB |
| `attachments` | `List[Attachment]` | User-uploaded files | MongoDB |
| `files` | `List[Dict]` | Files array (related to attachments) | MongoDB |
| `created_at` | `string` | Message creation timestamp | MongoDB |
| `updated_at` | `string` | Message update timestamp | MongoDB |
| `index` | `integer` | Sequential message index | Optional |
| `type` | `string` | Message type (prompt/response) | Legacy |
| `role` | `MessageRole` | Message role enum | Legacy |

### 3. ContentBlock
**Structured content within assistant messages**

| Field | Type | Description | Source |
|-------|------|-------------|---------|
| `type` | `ContentBlockType` | Block type: 'text' or 'thinking' | MongoDB |
| `text` | `string` | Response text content | MongoDB |
| `thinking` | `string` | AI thinking process content | MongoDB |
| `citations` | `List[Dict]` | Citation references | MongoDB |
| `summaries` | `List[Dict]` | AI-generated summaries | MongoDB |
| `start_timestamp` | `string` | Content generation start | MongoDB |
| `stop_timestamp` | `string` | Content generation end | MongoDB |
| `cut_off` | `boolean` | Whether content was truncated | MongoDB |
| `flags` | `Any` | Content flags | MongoDB |
| `data` | `string` | Alternative content field | Legacy |
| `language` | `string` | Programming language for code | Legacy |
| `source` | `Dict` | Source info for media | Legacy |
| `title` | `string` | Artifact/document title | Legacy |
| `id` | `string` | Unique artifact identifier | Legacy |
| `mime_type` | `string` | MIME type for artifacts | Legacy |

### 4. Attachment
**User-uploaded files in conversations**

| Field | Type | Description | Source |
|-------|------|-------------|---------|
| `file_name` | `string` | Original filename | MongoDB |
| `file_type` | `string` | File extension/type | MongoDB |
| `file_size` | `integer` | File size in bytes | MongoDB |
| `extracted_content` | `string` | Extracted text content | MongoDB |
| `file_id` | `string` | Unique file identifier | Legacy |
| `media_type` | `string` | MIME type | Legacy |
| `size` | `integer` | Alternative size field | Legacy |
| `extracted_text` | `string` | Alternative extracted content | Legacy |

### 5. Artifact
**AI-generated content objects**

| Field | Type | Description | Source |
|-------|------|-------------|---------|
| `id` | `string` | Unique artifact identifier | MongoDB |
| `type` | `string` | Artifact type (code, document, etc.) | MongoDB |
| `title` | `string` | Artifact title | MongoDB |
| `content` | `string` | Artifact content | MongoDB |
| `language` | `string` | Programming language if code | MongoDB |
| `mime_type` | `string` | MIME type | MongoDB |
| `created_at` | `datetime` | Creation timestamp | MongoDB |
| `updated_at` | `datetime` | Last update timestamp | MongoDB |

### 6. Account
**User account information**

| Field | Type | Description | Source |
|-------|------|-------------|---------|
| `uuid` | `string` | Account UUID | MongoDB |

### 7. Project
**Claude Projects (if included in export)**

| Field | Type | Description | Source |
|-------|------|-------------|---------|
| `uuid` | `string` | Project UUID | MongoDB |
| `name` | `string` | Project name | MongoDB |
| `description` | `string` | Project description | MongoDB |
| `is_private` | `boolean` | Privacy flag | MongoDB |
| `is_starter_project` | `boolean` | Starter project flag | MongoDB |
| `docs` | `List[Dict]` | Project documents | MongoDB |
| `prompt_template` | `List[Dict]` | Prompt templates | MongoDB |
| `created_at` | `string` | Creation timestamp | MongoDB |
| `updated_at` | `string` | Update timestamp | MongoDB |
| `_account_name` | `string` | Account name | Import System |
| `_import_id` | `string` | Import identifier | Import System |
| `_imported_at` | `string` | Import timestamp | Import System |

### 8. User
**User information (if included in export)**

| Field | Type | Description | Source |
|-------|------|-------------|---------|
| `uuid` | `string` | User UUID | MongoDB |
| `id` | `string` | Alternative identifier | MongoDB |
| `email` | `string` | User email | MongoDB |
| `_account_name` | `string` | Account name | Import System |
| `_import_id` | `string` | Import identifier | Import System |
| `_imported_at` | `string` | Import timestamp | Import System |

---

## 🗄️ Database Collections

### MongoDB Collections Overview

| Collection | Purpose | Primary Key | Indexes |
|------------|---------|-------------|---------|
| `conversations` | Store chat conversations | `uuid` | uuid, account.uuid, created_at, name (TEXT) |
| `users` | Store user information | `uuid` | uuid, email |
| `projects` | Store Claude Projects | `uuid` | uuid, name (TEXT) |
| `import_history` | Track import operations | `import_id` | import_id, timestamp |

### Index Strategy

```javascript
// Conversations Collection Indexes
db.conversations.createIndex({"uuid": 1}, {unique: true})
db.conversations.createIndex({"account.uuid": 1})
db.conversations.createIndex({"created_at": 1})
db.conversations.createIndex({"name": "text"})

// Users Collection Indexes
db.users.createIndex({"uuid": 1}, {unique: true})
db.users.createIndex({"email": 1}, {sparse: true})

// Projects Collection Indexes
db.projects.createIndex({"uuid": 1}, {unique: true})
db.projects.createIndex({"name": "text"})

// Import History Collection Indexes
db.import_history.createIndex({"import_id": 1})
db.import_history.createIndex({"timestamp": 1})
```

---

## 🔌 API Endpoints

### Web Routes (Flask)

| Route | Method | Purpose | Template |
|-------|--------|---------|----------|
| `/` | GET | Main dashboard with statistics | `index.html` |
| `/conversations` | GET | Conversations browser page | `conversations.html` |
| `/projects` | GET | Projects browser with pagination | `projects.html` |
| `/analytics` | GET | Analytics dashboard | `analytics.html` |
| `/export` | GET | Export tools page | `export.html` |
| `/upload` | GET/POST | File upload interface | `upload.html` |

### REST API Endpoints

| Endpoint | Method | Purpose | Parameters |
|----------|--------|---------|------------|
| `/api/search/conversations` | POST | Search conversations with filters | query, filters, page, per_page, sort_by |
| `/api/conversation/<uuid>` | GET | Get full conversation details | uuid |
| `/api/project/<uuid>` | GET | Get project details | uuid |
| `/api/export/conversation/<uuid>` | GET | Export single conversation as JSON | uuid |
| `/api/export/messages` | POST | Export selected messages (JSON/CSV) | conversation_uuid, message_indices, format |
| `/api/stats` | GET | Get database statistics | - |
| `/api/accounts` | GET | List imported accounts | - |
| `/api/attachment/<uuid>/<msg_idx>/<att_idx>` | GET | Get attachment metadata | conversation_uuid, message_index, attachment_index |
| `/api/artifact/<uuid>/<msg_idx>/<cnt_idx>` | GET | Get assistant artifact | conversation_uuid, message_index, content_index |
| `/api/recent/<collection>` | GET | Get recent items with pagination | collection_name, page, per_page |

---

## ⚙️ System Components

### 1. DataProcessor Class
**Core data processing engine**

| Method | Purpose | Parameters | Returns |
|--------|---------|------------|---------|
| `setup_indexes()` | Create MongoDB indexes | - | void |
| `process_zip()` | Process uploaded ZIP file | filepath, account_name | Dict[stats] |
| `_load_conversations()` | Load conversations with deduplication | filepath, import_id, account_name | Dict[loaded, duplicates] |
| `_load_users()` | Load users with deduplication | filepath, import_id, account_name | Dict[loaded, duplicates] |
| `_load_projects()` | Load projects with deduplication | filepath, import_id, account_name | Dict[loaded, duplicates] |

### 2. Import System
**File processing and data import pipeline**

| Component | Purpose | Technology |
|-----------|---------|------------|
| ZIP Extraction | Extract Anthropic export files | Python zipfile |
| JSON Processing | Parse conversation/project/user data | Python json |
| Deduplication | Prevent duplicate imports | MongoDB upsert |
| Metadata Tracking | Track import history | MongoDB import_history |
| File Cleanup | Clean temporary files | Python shutil |

### 3. Search System
**Advanced search and filtering capabilities**

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| Text Search | MongoDB Text Index | Full-text search in conversations |
| Aggregation Pipeline | MongoDB Aggregation | Complex queries with computed fields |
| Pagination | Skip/Limit with Counting | Handle large result sets |
| Sorting | Multiple sort fields | Order by date, message count, etc. |
| Filtering | Query Building | Filter by account, date, attachments |

---

## 🎨 User Interface Concepts

### 1. Dashboard Components

| Component | Purpose | Data Source |
|-----------|---------|-------------|
| Statistics Cards | Show totals (conversations, users, projects) | MongoDB counts |
| Recent Imports | Display import history | import_history collection |
| Quick Actions | Navigation buttons | Static UI |
| Activity Summary | Overview of data | Computed statistics |

### 2. Conversations Browser

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| Search Bar | Real-time text search | Find conversations by content |
| Filter Panel | Account, date, attachment filters | Narrow down results |
| Sort Options | Multiple sort fields | Order results |
| Conversation Cards | Display conversation metadata | Show key information |
| Pagination | Page-based navigation | Handle large datasets |
| Export Actions | Individual/bulk export | Data portability |

### 3. Projects Browser

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| Card Layout | Visual project cards | Easy browsing |
| Type Filters | Private/Public/Starter badges | Categorize projects |
| Search | Name/description search | Find specific projects |
| Computed Metrics | Docs, templates, conversations count | Show project activity |
| Pagination | Page-based navigation | Handle many projects |

### 4. Analytics Dashboard

| Metric | Calculation | Purpose |
|--------|-------------|---------|
| Total Conversations | Direct count | Volume indicator |
| Message Distribution | Sender aggregation | Usage patterns |
| Account Activity | Per-account statistics | Multi-account analysis |
| Date Range Analysis | Min/max date aggregation | Time span coverage |
| Attachment Usage | Attachment counting | File usage patterns |

---

## 🚀 Configuration & Deployment

### 1. Flask Application Configuration

| Setting | Default | Purpose |
|---------|---------|---------|
| `SECRET_KEY` | 'your-secret-key-change-in-production' | Session security |
| `UPLOAD_FOLDER` | './uploads' | Temporary file storage |
| `MAX_CONTENT_LENGTH` | 500MB | File upload limit |
| `MONGO_URI` | 'mongodb://localhost:27017/' | Database connection |
| `DB_NAME` | 'anthropic_data' | Database name |

### 2. Docker Services

| Service | Image | Purpose | Ports |
|---------|-------|---------|-------|
| `mongodb` | mongo:7.0 | Primary database | 27017 |
| `app` | Custom build | Flask application | 5000 |
| `mongo-express` | mongo-express:latest | Database admin UI | 8081 |

### 3. Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `MONGO_URI` | Database connection string | mongodb://admin:pass@host:27017/ |
| `FLASK_ENV` | Flask environment | production |
| `SECRET_KEY` | Application secret | your-secret-key-here |
| `MAX_CONTENT_LENGTH` | Upload limit | 524288000 |

### 4. Docker Volumes

| Volume | Purpose | Mount Point |
|--------|---------|-------------|
| `mongo_data` | MongoDB data persistence | /data/db |
| `mongo_config` | MongoDB configuration | /data/configdb |
| `./src` | Application code | /app |
| `./src/uploads` | Upload directory | /app/uploads |
| `./src/templates` | HTML templates | /app/templates |

---

## 📊 Data Flow & Processing

### 1. Import Process Flow

```
ZIP Upload → Extraction → JSON Parsing → Deduplication → MongoDB Storage
     ↓            ↓           ↓              ↓              ↓
  File Save → Temp Dir → Data Objects → Upsert Ops → Collections
     ↓            ↓           ↓              ↓              ↓
  Validation → Processing → Validation → Duplicate Check → Index Update
     ↓            ↓           ↓              ↓              ↓
  Cleanup → Temp Cleanup → Import Log → Statistics → Response
```

### 2. Search Query Flow

```
User Query → Filter Building → MongoDB Query → Aggregation → Results
     ↓            ↓              ↓              ↓            ↓
  UI Input → Query Object → Pipeline → Computed Fields → Pagination
     ↓            ↓              ↓              ↓            ↓
  Validation → Sanitization → Execution → Sorting → JSON Response
```

### 3. Export Process Flow

```
Export Request → Data Retrieval → Format Conversion → File Generation
      ↓              ↓                 ↓                  ↓
  Parameters → MongoDB Query → JSON/CSV → In-Memory File
      ↓              ↓                 ↓                  ↓
  Validation → Data Extraction → Pandas/JSON → BytesIO
      ↓              ↓                 ↓                  ↓
  Processing → Result Set → Serialization → Download Response
```

---

## 🔍 Enums & Constants

### MessageRole Enum
```python
HUMAN = "human"        # User messages
ASSISTANT = "assistant" # AI responses
USER = "user"          # Legacy value
PROMPT = "prompt"      # Legacy value
RESPONSE = "response"  # Legacy value
```

### ContentBlockType Enum
```python
TEXT = "text"          # Assistant response text
THINKING = "thinking"  # AI thinking process
PARAGRAPH = "p"        # HTML paragraph
CODE = "pre"          # Code blocks
IMAGE = "image"       # Image content
DOCUMENT = "document" # Document artifacts
ARTIFACT = "artifact" # General artifacts
```

### File Upload Limits
```python
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'.zip'}
```

---

## 📚 Dependencies & Technologies

### Python Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| `flask` | Latest | Web framework |
| `flask-cors` | Latest | CORS support |
| `pymongo` | Latest | MongoDB driver |
| `pandas` | Latest | Data processing |
| `werkzeug` | Latest | WSGI utilities |
| `python-dotenv` | Latest | Environment variables |
| `pydantic` | Latest | Data validation |

### External Services
| Service | Purpose | Version |
|---------|---------|---------|
| MongoDB | Primary database | 7.0 |
| Mongo Express | Database admin UI | Latest |
| Bootstrap | Frontend framework | 5.3.0 |
| Bootstrap Icons | Icon library | 1.11.0 |

---

## 🎯 Key Business Logic

### Deduplication Strategy
- **Primary Key**: UUID field for each entity type
- **Method**: MongoDB upsert operations
- **Tracking**: `_import_ids` array tracks all imports
- **Metadata**: Import timestamp and account tracking

### Search Capabilities
- **Full-text search** on conversation names and content
- **Filtering** by account, date, attachments
- **Sorting** by date, message count, attachment count
- **Pagination** with configurable page sizes

### Export Functionality
- **Individual conversations** as JSON
- **Selected messages** as JSON or CSV
- **Bulk operations** for multiple items
- **Real-time generation** using BytesIO

### Performance Optimizations
- **Database indexes** on key search fields
- **Aggregation pipelines** for computed statistics
- **Pagination** to limit result sets
- **Field projection** to exclude heavy content when unnecessary

---

*This data dictionary serves as the complete reference for all concepts, models, and components within the Anthropic Data Manager project.*

