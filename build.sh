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

# Create superuser (will not fail if user exists)
echo "Creating admin superuser..."
python -c "
import django
django.setup()
from django.contrib.auth.models import User
username = 'admin'
email = 'admin@example.com'
password = 'Admin@123456'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print('Superuser created.')
else:
    print('Superuser already exists.')
"
