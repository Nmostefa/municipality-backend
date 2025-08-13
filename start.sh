#!/bin/bash
# Apply database migrations
echo "Applying database migrations..."
python -m flask db upgrade

# Start the Flask application with Gunicorn
echo "Starting Flask application with Gunicorn..."
exec gunicorn -b 0.0.0.0:$PORT app:app --timeout 120 --workers 4 --threads 2
