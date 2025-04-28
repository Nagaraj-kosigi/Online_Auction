from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

class Command(BaseCommand):
    help = 'Creates a superuser account'
    
    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Superuser username')
        parser.add_argument('--email', type=str, default='admin@example.com', help='Superuser email')
        parser.add_argument('--password', type=str, default='admin123', help='Superuser password')
    
    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        try:
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully'))
            else:
                self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists'))
        except IntegrityError:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: username or email already exists'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))
