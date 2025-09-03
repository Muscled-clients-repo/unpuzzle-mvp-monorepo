from django.contrib import admin
from .models import Enrollment, CourseReview

# Simple admin registrations
admin.site.register(Enrollment)
admin.site.register(CourseReview)
