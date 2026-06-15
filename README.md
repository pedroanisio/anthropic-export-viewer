---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "Claude Opus 4.8 via Claude Code"
  date: "2026-06-15"
---

# Anthropic Export Viewer

> Self-hosted viewer for your Anthropic data export. Turn the raw ZIP of JSON
> into conversations you can read, search, visualize, and re-export — without
> sending your history to anyone.

[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000.svg)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.x-47A248.svg)](https://www.mongodb.com/)
[![Type-checked: mypy](https://img.shields.io/badge/types-mypy%20strict-2a6db2.svg)](https://mypy-lang.org/)
[![Lint: ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://docs.astral.sh/ruff/)
[![Coverage](https://img.shields.io/badge/coverage-%E2%89%A591%25-brightgreen.svg)](#running-tests)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](#license)

## Disclaimer

This work is subject to the methodological caveats and commitments described in [@DISCLAIMER.md](./DISCLAIMER.md).
> No statement or premise not backed by a real logical definition or verifiable reference should be taken for granted.

---

## Overview

When you export your Anthropic data, you receive a ZIP full of raw JSON —
technically complete, but practically unreadable. **Anthropic Export Viewer**
imports that archive into a local, self-hosted application so you can actually
*use* your history: read it, search it, see your usage trends, and export
selections back out.

It is a **reader, not a rewriter**. It runs where you run it, your data never
leaves your machine, and imports are deduplicated by UUID so re-importing or
merging accounts never drops or duplicates a conversation.

For *why* this project exists and what it deliberately does **not** do, see
[PURPOSE.md](./PURPOSE.md).

### Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Development](#development)
- [Database Schema](#database-schema)
- [Docker Deployment](#docker-deployment)
- [Backup & Restore](#backup--restore)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| | |
|---|---|
| 📤 **Multi-account import** | Import exports from multiple Anthropic accounts into one place |
| 🔒 **UUID deduplication** | Re-imports and account merges never drop or duplicate conversations |
| 📦 **Direct ZIP processing** | Upload and extract Anthropic export ZIPs without manual unpacking |
| 🔍 **Search & filter** | Search conversations by text, account, and date range, with sorting and pagination |
| 📊 **Visualization** | Browse conversations, projects, messages, and attachments |
| 📈 **Stats & trends** | Interactive charts: volume over time, distributions, and a GitHub-style activity heatmap |
| 💾 **Export** | Re-export any conversation or message selection as JSON, CSV, or ZIP |
| 🚀 **One-command deploy** | Docker Compose setup with health checks and optional admin UI |
| ✅ **Type-safe** | Full type annotations under strict `mypy` |
| 🧪 **Tested** | `pytest` suite with a ≥91% coverage gate |

---

## Tech Stack

| Layer | Choice |
|---|---|
| **Backend** | Flask 3.x · Python 3.11+ |
| **Database** | MongoDB 7.x (via PyMongo) |
| **Validation** | Pydantic v2 |
| **Configuration** | pydantic-settings |
| **Data export** | pandas (CSV serialization) |
| **Logging** | structlog (console or JSON) |
| **Testing** | pytest · pytest-cov · mongomock |
| **Quality** | ruff · mypy (strict) · pre-commit |

---

## Quick Start

### Option 1 — Docker (recommended)

```bash
# Clone the repository
git clone https://github.com/pedroanisio/anthropic-export-viewer.git
cd anthropic-export-viewer

# Copy the environment template and set required secrets
cp env.example .env
# Edit SECRET_KEY, MONGO_ROOT_PASSWORD,
# APP_BASIC_AUTH_USERNAME, and APP_BASIC_AUTH_PASSWORD

# Start the stack
docker compose up -d

# Open the application
open http://localhost:5000
```

### Option 2 — Local development

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Configure environment (optional — defaults work for local dev)
cp env.example .env

# Run the application
cd src
python app.py

# Open http://localhost:5000
```

---

## Configuration

Configuration is managed entirely through environment variables, with type-safe
defaults provided by `pydantic-settings`.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | auto-generated | Flask session secret key |
| `FLASK_ENV` | `development` | Environment mode (`development` / `production`) |
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `5000` | Server port |
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `DB_NAME` | `anthropic_data` | Database name |
| `UPLOAD_FOLDER` | `./uploads` | Upload directory |
| `MAX_CONTENT_LENGTH` | `524288000` | Max upload size in bytes (500 MB) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `console` | Log format (`console` or `json`) |
| `APP_BASIC_AUTH_USERNAME` | _unset_ | Required app username when `FLASK_ENV=production` |
| `APP_BASIC_AUTH_PASSWORD` | _unset_ | Required app password when `FLASK_ENV=production` |
| `MONGO_ROOT_USERNAME` | _unset_ | MongoDB root user (required by Docker Compose) |
| `MONGO_ROOT_PASSWORD` | _unset_ | MongoDB root password (required by Docker Compose) |
| `MONGO_EXPRESS_USERNAME` | _unset_ | mongo-express login (only for the `tools` profile) |
| `MONGO_EXPRESS_PASSWORD` | _unset_ | mongo-express password (only for the `tools` profile) |

### Example `.env`

```bash
SECRET_KEY=<generated-key>
FLASK_ENV=production
DEBUG=false
MONGO_URI=mongodb://anthropic_admin:<password>@mongodb:27017/anthropic_data?authSource=admin
APP_BASIC_AUTH_USERNAME=<username>
APP_BASIC_AUTH_PASSWORD=<strong-password>
LOG_LEVEL=INFO
LOG_FORMAT=json
```

> See [`env.example`](./env.example) for the full, annotated template.

---

## Usage Guide

### 1. Export your Anthropic data

1. Log in to [claude.ai](https://claude.ai).
2. Go to **Settings → Account**.
3. Click **Export Data**.
4. Download the ZIP file.

### 2. Import the data

1. Navigate to `http://localhost:5000/upload`.
2. Upload your ZIP file.
3. Enter an account name (e.g. `Personal`, `Work`).
4. Click **Import**. Re-imports are deduplicated automatically.

### 3. Browse & search

- **Conversations** — search by text, filter by account and date range, sort by
  date, message count, or attachments.
- **Projects** — filter by type (public / private / starter).
- **Details** — click any item to view its full content and attachments.

### 4. View stats & trends

The Stats page (`/stats`) provides interactive visualizations:

- **Summary cards** — total conversations, messages, daily averages, trend indicators.
- **Conversations over time** — line chart with day / week / month grouping.
- **Message distribution** — doughnut chart of human vs. assistant messages.
- **Message volume** — stacked bar chart of message counts over time.
- **Account distribution** — breakdown by imported account.
- **Activity by day of week** and **by hour** — find your most active periods.
- **Conversation length distribution** — message-count buckets.
- **Activity heatmap** — GitHub-style calendar of daily activity.

Use the time-range selector (7 days, 30 days, 90 days, 1 year, All time) to
adjust the view.

### 5. Export data

- **Single conversation** — export as JSON, or as a ZIP bundling attachments.
- **Selected messages** — export the current selection as JSON or CSV.
- **Bulk** — use the Export tab for bulk operations.

---

## API Reference

### Web pages (HTML)

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Dashboard with statistics |
| `/conversations` | GET | Conversation browser |
| `/projects` | GET | Project browser with filtering |
| `/upload` | GET / POST | Upload and import export ZIPs |
| `/analytics` | GET | Analytics dashboard |
| `/stats` | GET | Stats & trends with interactive charts |
| `/export` | GET | Export tools page |
| `/health` | GET | Container health check (JSON; bypasses Basic Auth) |

### JSON API

| Endpoint | Method | Description |
|---|---|---|
| `/api/search/conversations` | POST | Search with date-range filtering, pagination, and sorting |
| `/api/conversation/<uuid>` | GET | Get a single conversation |
| `/api/project/<uuid>` | GET | Get project details |
| `/api/export/conversation/<uuid>` | GET | Export a conversation as JSON |
| `/api/export/conversation/<uuid>/zip` | GET | Export a conversation with attachments as ZIP |
| `/api/export/messages` | POST | Export a selection of messages |
| `/api/stats` | GET | Database statistics |
| `/api/stats/timeseries` | GET | Time-series data for charts |
| `/api/stats/heatmap` | GET | Heatmap data for the activity calendar |
| `/api/accounts` | GET | List all imported accounts |
| `/api/attachment/<conv>/<msg_index>/<att_index>` | GET | Fetch a user attachment |
| `/api/attachment/<conv>/<msg_index>/<att_index>/download` | GET | Download an attachment file |
| `/api/artifact/<conv>/<msg_index>/<content_index>` | GET | Fetch an AI-generated artifact |
| `/api/recent/<collection>` | GET | Get recent items from a collection |

---

## Project Structure

```text
anthropic-export-viewer/
├── CLAUDE.md                 # Project guidelines for AI agents
├── PURPOSE.md                # Why this project exists
├── DISCLAIMER.md             # Methodological caveats (referenced by all READMEs)
├── README.md                 # This file
├── pyproject.toml            # Build, lint, type-check, and test configuration
├── .pre-commit-config.yaml   # Pre-commit hooks
├── requirements-dev.txt      # Development dependencies
├── env.example               # Environment template
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # Container build
├── src/
│   ├── app.py                # Flask application (type-annotated)
│   ├── config.py             # Settings (pydantic-settings)
│   ├── models.py             # Pydantic data models
│   ├── response_models.py    # API response models
│   ├── requirements.txt      # Production dependencies
│   ├── static/               # CSS and static assets
│   └── templates/            # Jinja2 HTML templates
│       ├── base.html
│       ├── index.html
│       ├── upload.html
│       ├── conversations.html
│       ├── projects.html
│       ├── analytics.html
│       ├── stats.html
│       └── export.html
├── tests/
│   ├── conftest.py           # Shared fixtures
│   ├── test_models.py        # Model tests
│   ├── test_config.py        # Configuration tests
│   ├── test_app.py           # API route tests
│   └── integration/          # Integration tests
└── docs/
    ├── adrs.jsonl            # Architecture Decision Records
    └── DATA_DICTIONARY.md    # Field-level data documentation
```

---

## Development

### Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

The suite enforces a **≥91% coverage gate** (configured in `pyproject.toml`).

```bash
# Run all tests (coverage is enforced via pyproject.toml)
pytest

# Coverage report in the terminal
pytest --cov=src --cov-report=term-missing

# A specific file
pytest tests/test_models.py

# Only unit / only integration tests
pytest -m unit
pytest -m integration
```

### Code Quality

```bash
# Type checking (strict mode)
mypy src/

# Linting
ruff check src/
ruff check --fix src/        # auto-fix

# Formatting
ruff format src/

# Run all pre-commit hooks
pre-commit run --all-files
```

---

## Database Schema

### Conversations collection

```javascript
{
  "uuid": "unique-id",
  "name": "Conversation Name",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z",
  "account": { "uuid": "account-uuid" },
  "chat_messages": [
    {
      "uuid": "msg-uuid",
      "sender": "human",
      "text": "Message text",
      "attachments": [],
      "content": []
    }
  ],
  "_account_name": "Personal",
  "_import_id": "abc123",
  "_imported_at": "2024-01-20T15:00:00Z"
}
```

See [`docs/DATA_DICTIONARY.md`](./docs/DATA_DICTIONARY.md) for field-level documentation.

### Deduplication strategy

- Each conversation, user, and project carries a stable UUID.
- `upsert` operations make imports idempotent — duplicates are never created.
- Re-importing the same export, or merging multiple accounts, is safe.
- Import provenance is tracked via the `_import_ids` array.

---

## Docker Deployment

### Production setup

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Set production values in .env
SECRET_KEY=<generated-key>
MONGO_ROOT_USERNAME=anthropic_admin
MONGO_ROOT_PASSWORD=<strong-database-password>
APP_BASIC_AUTH_USERNAME=<app-username>
APP_BASIC_AUTH_PASSWORD=<strong-app-password>
FLASK_ENV=production
DEBUG=false

# Start the services
docker compose up -d
```

### Services

| Service | Port | Description |
|---|---|---|
| `app` | 5000 | Flask application |
| `mongodb` | internal only | MongoDB database |
| `mongo-express` | 8081 | Optional admin UI — `docker compose --profile tools up -d` |

---

## Backup & Restore

### Backup

```bash
docker exec anthropic_mongodb mongodump \
  --username "$MONGO_ROOT_USERNAME" \
  --password "$MONGO_ROOT_PASSWORD" \
  --authenticationDatabase admin \
  --out /data/backup

docker cp anthropic_mongodb:/data/backup ./backup
```

### Restore

```bash
docker cp ./backup anthropic_mongodb:/data/backup

docker exec anthropic_mongodb mongorestore \
  --username "$MONGO_ROOT_USERNAME" \
  --password "$MONGO_ROOT_PASSWORD" \
  --authenticationDatabase admin \
  /data/backup
```

---

## Troubleshooting

| Symptom | Things to check |
|---|---|
| **Large uploads fail** | Increase `MAX_CONTENT_LENGTH`; check Docker memory limits |
| **MongoDB connection errors** | Verify MongoDB is running (`docker ps`); check `MONGO_URI` |
| **Import errors** | Inspect logs (`docker logs anthropic_app`); confirm the ZIP contains valid JSON |

### Viewing logs

```bash
# Application logs
docker logs anthropic_app

# Follow in real time
docker logs -f anthropic_app

# Structured JSON logging
LOG_FORMAT=json docker compose up
```

---

## Security Notes

> ⚠️ **For production use:**

- Generate a secure `SECRET_KEY`.
- Set strong MongoDB and app Basic Auth credentials.
- Keep all secrets in environment variables — never commit them.
- Terminate TLS at an nginx (or equivalent) reverse proxy.
- Keep `mongo-express` disabled unless actively needed.
- Run security scans: `bandit -r src/`.

---

## Roadmap

- [ ] User authentication and multi-user support
- [ ] Elasticsearch integration for advanced search
- [ ] Scheduled automatic imports
- [x] ~~Analytics dashboard with charts~~ — Stats page with Chart.js visualizations
- [ ] Conversation tagging and categorization
- [ ] Batch operations UI
- [ ] Real-time updates via WebSockets

---

## Contributing

1. Fork the repository.
2. Install pre-commit hooks: `pre-commit install`.
3. Create a feature branch.
4. Write tests for new functionality.
5. Ensure all tests pass: `pytest`.
6. Ensure code quality: `pre-commit run --all-files`.
7. Open a Pull Request.

---

## License

Released under the **MIT License**, as declared in [`pyproject.toml`](./pyproject.toml).

---

## Support

- Open an issue on GitHub.
- Check existing issues for known solutions.
- Review the application logs for error details.

---

<sub>Documentation generated with assistance from Claude Opus 4.8 via Claude Code.
See [DISCLAIMER.md](./DISCLAIMER.md) and [PURPOSE.md](./PURPOSE.md).</sub>
