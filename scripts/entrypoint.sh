#!/bin/sh
set -e

# Wait for Postgres to become available.
echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Perform migrations
echo "Running migrations"
poetry run prisma migrate dev --name updates

# Populate the database
echo "Populating database"
./run populate-db

# Start the application
echo "Starting server"
exec ./run serve
