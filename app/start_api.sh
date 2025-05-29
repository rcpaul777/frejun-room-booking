#! /bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Initialize the database
echo "Initializing database..."
python init_db.py

# Start the application
echo "Starting FastAPI application..."
uvicorn main:app --host 0.0.0.0 --port 8000
