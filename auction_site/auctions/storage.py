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
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        super().__init__(*args, **kwargs)
    
    def url(self, name):
        """
        Return the URL where the file can be accessed.
        """
        url = super().url(name)
        return url
