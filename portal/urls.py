from django.urls import path

from . import views



urlpatterns = [
    path("", views.index, name="index"),
    path("students-information", views.students_information, name="students_information"),
    path("academic-analysis", views.academic_analysis, name="academic_analysis"),
    path("statistics", views.statistics, name="statistics"),
    path("correlation", views.correlation, name="correlation"),
    path("prediction", views.prediction, name="prediction"),
    path("add-student", views.add_student_page, name="add_student_page"),
    path("api/data", views.api_data, name="api_data"),
    path("api/summary", views.api_summary, name="api_summary"),
    path("api/statistics", views.api_statistics, name="api_statistics"),
    path("api/correlation", views.api_correlation, name="api_correlation"),
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path("logout", views.logout, name="logout"),
    path("healthz", views.healthz, name="healthz"),
    path("student", views.student_dashboard, name="student_dashboard"),
    path("student/marks", views.student_submit, name="student_submit"),
    path("student/events", views.student_events, name="student_events"),
    path("student/events/<int:section_id>/join", views.student_join, name="student_join"),
    path("student/events/<int:section_id>/leave", views.student_leave, name="student_leave"),
    path("admin/submissions", views.admin_submissions, name="admin_submissions"),
    path("admin/records/<str:student_id>/delete", views.admin_delete_record, name="admin_delete_record"),
    path("admin/export.csv", views.admin_export, name="admin_export"),
    path("admin/events", views.admin_events, name="admin_events"),
    path("admin/events/add", views.admin_event_add, name="admin_event_add"),
    path("admin/events/<int:section_id>", views.admin_event_detail, name="admin_event_detail"),
    path("admin/events/<int:section_id>/delete", views.admin_event_delete, name="admin_event_delete"),
]
