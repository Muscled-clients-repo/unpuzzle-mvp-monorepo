FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=app.settings
ENV PORT=8000

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        libmagic1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements/production.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r production.txt

# Copy project
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Switch to non-root user
USER appuser

# Heroku uses PORT environment variable
EXPOSE $PORT

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && gunicorn app.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --worker-class gthread --log-file - --access-logfile - --error-logfile -"]