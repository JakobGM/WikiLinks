import hashlib
from gettext import gettext as _

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone

import requests

from examiner.parsers import ExamURLParser, Language, Season
from semesterpage.models import Course


def upload_path(instance, filename):
    """Return path to save FileBackup.file backups."""
    return f'examiner/FileBackup/' + filename


class FileBackup(models.Model):
    file = models.FileField(
        upload_to=upload_path,
        help_text=_('Kopi av fil hostet på en url.'),
    )
    md5_hash = models.CharField(
        max_length=32,
        unique=True,
        null=False,
        help_text=_('Unik md5 hash relativt til filinnhold.'),
    )
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class ExamURL(models.Model):
    url = models.TextField(
        unique=True,
        validators=[URLValidator()],
    )
    filename = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text=_('Ressursens filnavn.'),
    )
    course = models.ForeignKey(
        to=Course,
        on_delete=models.CASCADE,
        related_name='exam_urls',
        blank=True,
        null=True,
        help_text=_('Faget som eksamenen tilhører.'),
    )
    course_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text=_('Eksamens fagkode.'),
    )
    language = models.CharField(
        max_length=20,
        null=True,
        choices=[(tag, tag.value) for tag in Language],
        help_text=_('Språket som eksamen er skrevet i.'),
    )
    year = models.PositiveSmallIntegerField(
        null=True,
        help_text=_('Året som eksamen ble holdt.'),
    )
    season = models.CharField(
        max_length=20,
        null=True,
        choices=[(tag, tag.value) for tag in Season],
        help_text=_('Semestertype når eksamen ble holdt.'),
    )
    solutions = models.BooleanField(
        default=False,
        help_text=_('Om filen inneholder løsningsforslag.'),
    )
    probably_exam = models.BooleanField(
        default=False,
        help_text=_('Om denne filen trolig er relatert til en eksamen.'),
    )
    dead_link = models.NullBooleanField(
        default=None,
        null=True,
        help_text=_('Om URLen faktisk tjener relevant innhold.'),
    )
    verified_by = models.ManyToManyField(
        to=User,
        null=True,
        help_text=_('Brukere som har verifisert metadataen.'),
    )
    file_backup = models.ForeignKey(
        to=FileBackup,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_('Kopi av filen fra URLen.'),
    )
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()

    def backup_file(self) -> None:
        """Download and backup file from url, and save to self.file_backup."""
        response = requests.get(self.url, stream=True, allow_redirects=True)
        if not response.ok:
            self.dead_link = True
            self.save()
            return

        md5 = hashlib.md5(response.content).hexdigest()
        content_file = ContentFile(response.content)

        try:
            file_backup = FileBackup.objects.get(md5_hash=md5)
        except FileBackup.DoesNotExist:
            file_backup = FileBackup(md5_hash=md5)
            file_backup.file.save(name=md5, content=content_file)
            file_backup.save()

        self.file_backup = file_backup
        self.dead_link = False
        self.save()

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()

        if self.course and not self.course_code:
            self.course_code = self.course.course_code

        super().save(*args, **kwargs)

    def parse_url(self) -> None:
        """Set field attributes by parsing the provided url."""
        if self.id and self.verified_by.count() != 0:
            # The metadata has been verified, so we should not mutate
            return

        parser = ExamURLParser(url=self.url)
        self.course_code = parser.code

        try:
            self.course = Course.objects.get(course_code=self.course_code)
        except Course.DoesNotExist:
            self.course = None

        self.filename = parser.filename
        self.language = parser.language
        self.year = parser.year
        self.season = parser.season
        self.solutions = parser.solutions
        self.probably_exam = parser.probably_exam
