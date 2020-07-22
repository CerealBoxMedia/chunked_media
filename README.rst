Chunked Media
=====

chunked_media is a Wagtail app for uploading large media files. It is
Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "chunked_media" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'chunked_media',
    ]

2. Include the chunked_media URLconf in your project urls.py like this::

    path('chunked_media/', include('chunked_media.admin_urls')),

3. Run ``python manage.py migrate`` to create the chunked_media models.
