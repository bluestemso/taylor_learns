#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load configuration from .kamal/secrets
SECRETS_FILE=".kamal/secrets"

if [ ! -f "$SECRETS_FILE" ]; then
  echo -e "${RED}Error: Could not find $SECRETS_FILE${NC}"
  echo "Please ensure the .kamal/secrets file exists with the required configuration."
  exit 1
fi

# Parse only the specific variables we need from the secrets file
# This avoids issues with special characters in other variables
PROD_SSH_HOST=$(grep '^PROD_SSH_HOST=' "$SECRETS_FILE" | cut -d '=' -f2)
PROD_SSH_USER=$(grep '^PROD_SSH_USER=' "$SECRETS_FILE" | cut -d '=' -f2)
DATABASE_URL=$(grep '^DATABASE_URL=' "$SECRETS_FILE" | cut -d '=' -f2-)

# Validate required configuration
if [ -z "${PROD_SSH_HOST:-}" ] || [ -z "${PROD_SSH_USER:-}" ] || [ -z "${DATABASE_URL:-}" ]; then
  echo -e "${RED}Error: Missing required configuration in $SECRETS_FILE${NC}"
  echo ""
  echo "Please ensure the following variables are set in $SECRETS_FILE:"
  echo "  PROD_SSH_HOST - SSH hostname"
  echo "  PROD_SSH_USER - SSH username"
  echo "  DATABASE_URL - Production database URL"
  exit 1
fi

# Parse DATABASE_URL to extract connection details
# Format: postgres://user:password@host:port/database
DB_URL_NO_PROTO=${DATABASE_URL#postgres://}
DB_USER_PASS=${DB_URL_NO_PROTO%%@*}
DB_HOST_PORT_DB=${DB_URL_NO_PROTO#*@}

PROD_DB_USER=${DB_USER_PASS%%:*}
PROD_DB_PASSWORD=${DB_USER_PASS#*:}

DB_HOST_PORT=${DB_HOST_PORT_DB%%/*}
PROD_DB_NAME=${DB_HOST_PORT_DB#*/}

PROD_DB_HOST=${DB_HOST_PORT%%:*}
PROD_DB_PORT=${DB_HOST_PORT#*:}

# Local database configuration (from docker-compose.yml)
LOCAL_DB_NAME="taylor_learns"
LOCAL_DB_USER="postgres"
LOCAL_DB_PASSWORD="postgres"
LOCAL_DB_HOST="localhost"
LOCAL_DB_PORT="5432"

# Temporary file for database dump
DUMP_FILE="prod_db_dump_$(date +%Y%m%d_%H%M%S).sql"
REMOTE_DUMP_PATH="/tmp/${DUMP_FILE}"
LOCAL_DUMP_PATH="./backups/${DUMP_FILE}"

echo -e "${YELLOW}=== Production Database Sync ===${NC}"
echo ""
echo "This will:"
echo "  1. Create a dump of your production database"
echo "  2. Download it to your local machine"
echo "  3. DROP your local database and recreate it"
echo "  4. Import the production data"
echo ""
echo -e "${RED}WARNING: This will DESTROY all data in your local database!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

# Create backups directory if it doesn't exist
mkdir -p ./backups

# Set up SSH connection multiplexing to reuse a single connection
SSH_CONTROL_PATH="/tmp/ssh-sync-prod-db-$$"
SSH_OPTS="-o ControlMaster=auto -o ControlPath=${SSH_CONTROL_PATH} -o ControlPersist=300"

echo ""
echo -e "${GREEN}[1/5] Creating dump on production server...${NC}"
# Run pg_dump inside the database container using docker exec
ssh ${SSH_OPTS} "${PROD_SSH_USER}@${PROD_SSH_HOST}" "docker exec ${PROD_DB_HOST} pg_dump -U ${PROD_DB_USER} -Fc ${PROD_DB_NAME} > ${REMOTE_DUMP_PATH}"

echo -e "${GREEN}[2/5] Downloading dump from production...${NC}"
scp ${SSH_OPTS} "${PROD_SSH_USER}@${PROD_SSH_HOST}:${REMOTE_DUMP_PATH}" "${LOCAL_DUMP_PATH}"

echo -e "${GREEN}[3/5] Cleaning up remote dump file...${NC}"
ssh ${SSH_OPTS} "${PROD_SSH_USER}@${PROD_SSH_HOST}" "rm ${REMOTE_DUMP_PATH}"

# Close the SSH connection
ssh -O exit -S "${SSH_CONTROL_PATH}" "${PROD_SSH_USER}@${PROD_SSH_HOST}" 2>/dev/null || true

echo -e "${GREEN}[4/5] Dropping and recreating local database...${NC}"
# First, terminate all connections to the database
docker compose exec -T db psql -U ${LOCAL_DB_USER} postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${LOCAL_DB_NAME}' AND pid <> pg_backend_pid();"

# Drop and recreate the database
docker compose exec -T db psql -U ${LOCAL_DB_USER} postgres -c "DROP DATABASE IF EXISTS ${LOCAL_DB_NAME};"
docker compose exec -T db psql -U ${LOCAL_DB_USER} postgres -c "CREATE DATABASE ${LOCAL_DB_NAME};"

echo -e "${GREEN}[5/5] Restoring production data to local database...${NC}"
# Capture pg_restore output and only show if there's an error
RESTORE_OUTPUT=$(docker compose exec -T db pg_restore -U ${LOCAL_DB_USER} -d ${LOCAL_DB_NAME} --no-owner --role=${LOCAL_DB_USER} < "${LOCAL_DUMP_PATH}" 2>&1)
RESTORE_EXIT_CODE=$?

if [ $RESTORE_EXIT_CODE -ne 0 ]; then
  echo -e "${RED}Error during restore:${NC}"
  echo "$RESTORE_OUTPUT"
  exit 1
fi

# Get some summary stats
echo ""
echo -e "${GREEN}✓ Database sync complete!${NC}"
echo ""
echo "Backup saved to: ${LOCAL_DUMP_PATH}"
echo ""

# Show summary statistics
echo -e "${GREEN}Summary:${NC}"
PAGE_COUNT=$(docker compose exec -T db psql -U ${LOCAL_DB_USER} -d ${LOCAL_DB_NAME} -tAc "SELECT COUNT(*) FROM wagtailcore_page WHERE live = true;")
TOTAL_PAGES=$(docker compose exec -T db psql -U ${LOCAL_DB_USER} -d ${LOCAL_DB_NAME} -tAc "SELECT COUNT(*) FROM wagtailcore_page;")
LATEST_PAGE=$(docker compose exec -T db psql -U ${LOCAL_DB_USER} -d ${LOCAL_DB_NAME} -tAc "SELECT title || ' (' || TO_CHAR(first_published_at, 'YYYY-MM-DD') || ')' FROM wagtailcore_page WHERE first_published_at IS NOT NULL ORDER BY first_published_at DESC LIMIT 1;")

echo "  - Total pages: ${TOTAL_PAGES} (${PAGE_COUNT} published)"
if [ -n "$LATEST_PAGE" ]; then
  echo "  - Most recent: ${LATEST_PAGE}"
fi

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  - Run migrations if your local code is ahead: make migrate"
echo "  - Create a superuser if needed: make manage ARGS='createsuperuser'"
