#!/bin/sh

set -eu

echo 'Waiting for Postgres...'
until pg_isready -h postgres -U "$POSTGRES_USER" > /dev/null 2>&1; do
  sleep 2
done

echo 'Connected to Postgres.'

echo 'Creating airflow DB user...'
PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U "$POSTGRES_USER" <<EOSQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$AIRFLOW_DB_USER') THEN
    CREATE USER $AIRFLOW_DB_USER WITH PASSWORD '$AIRFLOW_DB_PASSWORD';
  END IF;
END
\$\$;
EOSQL

echo "Changing ownership of database '$POSTGRES_DB' to user '$AIRFLOW_DB_USER'..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U "$POSTGRES_USER" -c "ALTER DATABASE $POSTGRES_DB OWNER TO $AIRFLOW_DB_USER;"

PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U "$POSTGRES_USER" <<EOSQL
GRANT CONNECT ON DATABASE $POSTGRES_DB TO $AIRFLOW_DB_USER;
GRANT USAGE ON SCHEMA public TO $AIRFLOW_DB_USER;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $AIRFLOW_DB_USER;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $AIRFLOW_DB_USER;
EOSQL

echo 'Creating footgraph DB user...'
PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U "$POSTGRES_USER" <<EOSQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$FOOTGRAPH_DB_USER') THEN
    CREATE USER $FOOTGRAPH_DB_USER WITH PASSWORD '$FOOTGRAPH_DB_PASSWORD';
  END IF;
END
\$\$;
EOSQL

echo "Checking for existence of database '$FOOTGRAPH_DB'..."
EXISTS=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname = '$FOOTGRAPH_DB'")

if [ "$EXISTS" != "1" ]; then
  echo "Creating database '$FOOTGRAPH_DB' owned by '$FOOTGRAPH_DB_USER'..."
  PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U "$POSTGRES_USER" -c "CREATE DATABASE $FOOTGRAPH_DB OWNER $FOOTGRAPH_DB_USER"
else
  echo "Database '$FOOTGRAPH_DB' already exists."
fi

echo "Creating table in '$FOOTGRAPH_DB' as user '$FOOTGRAPH_DB_USER'..."
PGPASSWORD=$FOOTGRAPH_DB_PASSWORD psql -h postgres -U "$FOOTGRAPH_DB_USER" -d "$FOOTGRAPH_DB" <<EOSQL
CREATE TABLE IF NOT EXISTS requests (
  id SERIAL PRIMARY KEY,
  url TEXT NOT NULL,
  params JSONB,
  payload JSONB,
  metadata JSONB,
  created_at TIMESTAMP NOT NULL,
  created_by TEXT NOT NULL,
  updated_at TIMESTAMP,
  status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'Succeeded', 'Failed'))
);
EOSQL

echo 'DB initialization complete.'
