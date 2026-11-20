"""Login accounts use Django's built-in User model (users database).

role: is_staff=True  -> administrator,  is_staff=False -> student.
Email is the username. The person's name is stored in first_name.
"""
import re

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def clean_email(email):
    return (email or "").strip().lower()


def create_user(name, email, password, role="student"):
    name = (name or "").strip()
    email = clean_email(email)
    if not name or len(name) > 80:
        raise ValueError("Please enter your full name (up to 80 characters).")
    if not EMAIL_PATTERN.match(email) or len(email) > 120:
        raise ValueError("Please enter a valid email address.")
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise ValueError("Password must be at least %d characters." % MIN_PASSWORD_LENGTH)
    if role not in ("student", "admin"):
        raise ValueError("Invalid role.")
    if User.objects.filter(username=email).exists():
        raise ValueError("An account with this email already exists.")
    try:
        with transaction.atomic():
            return User.objects.create_user(
                username=email, email=email, password=password, first_name=name,
                is_staff=(role == "admin"), is_superuser=(role == "admin"),
            )
    except IntegrityError:
        raise ValueError("An account with this email already exists.")


def verify_login(email, password):
    return authenticate(username=clean_email(email), password=password or "")


def list_students():
    return list(User.objects.filter(is_staff=False).order_by("id")
                .values("id", "first_name", "email", "date_joined"))


def ensure_admin(email, password, name="Administrator"):
    """The ADMIN_PASSWORD environment variable is always the source of truth."""
    email = clean_email(email)
    user = User.objects.filter(username=email).first()
    if user is None:
        user = User(username=email, email=email, first_name=name)
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    return user


def role_of(user):
    return "admin" if user.is_staff else "student"
