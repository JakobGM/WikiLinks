import hashlib
from gettext import gettext as _
from tempfile import NamedTemporaryFile

from django.contrib.auth.models import User
from django.core.files import File
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
    URLValidator,
)
from django.db import models
from django.utils import timezone

import requests

from examiner.parsers import ExamURLParser, Season
from examiner.pdf import PdfReader
from semesterpage.models import Course


def upload_path(instance, filename):
    """Return path to save FileBackup.file backups."""
    return f'examiner/FileBackup/' + filename


class Pdf(models.Model):
    file = models.FileField(
        upload_to=upload_path,
        help_text=_('Kopi av fil hostet på en url.'),
    )
    sha1_hash = models.CharField(
        max_length=40,
        unique=True,
        null=False,
        help_text=_('Unik sha1 hash relativt til filinnhold.'),
        validators=[RegexValidator(
            regex='^[0-9a-f]{40}$',
            message='Not a valid SHA1 hash string.',
        )],
    )
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()

    def read_text(self, allow_ocr: bool = False) -> None:
        """
        Read text from pdf and save result to self.text.

        NB: This does not save the model, you have to explicitly call
        self.save() in order to save the result to the database.

        :param allow_ocr: If True, slow OCR will be used for text extraction
          from non-indexed PDF files.
        """
        pdf = PdfReader(path=self.file.path)
        pdf.read_text(allow_ocr=allow_ocr)
        for page_number, page in enumerate(pdf.pages):
            PdfPage.objects.create(
                pdf=self,
                number=page_number,
                text=page,
                confidence=pdf.page_confidences[page_number],
            )

    @property
    def text(self) -> str:
        """
        Return string content of pdf.

        Pages are separated by pagebreaks, i.e. '\f'.
        """
        return '\f'.join([page.text for page in self.pages.order_by('number')])

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class PdfPage(models.Model):
    pdf = models.ForeignKey(
        to=Pdf,
        null=False,
        on_delete=models.CASCADE,
        help_text=_('Tilhørende PDF fil.'),
        related_name='pages',
    )
    number = models.PositiveSmallIntegerField(
        null=False,
        help_text=_('Sidetall.'),
    )
    text = models.TextField(
        null=False,
        help_text=_('Sideinnhold i rent tekstformat.'),
    )
    confidence = models.PositiveIntegerField(
        null=True,
        default=None,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Konfidens til evt. OCR av tekstinnhold.'),
    )

    class Meta:
        ordering = ('pdf', 'number')
        unique_together = ('pdf', 'number')


class PdfUrlQuerySet(models.QuerySet):
    def organize(self):
        organization = {}
        for url in self:
            urls = organization.setdefault(url.course_code, [])
            urls.append(url)

        for course_code, urls in organization.items():
            organization[course_code] = {'years': {}}
            for url in urls:
                year = organization[course_code]['years'].setdefault(
                    url.year,
                    {},
                )
                semester = year.setdefault(
                    Season.str_from_field(url.season),
                    {'solutions': {}, 'exams': {}}
                )
                key = 'solutions' if url.solutions else 'exams'
                urls = semester[key].setdefault(
                    url.language or 'Ukjent',
                    [],
                )
                urls.append(url)

            organization[course_code] = dict(organization[course_code])

        courses = Course.objects.filter(
            course_code__in=organization.keys(),
        )
        for course in courses:
            course_dict = organization[course.course_code]
            course_dict['full_name'] = course.full_name
            course_dict['nick_name'] = course.display_name

        return organization


class PdfUrl(models.Model):
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
        choices=[
            ('Bokmål', 'Bokmål'),
            ('Nynorsk', 'Nynorsk'),
            ('Engelsk', 'Engelsk'),
            (None, 'Ukjent'),
        ],
        help_text=_('Språket som eksamen er skrevet i.'),
    )
    year = models.PositiveSmallIntegerField(
        null=True,
        help_text=_('Året som eksamen ble holdt.'),
    )
    season = models.PositiveSmallIntegerField(
        null=True,
        choices=[
            (1, 'Vår'),
            (2, 'Kontinuasjonseksamen'),
            (3, 'Høst'),
            (None, 'Ukjent'),
        ],
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
        help_text=_('Brukere som har verifisert metadataen.'),
    )
    scraped_pdf = models.ForeignKey(
        to=Pdf,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_('Kopi av filen fra URLen.'),
        related_name='hosted_at',
    )
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()
    objects = PdfUrlQuerySet.as_manager()

    def backup_file(self) -> None:
        """Download and backup file from url, and save to self.file_backup."""
        response = requests.get(self.url, stream=True, allow_redirects=True)
        if not response.ok:
            self.dead_link = True
            self.save()
            return

        sha1_hasher = hashlib.sha1()
        temp_file = NamedTemporaryFile()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)
                sha1_hasher.update(chunk)

        content_file = File(temp_file)
        sha1_hash = sha1_hasher.hexdigest()

        try:
            file_backup = Pdf.objects.get(sha1_hash=sha1_hash)
        except Pdf.DoesNotExist:
            file_backup = Pdf(sha1_hash=sha1_hash)
            file_backup.file.save(name=sha1_hash, content=content_file)
            file_backup.save()

        self.scraped_pdf = file_backup
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
