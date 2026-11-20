from django.conf import settings


def student_alias():
    return "student_data" if "student_data" in settings.DATABASES else "default"


class PortalRouter:
    """Marks / events tables -> student database. Logins -> users database."""

    def _is_portal(self, model):
        return model._meta.app_label == "portal"

    def db_for_read(self, model, **hints):
        return student_alias() if self._is_portal(model) else "default"

    db_for_write = db_for_read

    def allow_relation(self, a, b, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "portal":
            return db == student_alias()
        return db == "default"
