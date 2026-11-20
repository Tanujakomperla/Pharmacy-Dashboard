from django.db import models


class StudentRecord(models.Model):
    """One student's marks. Lives in the STUDENT database (not the users one).

    user_id is the id of the login account in the other database. It is a plain
    number (not a ForeignKey) because the two databases are separate.
    """

    student_id = models.CharField(max_length=10, unique=True)
    user_id = models.IntegerField(null=True, blank=True, unique=True)
    source = models.CharField(max_length=10, default="student")
    student_name = models.CharField(max_length=80)
    gender = models.CharField(max_length=10)
    age = models.IntegerField()
    year = models.CharField(max_length=20, default="3rd Year")
    semester = models.IntegerField(default=5)
    course = models.CharField(max_length=30, default="B.Pharm")
    attendance = models.FloatField()
    cgpa = models.FloatField()
    medicinal_chemistry_ii = models.IntegerField()
    industrial_pharmacy_i = models.IntegerField()
    pharmacology_ii = models.IntegerField()
    pharmacognosy_phytochemistry_ii = models.IntegerField()
    pharmaceutical_jurisprudence = models.IntegerField()
    total_marks = models.IntegerField()
    percentage = models.FloatField()
    gpat_mock_score = models.IntegerField()
    internship_status = models.CharField(max_length=20)
    project_status = models.CharField(max_length=20)
    backlogs = models.IntegerField()
    placement_status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "students"

    def __str__(self):
        return f"{self.student_id} {self.student_name}"


class EventSection(models.Model):
    event_name = models.CharField(max_length=80)
    section_name = models.CharField(max_length=80)
    description = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "event_sections"
        ordering = ["event_name", "section_name"]
        constraints = [
            models.UniqueConstraint(fields=["event_name", "section_name"], name="ux_event_section")
        ]

    def __str__(self):
        return f"{self.event_name} / {self.section_name}"


class EventRegistration(models.Model):
    section = models.ForeignKey(EventSection, on_delete=models.CASCADE, related_name="registrations")
    user_id = models.IntegerField()
    user_name = models.CharField(max_length=80)
    user_email = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "event_registrations"
        constraints = [
            models.UniqueConstraint(fields=["section", "user_id"], name="ux_registration")
        ]
