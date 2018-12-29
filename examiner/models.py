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

from examiner.parsers import ExamURLParser, PdfParser, Season
from examiner.pdf import PdfReader, PdfReaderException
from semesterpage.models import Course


class Exam(models.Model):
    course = models.ForeignKey(
        to=Course,
        on_delete=models.CASCADE,
        related_name='exams',
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

    def __repr__(self) -> str:
        return (
            'Exam('
            f"course_code='{self.course_code}', "
            f'year={self.year}, '
            f'season={self.season}, '
            f'language={self.language}, '
            f'solutions={self.solutions}'
            ')'
        )

    class Meta:
        ordering = ('course_code', '-year', '-solutions')
        unique_together = (
            'course_code',
            'language',
            'year',
            'season',
            'solutions',
        )

    def save(self, *args, **kwargs) -> None:
        if self.course and not self.course_code:
            self.course_code = self.course.course_code
        elif self.course_code and not self.course:
            try:
                self.course = Course.objects.get(course_code=self.course_code)
            except Course.DoesNotExist:
                pass

        super().save(*args, **kwargs)


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
    exam = models.ForeignKey(
        to=Exam,
        on_delete=models.SET_NULL,
        null=True,
        help_text=_('Hvilket eksamenssett PDFen trolig inneholder.'),
    )
    content_type = models.CharField(
        max_length=20,
        null=True,
        default=None,
        choices=[
            ('Exam', 'Eksamen'),
            ('Exercise', 'Øving'),
            ('Other', 'Annet'),
            (None, 'Ubestemt'),
        ],
        help_text=_('PDF-ens innholdstype, f.eks. "eksamen".'),
    )
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()

    def read_text(
        self,
        allow_ocr: bool = False,
        force_ocr: bool = False,
    ) -> bool:
        """
        Read text from pdf and save result to self.text.

        NB: This does not save the model, you have to explicitly call
        self.save() in order to save the result to the database.

        :param allow_ocr: If True, slow OCR will be used for text extraction
          from non-indexed PDF files.
        :param force_ocr: If True, OCR will be used even if text content can
          be read directly from the PDF.
        :return: True if pages were actually read and persisted.
        """
        pdf = PdfReader(path=self.file.path)
        try:
            pdf.read_text(allow_ocr=allow_ocr, force_ocr=force_ocr)
        except PdfReaderException:
            return False

        pages = pdf.pages
        if len(pages) == 0:
            return False

        for page_number, page in enumerate(pdf.pages):
            PdfPage.objects.create(
                pdf=self,
                number=page_number,
                text=page,
                confidence=pdf.page_confidences[page_number],
            )
        return True

    @property
    def text(self) -> str:
        """
        Return string content of pdf.

        Pages are separated by pagebreaks, i.e. '\f'.
        """
        return '\f'.join([page.text for page in self.pages.order_by('number')])

    def classify(
        self,
        save: bool = True,
        read: bool = True,
        allow_ocr: bool = True,
    ) -> bool:
        """
        Parse PDF content and classify the related Exam model object.

        :param save: If the Pdf should be saved when parsing finishes.
        :param read: If PDF content should be read if no pages are found.
        :param allow_ocr: If OCR can be used when reading PDF content.
        :return: True if parsing was a success.
        """
        first_page = self.pages.first()
        if not first_page and not read:
            return False

        if not first_page:
            success = self.read_text(allow_ocr=allow_ocr)
            if not success:
                return False
            else:
                first_page = self.pages.first()

        assert first_page.number == 0
        pdf_parser = PdfParser(text=first_page.text)

        if pdf_parser.probably_exam:
            self.content_type = 'Exam'

        # TODO: Support several course codes
        if pdf_parser.course_codes:
            course_code = pdf_parser.course_codes[0]
        else:
            course_code = None

        self.exam, _ = Exam.objects.get_or_create(
            course_code=course_code,
            language=pdf_parser.language,
            year=pdf_parser.year,
            season=pdf_parser.season,
            solutions=pdf_parser.solutions,
        )
        if save:
            self.save()
        return True

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __repr__(self) -> str:
        """Return programmer representation of Pdf object."""
        return (
            'Pdf('
            f"sha1_hash='{self.sha1_hash}', "
            f'exam={self.exam}, '
            f'pages={self.pages.count()}'
            ')'
        )


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

    def __repr__(self) -> str:
        """Return programmer representation of PdfPage object."""
        return (
            'PdfPage('
            f'pdf={repr(self.pdf)}, '
            f'number={self.number}, '
            f'confidence={self.confidence}'
            ')'
        )


class PdfUrlQuerySet(models.QuerySet):
    def organize(self):
        organization = {}
        for url in self.prefetch_related('exam'):
            urls = organization.setdefault(url.exam.course_code, [])
            urls.append(url)

        for course_code, urls in organization.items():
            organization[course_code] = {'years': {}}
            for url in urls:
                if url.scraped_pdf and url.scraped_pdf.exam:
                    # Use classification of PDF content
                    exam = url.scraped_pdf.exam
                else:
                    # Use classification of URL
                    exam = url.exam

                year = organization[course_code]['years'].setdefault(
                    exam.year,
                    {},
                )
                semester = year.setdefault(
                    Season.str_from_field(exam.season),
                    {'solutions': {}, 'exams': {}}
                )
                key = 'solutions' if exam.solutions else 'exams'
                urls = semester[key].setdefault(
                    exam.language or 'Ukjent',
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
    exam = models.ForeignKey(
        to=Exam,
        on_delete=models.SET_NULL,
        null=True,
        help_text=_('Hvilket eksamenssett URLen trolig tjener.'),
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

    def backup_file(self) -> bool:
        """
        Download and backup file from url, and save to self.file_backup.

        :return: True if the PDF backup is a new unique backup, else False.
        """
        try:
            response = requests.get(self.url, stream=True, allow_redirects=True)
        except ConnectionError:
            self.dead_link = True
            self.save()
            return

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
            new = False
        except Pdf.DoesNotExist:
            new = True
            file_backup = Pdf(sha1_hash=sha1_hash)
            file_backup.file.save(name=sha1_hash, content=content_file)
            file_backup.save()

        self.scraped_pdf = file_backup
        self.dead_link = False
        self.save()
        return new

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def classify(self) -> None:
        """Set field attributes by parsing the provided url."""
        if self.id and self.verified_by.count() != 0:
            # The metadata has been verified, so we should not mutate
            return

        parser = ExamURLParser(url=self.url)
        self.filename = parser.filename
        self.probably_exam = parser.probably_exam
        self.exam, _ = Exam.objects.get_or_create(
            language=parser.language,
            year=parser.year,
            season=parser.season,
            solutions=parser.solutions,
            course_code=parser.code,
        )
        self.save()

    def __repr__(self) -> str:
        """Return programmer representation of PdfUrl object."""
        return f"PdfUrl(url='{self.url}')"
