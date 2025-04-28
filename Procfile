web: cd auction_site && python manage.py migrate --noinput || python manage.py migrate --noinput --fake && gunicorn auction_site.wsgi:application
