#!/bin/bash
set -e

echo "========================================="
echo "Auth Service - Starting"
echo "========================================="

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Migrations completed successfully"
else
    echo "✗ Migration failed"
    exit 1
fi

echo "Starting application..."
exec "$@"
