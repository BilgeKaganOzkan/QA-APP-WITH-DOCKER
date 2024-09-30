DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'user_db') THEN
      PERFORM dblink_exec('dbname=postgres', 'CREATE DATABASE user_db');
   END IF;
END
$do$;

DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'qa') THEN
      CREATE ROLE qa WITH LOGIN PASSWORD 'qa';
   END IF;
END
$do$;

GRANT ALL PRIVILEGES ON DATABASE user_db TO qa;
ALTER ROLE qa WITH CREATEDB;

\c user_db;

CREATE TABLE IF NOT EXISTS "User" (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL
);
