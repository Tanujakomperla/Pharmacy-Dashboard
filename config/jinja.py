"""Lets the Jinja2 templates written for Flask run unchanged on Django."""
import os
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.middleware.csrf import get_token
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def url_for(endpoint, **kwargs):
    if endpoint == "static":
        return static(kwargs["filename"])
    return reverse(endpoint, kwargs=kwargs or None)


def format_datetime(value):
    if not value:
        return "-"
    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(value[:19])
        value = value.replace(tzinfo=None) + timedelta(minutes=settings.DISPLAY_TZ_OFFSET_MINUTES)
        return value.strftime("%d %b %Y, %H:%M")
    except (ValueError, TypeError):
        return str(value)[:16]


def environment(**options):
    env = Environment(**options)
    env.globals.update(url_for=url_for, static=static, config=settings)
    env.filters["dt"] = format_datetime
    return env
