from django.contrib import admin

from config.routers import student_alias
from .models import EventRegistration, EventSection, StudentRecord


class StudentDBAdmin(admin.ModelAdmin):
    """Django's admin site must read the student database for these models."""

    def get_queryset(self, request):
        return super().get_queryset(request).using(student_alias())

    def save_model(self, request, obj, form, change):
        obj.save(using=student_alias())

    def delete_model(self, request, obj):
        obj.delete(using=student_alias())


@admin.register(StudentRecord)
class StudentRecordAdmin(StudentDBAdmin):
    list_display = ("student_id", "student_name", "percentage", "attendance", "cgpa", "backlogs")
    search_fields = ("student_id", "student_name")


@admin.register(EventSection)
class EventSectionAdmin(StudentDBAdmin):
    list_display = ("event_name", "section_name")


@admin.register(EventRegistration)
class EventRegistrationAdmin(StudentDBAdmin):
    list_display = ("section", "user_name", "user_email", "created_at")
