FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required by psycopg (libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files (no DB needed, skip checks to avoid DB connectivity attempt)
RUN SECRET_KEY=dummy-build-key DEBUG=False python manage.py collectstatic --noinput --skip-checks

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "seriea_reference.wsgi:application"]