#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r Requirements.txt

# Navigate to the Django project directory
cd auction_site

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations - use --fake if needed
python manage.py migrate --noinput || python manage.py migrate --noinput --fake

# Create superuser using a more reliable approach
echo "Creating admin superuser..."
python manage.py shell -c "
from django.contrib.auth.models import User
from django.db import transaction

try:
    with transaction.atomic():
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'Admin@123456')
            print('Superuser created successfully.')
        else:
            # Update password for existing admin user
            admin = User.objects.get(username='admin')
            admin.set_password('Admin@123456')
            admin.save()
            print('Admin password updated.')
except Exception as e:
    print(f'Error creating superuser: {e}')
    # Try alternative method
    try:
        from django.contrib.auth.hashers import make_password
        User.objects.filter(username='admin').update(
            is_staff=True,
            is_superuser=True,
            password=make_password('Admin@123456')
        )
        print('Admin user updated using alternative method.')
    except Exception as e2:
        print(f'Alternative method failed: {e2}')
"
