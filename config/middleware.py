"""Who may open which page (admin vs student vs not logged in)."""
from django.http import JsonResponse
from django.shortcuts import redirect

PUBLIC = {"login", "register", "healthz"}
STUDENT_ENDPOINTS = {
    "student_dashboard", "student_submit", "student_events",
    "student_join", "student_leave", "logout",
}


class RoleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Django's own admin site has its own login (staff only)
        if request.path.startswith("/django-admin/"):
            return None
        match = request.resolver_match
        endpoint = match.url_name if match else None
        request.endpoint = endpoint
        if endpoint is None:
            return None

        from portal.views import render_error  # local import avoids a cycle

        user = request.user
        if endpoint in PUBLIC:
            if user.is_authenticated and endpoint in ("login", "register"):
                return redirect("index" if user.is_staff else "student_dashboard")
            return None

        if not user.is_authenticated:
            if request.path.startswith("/api/"):
                return JsonResponse({"error": "Please log in first."}, status=401)
            return redirect("login")

        if not user.is_staff:                       # ---- student ----
            if endpoint in STUDENT_ENDPOINTS:
                return None
            if request.path.startswith("/api/"):
                return JsonResponse({"error": "Administrators only."}, status=403)
            if endpoint == "index":
                return redirect("student_dashboard")
            return render_error(request, 403, "This page is only for administrators.")

        if endpoint in STUDENT_ENDPOINTS and endpoint != "logout":   # ---- admin ----
            return redirect("index")
        return None

    def process_template_response(self, request, response):
        return response


def add_headers(response):
    response["Cache-Control"] = "no-store"
    return response
