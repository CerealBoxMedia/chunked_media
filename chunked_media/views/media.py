from __future__ import unicode_literals
import os

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from django.core.files import File

from wagtail import VERSION as WAGTAIL_VERSION
from wagtail.admin import messages
from wagtail.core.models import Collection
from wagtail.search.backends import get_search_backends

from .forms import get_media_form
from .models import get_media_model
from .permissions import permission_policy
from .utils import paginate, chunk_uploaded_file, upload_path

if WAGTAIL_VERSION < (2, 5):
    from wagtail.admin.forms import SearchForm
else:
    from wagtail.admin.forms.search import SearchForm

if WAGTAIL_VERSION < (2, 9):
    from wagtail.admin.utils import PermissionPolicyChecker, permission_denied, popular_tags_for_model
else:
    from wagtail.admin.auth import PermissionPolicyChecker, permission_denied
    from wagtail.admin.models import popular_tags_for_model


permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    Media = get_media_model()

    # Get media files (filtered by user permission)
    media = permission_policy.instances_user_has_any_permission_for(
        request.user, ['change', 'delete']
    )

    # Ordering
    if 'ordering' in request.GET and request.GET['ordering'] in ['title', '-created_at']:
        ordering = request.GET['ordering']
    else:
        ordering = '-created_at'
    media = media.order_by(ordering)

    # Filter by collection
    current_collection = None
    collection_id = request.GET.get('collection_id')
    if collection_id:
        try:
            current_collection = Collection.objects.get(id=collection_id)
            media = media.filter(collection=current_collection)
        except (ValueError, Collection.DoesNotExist):
            pass

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search media files"))
        if form.is_valid():
            query_string = form.cleaned_data['q']
            media = media.search(query_string)
    else:
        form = SearchForm(placeholder=_("Search media"))

    # Pagination
    paginator, media = paginate(request, media)

    collections = permission_policy.collections_user_has_any_permission_for(
        request.user, ['add', 'change']
    )
    if len(collections) < 2:
        collections = None

    # Create response
    if request.is_ajax():
        return render(request, 'chunked_media/media/results.html', {
            'ordering': ordering,
            'media_files': media,
            'query_string': query_string,
            'is_searching': bool(query_string),
        })
    else:
        return render(request, 'chunked_media/media/index.html', {
            'ordering': ordering,
            'media_files': media,
            'query_string': query_string,
            'is_searching': bool(query_string),

            'search_form': form,
            'popular_tags': popular_tags_for_model(Media),
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
            'collections': collections,
            'current_collection': current_collection,
        })


@permission_checker.require('add')
def add(request, media_type):
    Media = get_media_model()
    MediaForm = get_media_form(Media)

    if request.POST:
        media = Media(uploaded_by_user=request.user, type=media_type)
        form = MediaForm(request.POST, request.FILES, instance=media, user=request.user)
        if form.is_valid():
            try:
                messages.info(request, _(f"'{media.title.capitalize()}' is being processed"))
                chunk_upload_path = upload_path(media.title)
                messages.info(request, _(f"chunk_upload_path = '{chunk_upload_path}'"))
                uploaded_file = chunk_uploaded_file(request.FILES['file'], media.filename, chunk_upload_path)
                print(f'after uploaded file. uploaded_file Var is {uploaded_file}')
                # May need to make the chunk uploaded file method save into an intermediary model for this to work
                form.instance.file = File(uploaded_file, os.path.basename(uploaded_file.path))
                print('after form.instance.file. Above form.save. About to form.save()')
                form.save()
                print('form saved!')
                # Ensure the uploaded_file is closed because calling save() will open the file and read its content.
                uploaded_file.close()
                uploaded_file.delete()

                # Reindex the media entry to make sure all tags are indexed
                for backend in get_search_backends():
                    backend.add(media)

                messages.success(request, _(f"'{media.title.capitalize()}' successfully uploaded!."), buttons=[
                    messages.button(reverse('chunked_media:index'), _('Index'))
                ])
                return redirect('chunked_media:index')
            except Exception as e:
                messages.error(request, _(f"{media.title} could not be saved due to: {e}."))
        else:
            messages.error(request, _("The media file could not be saved due to errors."))
    else:
        media = Media(uploaded_by_user=request.user, type=media_type)
        form = MediaForm(user=request.user, instance=media)

    return render(request, "chunked_media/media/add.html", {
        'form': form,
        'media_type': media_type,
    })


@permission_checker.require('change')
def edit(request, media_id):
    Media = get_media_model()
    MediaForm = get_media_form(Media)

    media = get_object_or_404(Media, id=media_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', media):
        return permission_denied(request)

    if request.POST:
        original_file = media.file
        form = MediaForm(request.POST, request.FILES, instance=media, user=request.user)
        if form.is_valid():
            if 'file' in form.changed_data:
                # if providing a new media file, delete the old one.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
            messages.info(request, _(f"'{media.title.capitalize()}' is being processed"))
            chunk_upload_path = upload_path(media.title)
            uploaded_file = chunk_uploaded_file(request.FILES['file'], media.filename, chunk_upload_path)
            # May need to make the chunk uploaded file method save into an intermediary model for this to work
            form.instance.file = File(uploaded_file, os.path.basename(uploaded_file.path))
            form.save()
            # Ensure the uploaded_file is closed because calling save() will open the file and read its content.
            uploaded_file.close()
            uploaded_file.delete()

            # media = save_final_media_to_model(chunk_uploaded_file(request.FILES['file'],
            #                                                       media.filename,
            #                                                       chunk_upload_path))

            # Reindex the media entry to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(media)

            messages.success(request, _(f"{media.title.capitalize()} updated"), buttons=[
                messages.button(reverse('chunked_media:edit', args=(media.id,)), _('Edit'))
            ])
            return redirect('chunked_media:index')
        else:
            messages.error(request, _("The media could not be saved due to errors."))
    else:
        form = MediaForm(instance=media, user=request.user)

    filesize = None

    # Get file size when there is a file associated with the Media object
    if media.file:
        try:
            filesize = media.file.size
        except OSError:
            # File doesn't exist
            pass

    if not filesize:
        messages.error(
            request,
            _("The file could not be found. Please change the source or delete the media file"),
            buttons=[messages.button(reverse('chunked_media:delete', args=(media.id,)), _('Delete'))]
        )

    return render(request, "chunked_media/media/edit.html", {
        'media': media,
        'filesize': filesize,
        'form': form,
        'user_can_delete': permission_policy.user_has_permission_for_instance(
            request.user, 'delete', media
        ),
    })


@permission_checker.require('delete')
def delete(request, media_id):
    Media = get_media_model()
    media = get_object_or_404(Media, id=media_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', media):
        return permission_denied(request)

    if request.POST:
        media.delete()
        messages.success(request, _(f"{media.title.capitalize()} deleted."))
        return redirect('chunked_media:index')

    return render(request, "chunked_media/media/confirm_delete.html", {
        'media': media,
    })


def usage(request, media_id):
    Media = get_media_model()
    media = get_object_or_404(Media, id=media_id)

    paginator, used_by = paginate(request, media.get_usage())

    return render(request, "chunked_media/media/usage.html", {
        'media': media,
        'used_by': used_by
    })
