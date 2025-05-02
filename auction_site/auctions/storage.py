from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

class MediaStorage(FileSystemStorage):
    """
    Custom storage for media files that ensures directories exist
    and handles file paths correctly.
    """
    def __init__(self, *args, **kwargs):
        # Ensure the media directory exists
        location = kwargs.get('location', settings.MEDIA_ROOT)
        os.makedirs(location, exist_ok=True)

        # Create subdirectories for different types of uploads
        os.makedirs(os.path.join(location, 'auction_images'), exist_ok=True)
        os.makedirs(os.path.join(location, 'profile_images'), exist_ok=True)
        os.makedirs(os.path.join(location, 'fraud_evidence'), exist_ok=True)

        super().__init__(*args, **kwargs)

    def url(self, name):
        """
        Return the URL where the file can be accessed.
        """
        url = super().url(name)

        # Handle the case where the URL might be incorrect in production
        if settings.DEBUG:
            return url

        # For production, ensure the URL is correct
        # This helps with Render and similar platforms
        if not url.startswith('/media/'):
            url = f'/media/{name}'

        return url
