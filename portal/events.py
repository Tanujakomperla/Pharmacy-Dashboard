"""Pharmacy Week events: the admin creates sections, students join them."""
from django.db import IntegrityError, transaction
from django.db.models import Count

from config.routers import student_alias
from .models import EventRegistration, EventSection

DEFAULT_EVENT = "Pharmacy Week"
DEFAULT_SECTIONS = [
    ("Quiz", "Pharmacy and healthcare knowledge quiz."),
    ("Poster Presentation", "Present a poster on any pharmacy topic."),
    ("Model Making", "Build a working or display model."),
    ("Debate", "Debate on current issues in pharmacy practice."),
    ("Health Awareness Skit", "Short skit to spread health awareness."),
]


def _db():
    return student_alias()


def seed_default_sections():
    if not EventSection.objects.using(_db()).exists():
        for name, description in DEFAULT_SECTIONS:
            EventSection.objects.using(_db()).create(
                event_name=DEFAULT_EVENT, section_name=name, description=description
            )


def list_sections():
    qs = (EventSection.objects.using(_db())
          .annotate(participants=Count("registrations"))
          .order_by("event_name", "section_name"))
    return list(qs.values("id", "event_name", "section_name", "description", "participants"))


def get_section(section_id):
    return EventSection.objects.using(_db()).filter(pk=section_id).values().first()


def add_section(event_name, section_name, description):
    event_name = (event_name or "").strip()
    section_name = (section_name or "").strip()
    description = (description or "").strip()
    if not event_name or not section_name:
        raise ValueError("Event name and section name are required.")
    if len(event_name) > 80 or len(section_name) > 80 or len(description) > 300:
        raise ValueError("Text is too long.")
    try:
        with transaction.atomic(using=_db()):
            return EventSection.objects.using(_db()).create(
                event_name=event_name, section_name=section_name, description=description
            ).pk
    except IntegrityError:
        raise ValueError("That section already exists.")


def delete_section(section_id):
    EventSection.objects.using(_db()).filter(pk=section_id).delete()


def user_section_ids(user_id):
    return set(EventRegistration.objects.using(_db())
               .filter(user_id=user_id).values_list("section_id", flat=True))


def join_section(user, section_id):
    section = EventSection.objects.using(_db()).filter(pk=section_id).first()
    if section is None:
        raise ValueError("That section no longer exists.")
    try:
        with transaction.atomic(using=_db()):
            EventRegistration.objects.using(_db()).create(
                section=section, user_id=user["id"],
                user_name=user["name"], user_email=user["email"],
            )
    except IntegrityError:
        pass  # already joined


def leave_section(user_id, section_id):
    EventRegistration.objects.using(_db()).filter(user_id=user_id, section_id=section_id).delete()


def participants(section_id):
    return list(EventRegistration.objects.using(_db()).filter(section_id=section_id)
                .order_by("id").values("user_name", "user_email", "created_at"))
