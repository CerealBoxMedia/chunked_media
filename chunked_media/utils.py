import os
from django.conf import settings
from wagtail import VERSION as WAGTAIL_VERSION

if WAGTAIL_VERSION < (2, 5):
    from wagtail.utils.pagination import paginate
else:
    from django.core.paginator import Paginator

    DEFAULT_PAGE_KEY = 'p'

    def paginate(request, items, page_key=DEFAULT_PAGE_KEY, per_page=20):
        paginator = Paginator(items, per_page)
        page = paginator.get_page(request.GET.get(page_key))
        return paginator, page


def upload_path(title):
    from django.utils import timezone
    timestamp_now = timezone.now()
    media_upload_path = os.path.join(settings.MEDIA_ROOT, f'chunked_media/{timestamp_now}-{title}')
    if not os.path.exists(media_upload_path):
        try:
            return os.mkdir(os.path.join(settings.MEDIA_ROOT, f'chunked_media/{timestamp_now}-{title}'))
        except:
            media_upload_path = settings.MEDIA_ROOT
            return media_upload_path
    else:
        return media_upload_path


def chunk_uploaded_file(file, filename, chunk_upload_path):
    # the property that constructs filename attribute should return extension too
    if not chunk_upload_path:
        # Lazy way to handle upload_path returning None.
        chunk_upload_path = settings.MEDIA_ROOT
    file_destination = os.path.join(chunk_upload_path, filename)
    with open(file_destination, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return file_destination


# def save_final_media_to_model(file_destination):
#     from chunked_media.models import Media
#     if os.path.isfile(file_destination):
#         # TODO: get this method working (save() is not an attribute we can use here as not part of MediaQuerySet)
#         # TODO: Add some logic for the url() property in Models as it currently has None whilst the chunk happens and that is a problem
#         Media.objects.create()
#         try:
#             for root, dirs, file in os.walk(file_destination, topdown=False):
#                 # Using list indexing here as there should only be one file and one parent dir
#                 os.remove(file[0])
#                 os.rmdir(dirs[0])
#         except Exception as e:
#             print(f'Could not remove file due to {e}')
#
#     else:
#         f"Error: Media object could not be saved. {os.path.basename(file_destination)} does not exist"