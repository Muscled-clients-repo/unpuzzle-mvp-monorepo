from django.contrib import admin
from .models import CourseCategory, Course, CourseSection

# Simple admin registrations
admin.site.register(CourseCategory)
admin.site.register(Course)
admin.site.register(CourseSection)
