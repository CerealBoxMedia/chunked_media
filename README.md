A package to upload large media files through Wagtail.
Built on top of WagtailMedia

Whilst the standard set up for handling media files within Django systems usually relies on a third party 
systems such as s3 buckets for hosting and/or a CDN layer for the upload, something this is not possible.
If you need to upload and host large media files directly within the platform to a standard directory or EFS 
service (elastic file system) for stakeholder reasons, security (no outside POST or GET requests to other services),
or authorisation purposes.