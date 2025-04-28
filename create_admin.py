#!/usr/bin/env python
"""
Standalone script to create an admin user.
Can be run directly: python create_admin.py
"""

import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction_site.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction

def create_admin():
    """Create a superuser for the admin panel"""
    username = 'admin'
    email = 'admin@example.com'
    password = 'Admin@123456'
    
    try:
        with transaction.atomic():
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username, email, password)
                print(f"Superuser '{username}' created successfully!")
            else:
                user = User.objects.get(username=username)
                user.is_staff = True
                user.is_superuser = True
                user.email = email
                user.set_password(password)
                user.save()
                print(f"Superuser '{username}' updated successfully!")
        return True
    except Exception as e:
        print(f"Error creating superuser: {e}")
        return False

if __name__ == "__main__":
    create_admin()
