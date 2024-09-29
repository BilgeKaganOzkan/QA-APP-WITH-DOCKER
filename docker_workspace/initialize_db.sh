#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Database connection parameters
DB_USER="qa"
DB_PASSWORD="qa"
DB_HOST="postgres"
DB_NAME="user_db"
TABLE_NAME="User"

# Wait for PostgreSQL to start
echo "Waiting for PostgreSQL to be available..."
until pg_isready -h "$DB_HOST" -U "$DB_USER"; do
  sleep 2
done

echo "PostgreSQL is available, proceeding with database initialization..."

# Create the database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$DB_USER" --host "$DB_HOST" <<-EOSQL
    DO \$\$ 
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$DB_NAME') THEN
            PERFORM dblink_exec('dbname=' || current_database(), 'CREATE DATABASE $DB_NAME');
        END IF;
    END
    \$\$;
EOSQL

# Connect to the database and create the User table if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$DB_USER" --host "$DB_HOST" --dbname="$DB_NAME" <<-EOSQL
    CREATE TABLE IF NOT EXISTS $TABLE_NAME (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL
    );
EOSQL

echo "Database and User table created successfully."
