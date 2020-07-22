from django.conf import settings
from django.contrib import admin

from chunked_media.models import Media

if hasattr(settings, 'CHUNKED_MEDIA_MODEL') and settings.CHUNKED_MEDIA_MODEL != 'chunked_media.Media':
    # This installation provides its own custom media class;
    # to avoid confusion, we won't expose the unused chunked_media.Media class
    # in the admin.
    pass
else:
    admin.site.register(Media)
