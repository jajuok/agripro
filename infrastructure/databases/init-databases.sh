#!/bin/bash
set -e

echo "Creating AgriScheme databases..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create all service databases
    CREATE DATABASE agrischeme_auth;
    CREATE DATABASE agrischeme_farmer;
    CREATE DATABASE agrischeme_farm;
    CREATE DATABASE agrischeme_financial;
    CREATE DATABASE agrischeme_gis;
    CREATE DATABASE agrischeme_market;
    CREATE DATABASE agrischeme_ai;
    CREATE DATABASE agrischeme_iot;
    CREATE DATABASE agrischeme_livestock;
    CREATE DATABASE agrischeme_task;
    CREATE DATABASE agrischeme_inventory;
    CREATE DATABASE agrischeme_notification;
    CREATE DATABASE agrischeme_traceability;
    CREATE DATABASE agrischeme_compliance;
    CREATE DATABASE agrischeme_integration;

    -- Grant all privileges
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_auth TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_farmer TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_farm TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_financial TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_gis TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_market TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_ai TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_iot TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_livestock TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_task TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_inventory TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_notification TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_traceability TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_compliance TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE agrischeme_integration TO $POSTGRES_USER;
EOSQL

echo "✓ All 15 databases created successfully"
