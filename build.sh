#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r Requirements.txt

# Navigate to the Django project directory
cd auction_site

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
