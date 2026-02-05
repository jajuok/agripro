#!/bin/bash
set -e

echo "========================================="
echo "Auth Service - Starting"
echo "========================================="

# Run database migrations
echo "Running database migrations..."

# Try to run migrations
if alembic upgrade head 2>&1 | tee /tmp/migration.log; then
    echo "✓ Migrations completed successfully"
else
    EXIT_CODE=$?

    # Check if the error is "table already exists"
    if grep -q "already exists" /tmp/migration.log; then
        echo "⚠ Tables already exist - stamping database with current version..."

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
    else
        echo "✗ Migration failed with unexpected error"
        cat /tmp/migration.log
        exit $EXIT_CODE
    fi
fi

echo "Starting application..."
exec "$@"
