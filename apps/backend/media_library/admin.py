from django.contrib import admin
from .models import MediaFile, UploadSession

# Simple admin registrations
admin.site.register(MediaFile)
admin.site.register(UploadSession)
