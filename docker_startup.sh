#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

PORT=${PORT:-8000}

# Wait for database to be ready
echo "Waiting for database to be ready..."
python << END
import sys
import time
import psycopg2
from urllib.parse import urlparse
import os

# Parse DATABASE_URL
db_url = os.environ.get('DATABASE_URL', '')
result = urlparse(db_url)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        conn = psycopg2.connect(
            dbname=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        conn.close()
        print("Database is ready!")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        attempt += 1
        print(f"Database not ready yet (attempt {attempt}/{max_attempts}): {e}")
        time.sleep(2)

print("Could not connect to database after 30 attempts")
sys.exit(1)
END

echo "Django migrate"
python manage.py migrate --noinput
echo "Run Gunicorn"
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 taylor_learns.asgi:application -k uvicorn.workers.UvicornWorker
