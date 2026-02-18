#!/bin/bash

echo "========================================="
echo "Notification Service - Starting"
echo "========================================="

# Run database migrations (non-fatal: app can start without migrations)
echo "Running database migrations..."
if alembic upgrade head 2>&1; then
    echo "Migrations completed successfully"
else
    echo "WARNING: Migration failed - app will start without migrations"
fi

echo "Starting application..."
exec "$@"
