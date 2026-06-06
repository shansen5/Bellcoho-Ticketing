#!/bin/bash
# Run from your local machine each time you want to push changes.
set -euo pipefail

SERVER="root@159.223.153.249"
APP_DIR="/var/www/ticketing2"

echo "==> Syncing files to $SERVER..."
rsync -az --delete \
    --exclude='venv/' \
    --exclude='instance/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='residents_data.py' \
    --exclude='2025-Dec Member Directory.pdf' \
    --exclude='TicketingRequirements.odt' \
    --exclude='buildings.sql' \
    --exclude='CLAUDE.md' \
    --exclude='server_setup.sh' \
    --exclude='deploy.sh' \
    ./ "$SERVER:$APP_DIR/"

echo "==> Installing/updating Python dependencies..."
ssh "$SERVER" "cd $APP_DIR && venv/bin/pip install -q -r requirements.txt"

echo "==> Restarting app service..."
ssh "$SERVER" "systemctl restart ticketing2"

echo ""
echo "Deployed. App is at http://159.223.153.249"
