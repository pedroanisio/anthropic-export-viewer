# Anthropic Data Exporter Viewer
A complete application for managing Anthropic data exports from multiple accounts with deduplication, search, and visualization.

## Features

- 📤 **Multi-Account Support**: Import data from multiple Anthropic accounts
- 🔒 **Automatic Deduplication**: Prevents duplicate data using UUID-based detection
- 📦 **ZIP File Processing**: Direct upload and extraction of Anthropic export files
- 🔍 **Search & Filter**: Search conversations by text, account, date, and more
- 📊 **Visualization**: View conversations, messages, and statistics
- 💾 **Export Options**: Export conversations and messages as JSON or CSV
- 🚀 **Easy Deployment**: Docker-based setup with one command
- ✅ **Type-Safe**: Full type annotations with strict mypy checking
- 🧪 **Tested**: Comprehensive test suite with pytest

## Tech Stack

- **Backend**: Flask 3.x with Python 3.11+
- **Database**: MongoDB 7.x
- **Validation**: Pydantic v2
- **Configuration**: pydantic-settings
- **Logging**: structlog
- **Testing**: pytest with mongomock

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/pedroanisio/anthropic-data-viewer.git
cd anthropic-data-viewer

# Copy environment template
cp env.example .env

# Start with Docker Compose
docker compose up -d

# Access the application
open http://localhost:5000
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Configure environment (optional - defaults work for local dev)
cp env.example .env

# Run the application
cd src
python app.py

# Access at http://localhost:5000
```

## Project Structure

```
anthropic-data-manager/
├── pyproject.toml          # Project configuration (build, lint, test)
├── .pre-commit-config.yaml # Pre-commit hooks
├── requirements-dev.txt    # Development dependencies
├── env.example             # Environment template
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Container build
├── src/
│   ├── app.py              # Flask application (type-annotated)
│   ├── config.py           # Settings with pydantic-settings
│   ├── models.py           # Pydantic data models
│   ├── requirements.txt    # Production dependencies
│   └── templates/          # Jinja2 HTML templates
│       ├── base.html
│       ├── index.html
│       ├── upload.html
│       ├── conversations.html
│       ├── projects.html
│       ├── analytics.html
│       └── export.html
├── tests/                  # Test suite
│   ├── conftest.py         # Shared fixtures
│   ├── test_models.py      # Model tests
│   ├── test_config.py      # Configuration tests
│   ├── test_app.py         # API route tests
│   └── integration/        # Integration tests
│       └── test_data_processor.py
└── docs/
    └── adrs.jsonl          # Architecture Decision Records
```

## Configuration

Configuration is managed via environment variables with type-safe defaults using `pydantic-settings`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Auto-generated | Flask session secret key |
| `FLASK_ENV` | `development` | Environment mode |
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `5000` | Server port |
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `DB_NAME` | `anthropic_data` | Database name |
| `UPLOAD_FOLDER` | `./uploads` | Upload directory |
| `MAX_CONTENT_LENGTH` | `524288000` | Max upload size (500MB) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `console` | Log format (`console` or `json`) |

### Example `.env` File

```bash
SECRET_KEY=your-secure-secret-key-here
FLASK_ENV=production
DEBUG=false
MONGO_URI=mongodb://admin:password@mongodb:27017/
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Development

### Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_models.py

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Code Quality

```bash
# Type checking (strict mode)
mypy src/

# Linting
ruff check src/

# Auto-fix lint issues
ruff check --fix src/

# Format code
ruff format src/

# Run all pre-commit hooks
pre-commit run --all-files
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard with statistics |
| `/conversations` | GET | Conversations browser |
| `/projects` | GET | Projects browser with filtering |
| `/upload` | GET/POST | Upload and process ZIP files |
| `/analytics` | GET | Analytics dashboard |
| `/export` | GET | Export tools page |
| `/api/search/conversations` | POST | Search with pagination/sorting |
| `/api/conversation/<uuid>` | GET | Get single conversation |
| `/api/project/<uuid>` | GET | Get project details |
| `/api/export/conversation/<uuid>` | GET | Export conversation as JSON |
| `/api/export/messages` | POST | Export selected messages |
| `/api/stats` | GET | Get database statistics |
| `/api/accounts` | GET | List all imported accounts |
| `/api/attachment/...` | GET | Download user attachment |
| `/api/artifact/...` | GET | Get AI-generated artifact |
| `/api/recent/<collection>` | GET | Get recent items |

## Usage Guide

### 1. Export Your Anthropic Data

1. Log in to [claude.ai](https://claude.ai)
2. Go to Settings → Account
3. Click "Export Data"
4. Download the ZIP file

### 2. Import Data

1. Navigate to http://localhost:5000/upload
2. Upload your ZIP file
3. Enter an account name (e.g., "Personal", "Work")
4. Click Import

### 3. Browse & Search

- **Conversations**: Search, sort by date/messages/attachments
- **Projects**: Filter by type (public/private/starter)
- **View Details**: Click any item to see full content

### 4. Export Data

- **Single Conversation**: Click Export JSON in conversation view
- **Multiple Messages**: Select messages and export as JSON/CSV
- **Bulk Export**: Use the Export tab for bulk operations

## Database Schema

### Conversations Collection

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
      "attachments": [...],
      "content": [...]
    }
  ],
  "_account_name": "Personal",
  "_import_id": "abc123",
  "_imported_at": "2024-01-20T15:00:00Z"
}
```

### Deduplication Strategy

- Each conversation, user, and project has a unique UUID
- `upsert` operations prevent duplicates
- Multiple imports from same account won't create duplicates
- Import history tracked with `_import_ids` array

## Docker Deployment

### Production Setup

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Update .env with production values
SECRET_KEY=<generated-key>
FLASK_ENV=production
MONGO_URI=mongodb://admin:securepassword123@mongodb:27017/

# Start services
docker compose up -d
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `app` | 5000 | Flask application |
| `mongodb` | 27017 | MongoDB database |
| `mongo-express` | 8081 | Database admin UI |

## Backup & Restore

### Backup Database

```bash
docker exec anthropic_mongodb mongodump \
  --username admin \
  --password securepassword123 \
  --out /data/backup

docker cp anthropic_mongodb:/data/backup ./backup
```

### Restore Database

```bash
docker cp ./backup anthropic_mongodb:/data/backup

docker exec anthropic_mongodb mongorestore \
  --username admin \
  --password securepassword123 \
  /data/backup
```

## Troubleshooting

### Common Issues

1. **Large file uploads fail**
   - Increase `MAX_CONTENT_LENGTH` environment variable
   - Check Docker memory limits

2. **MongoDB connection errors**
   - Verify MongoDB is running: `docker ps`
   - Check `MONGO_URI` in environment

3. **Import errors**
   - Check application logs: `docker logs anthropic_app`
   - Verify ZIP file contains valid JSON

### Viewing Logs

```bash
# Application logs
docker logs anthropic_app

# Follow logs in real-time
docker logs -f anthropic_app

# With structured JSON logging
LOG_FORMAT=json docker compose up
```

## Security Notes

⚠️ **For production use**:

- Generate a secure `SECRET_KEY`
- Change default MongoDB passwords
- Use environment variables for all secrets
- Enable HTTPS with nginx reverse proxy
- Consider adding user authentication
- Run security scans: `bandit -r src/`

## Roadmap

- [ ] User authentication and multi-user support
- [ ] Elasticsearch integration for advanced search
- [ ] Scheduled automatic imports
- [ ] Analytics dashboard with charts
- [ ] Conversation tagging and categorization
- [ ] Batch operations UI
- [ ] Real-time updates with WebSockets

## Contributing

1. Fork the repository
2. Install pre-commit hooks: `pre-commit install`
3. Create a feature branch
4. Write tests for new functionality
5. Ensure all tests pass: `pytest`
6. Ensure code quality: `pre-commit run --all-files`
7. Submit a Pull Request

## License

MIT License - feel free to use for personal or commercial purposes.

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review logs for error details

---

Made with ❤️ for the Anthropic community
