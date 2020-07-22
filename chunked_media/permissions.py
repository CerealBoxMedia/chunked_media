from wagtail.core.permission_policies.collections import CollectionOwnershipPermissionPolicy

from knowledge_hub.chunked_media.models import Media, get_media_model

permission_policy = CollectionOwnershipPermissionPolicy(
    get_media_model(),
    auth_model=Media,
    owner_field_name='uploaded_by_user'
)
