"""One command that prepares everything: tables, admin account, event sections.

    python manage.py setup_portal
Safe to run on every start.
"""
import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from portal import accounts, events


class Command(BaseCommand):
    help = "Create database tables, the admin account and starter event sections."

    def handle(self, *args, **options):
        for alias in settings.DATABASES:
            call_command("migrate", database=alias, interactive=False, verbosity=0)
            self.stdout.write(f"Database ready: {alias}")

        email = os.environ.get("ADMIN_EMAIL", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        on_render = bool(os.environ.get("RENDER"))
        has_remote = bool(os.environ.get("DATABASE_URL"))

        if email and password:
            accounts.ensure_admin(email, password)
            self.stdout.write(f"Admin account ready: {email}")
        elif not on_render and not has_remote:
            accounts.ensure_admin(settings.DEV_ADMIN_EMAIL, settings.DEV_ADMIN_PASSWORD)
            self.stdout.write(
                f"Local admin: {settings.DEV_ADMIN_EMAIL} / {settings.DEV_ADMIN_PASSWORD}"
            )
        else:
            self.stdout.write("WARNING: set ADMIN_EMAIL and ADMIN_PASSWORD for the admin login.")

        events.seed_default_sections()
        self.stdout.write("Event sections ready.")
