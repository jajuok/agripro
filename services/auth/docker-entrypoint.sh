#!/bin/bash
set +e  # Don't exit on error, we'll handle it

echo "========================================="
echo "Auth Service - Starting"
echo "========================================="

# Run database migrations
echo "Running database migrations..."

# Capture both output and exit code
alembic upgrade head 2>&1 | tee /tmp/migration.log
MIGRATION_EXIT=$?

# Check if migration output contains "already exists" error
if grep -q "already exists" /tmp/migration.log; then
    echo ""
    echo "⚠  Tables already exist - stamping database with current version..."

    # Get the current head revision
    CURRENT_HEAD=$(alembic heads | grep -oE '^[a-z0-9]+' | head -1)

    if [ -n "$CURRENT_HEAD" ]; then
        echo "Stamping database with revision: $CURRENT_HEAD"
        alembic stamp head

        if [ $? -eq 0 ]; then
            echo "✓ Database stamped successfully"
            echo "✓ Migration tracking fixed"
        else
            echo "✗ Failed to stamp database"
            exit 1
        fi
    else
        echo "✗ Could not determine current migration head"
        exit 1
    fi
elif [ $MIGRATION_EXIT -ne 0 ]; then
    # Migration failed with a different error
    echo "✗ Migration failed with unexpected error (exit code: $MIGRATION_EXIT)"
    cat /tmp/migration.log
    exit 1
else
    # Migration succeeded normally
    echo "✓ Migrations completed successfully"
fi

echo "Starting application..."
exec "$@"
