from django.contrib import messages


def current_user_dict(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None
    return {
        "id": user.pk,
        "name": user.first_name or user.username,
        "email": user.email,
        "role": "admin" if user.is_staff else "student",
    }


def globals(request):
    """Names the old Flask templates expect."""
    from django.middleware.csrf import get_token

    def get_flashed_messages(with_categories=False):
        items = [(m.level_tag or "success", str(m)) for m in messages.get_messages(request)]
        return items if with_categories else [text for _, text in items]

    return {
        "current_user": current_user_dict(request),
        "csrf_token": lambda: get_token(request),
        "get_flashed_messages": get_flashed_messages,
    }
