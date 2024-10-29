-- Enable dblink extension
DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'dblink') THEN
      CREATE EXTENSION dblink;
   END IF;
END
$$;

-- Create user_db if it does not exist
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'user_db') THEN
      PERFORM dblink_exec('dbname=postgres', 'CREATE DATABASE user_db');
   END IF;
END
$$;

-- Create test_user_db if it does not exist
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test_user_db') THEN
      PERFORM dblink_exec('dbname=postgres', 'CREATE DATABASE test_user_db');
   END IF;
END
$$;

-- Create role qa if it does not exist
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'qa') THEN
      CREATE ROLE qa WITH LOGIN PASSWORD 'qa';
   END IF;
END
$$;

-- Grant privileges and set role properties
GRANT ALL PRIVILEGES ON DATABASE user_db TO qa;
GRANT ALL PRIVILEGES ON DATABASE test_user_db TO qa;
ALTER ROLE qa WITH CREATEDB;

-- Connect to user_db and create User table
\c user_db;
CREATE TABLE IF NOT EXISTS "User" (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL
);

-- Connect to test_user_db and create User table
\c test_user_db;
CREATE TABLE IF NOT EXISTS "User" (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL
);