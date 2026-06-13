FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/app.py .
COPY src/models.py .
COPY src/config.py .
COPY src/templates ./templates

# Create non-root runtime user and upload directory
RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /app/uploads \
    && chown -R app:app /app

USER app

# Expose port
EXPOSE 5000

# Run the application with a production WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "app:app"]
