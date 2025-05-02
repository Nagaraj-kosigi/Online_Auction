from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

class MediaStorage(FileSystemStorage):
    """
    Custom storage for media files that ensures directories exist
    and handles file paths correctly.
    """
    def __init__(self, *args, **kwargs):
        # Set location to MEDIA_ROOT if not provided
        if 'location' not in kwargs:
            kwargs['location'] = settings.MEDIA_ROOT

        # Set base_url to MEDIA_URL if not provided
        if 'base_url' not in kwargs:
            kwargs['base_url'] = settings.MEDIA_URL

        # Ensure the media directory exists
        location = kwargs['location']
        os.makedirs(location, exist_ok=True)

        # Create subdirectories for different types of uploads
        os.makedirs(os.path.join(location, 'auction_images'), exist_ok=True)
        os.makedirs(os.path.join(location, 'profile_images'), exist_ok=True)

        # Initialize the parent class
        super().__init__(*args, **kwargs)

    def url(self, name):
        """
        Return the URL where the file can be accessed.
        """
        if not name:
            return ''

        # Get the URL from the parent class
        url = super().url(name)

        # Log the URL for debugging
        logger.debug(f"Generated URL for {name}: {url}")

        return url
