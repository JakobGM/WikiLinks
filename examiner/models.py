import hashlib
import re
from gettext import gettext as _
from tempfile import NamedTemporaryFile

from django.contrib.auth.models import User
from django.core.files import File
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
    URLValidator,
    ValidationError,
)
from django.db import models
from django.shortcuts import reverse
from django.utils import timezone

import requests

from examiner.parsers import ExamURLParser, PdfParser, Season
from examiner.pdf import PdfReader, PdfReaderException
from semesterpage.models import Course


class ExamRelatedCourse(models.Model):
    """
    Model representing an exam relation between two distinct courses.

    Examples of where this relation will be applicable:

    1) If a course has been discontinued, but a new course is, for all intents
    and purposes, a continuation of the old one.

    2) If a course changes its course code. For instance the SIFXXXX -> TMAXXXX
    re-organization at the Department of Mathematics at NTNU.

    3) Two separate courses always have a common exam each year.

    In this case, we link the course code of one course, for instance 'SIF5013',
    to another course, 'TMA4122'. This relation will group up such courses into
    a single exam archive view for all those courses.
    """
    primary_course = models.ForeignKey(
        to=Course,
        on_delete=models.CASCADE,
        related_name='secondary_courses',
        unique=False,
        blank=False,
        null=False,
        help_text=_('Faget som regnes som hovedfaget.'),
    )
    secondary_course = models.OneToOneField(
        to=Course,
        on_delete=models.SET_NULL,
        related_name='primary_course',
        unique=True,
        blank=True,
        null=True,
        help_text=_('Faget som er underordnet hovedfaget.'),
    )
    secondary_course_code = models.CharField(
        _('sekundæremnekode'),
        unique=True,
        null=False,
        blank=False,
        max_length=15,
        help_text=_('Emnekoden til sekundærfaget, f.eks. "SIF5013".')
    )

    def clean(self, *args, **kwargs) -> None:
        """Derive secondary course from secondary course code if in db."""
        super().clean(*args, **kwargs)
        self.secondary_course_code = self.secondary_course_code.upper()
        try:
            self.secondary_course = (
                Course.objects.get(course_code=self.secondary_course_code)
            )
        except Course.DoesNotExist:
            self.secondary_course = None

    def validate_unique(self, *args, **kwargs):
        """Enforce uniqueness constraints."""
        super().validate_unique(*args, **kwargs)

        # Prevent primary course to be set as a secondary one
        if (
            ExamRelatedCourse
            .objects
            .filter(primary_course__course_code=self.secondary_course_code)
            .exists()
        ):
            raise ValidationError(
                f'Secondary course {self.secondary_course}'
                'is already set as primary course for another course!'
            )

    def save(self, *args, **kwargs):
        """
        Clean and save the ExamRelatedCourse object.

        As the call to the clean method overrides the save method, we must
        invoke it explicitly here.
        See: https://stackoverflow.com/a/32251978
        """
        self.full_clean()
        super().save(*args, **kwargs)


class DocumentInfoQueryset(models.QuerySet):
    def organize(self):
        self = self.filter(pdfs__isnull=False).prefetch_related('course')

        organization = {}
        for docinfo in self:
            course_dict = organization.setdefault(
                docinfo.course_code,
                {'years': {}},
            )
            if docinfo.course and 'full_name' not in course_dict:
                course_dict['full_name'] = docinfo.course.full_name
                course_dict['nick_name'] = docinfo.course.display_name

            year = organization[docinfo.course_code]['years'].setdefault(
                docinfo.year,
                {},
            )
            semester = year.setdefault(
                Season.str_from_field(docinfo.season),
                {'solutions': {}, 'exams': {}}
            )
            key = 'solutions' if docinfo.solutions else 'exams'
            urls = semester[key].setdefault(
                docinfo.language or 'Ukjent',
                [],
            )
            try:
                url = DocumentInfoSource.objects.filter(
                    document_info=docinfo,
                    verified_by__isnull=False,
                ).first().pdf.hosted_at.filter(dead_link=False).first()
            except (AttributeError, DocumentInfoSource.DoesNotExist):
                url = DocumentInfoSource.objects.filter(
                    document_info=docinfo,
                ).first().pdf.hosted_at.filter(dead_link=False).first()

            if url not in urls:
                urls.append(url)

        return organization


class DocumentInfo(models.Model):
    EXAM = 'Exam'
    EXERCISE = 'Exercise'
    IRRELEVANT = 'Irrelevant'
    PROJECT = 'Project'
    UNDETERMINED = None

    content_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        default=None,
        choices=[
            (EXAM, 'Eksamen'),
            (EXERCISE, 'Øving'),
            (PROJECT, 'Prosjekt'),
            (IRRELEVANT, 'Urelevant'),
            (UNDETERMINED, 'Ubestemt'),
        ],
        help_text=_('PDF-ens innholdstype, f.eks. "eksamen".'),
    )

    course = models.ForeignKey(
        to=Course,
        on_delete=models.SET_NULL,
        related_name='docinfos',
        null=True,
        blank=True,
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
        blank=True,
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
        blank=True,
        help_text=_('Året som eksamen ble holdt.'),
    )
    season = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
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
    exercise_number = models.PositiveSmallIntegerField(
        _('Øvingsnummer'),
        default=None,
        null=True,
        blank=True,
        help_text=_(
            'Øvingsnummer hvis dokumentet er en øving eller et prosjekt.',
        ),
    )
    objects = DocumentInfoQueryset.as_manager()

    def __repr__(self) -> str:
        return (
            'DocumentInfo('
            f'content_type={self.content_type}, '
            f"course_code='{self.course_code}', "
            f'year={self.year}, '
            f'season={self.season}, '
            f'language={self.language}, '
            f'solutions={self.solutions}, '
            f'exercise_number={self.exercise_number}'
            ')'
        )

    class Meta:
        ordering = ('course_code', '-year', '-solutions')
        unique_together = (
            'content_type',
            'course_code',
            'language',
            'year',
            'season',
            'solutions',
            'exercise_number',
        )

    def clean(self, *args, **kwargs) -> None:
        """Derive secondary course from secondary course code if in db."""
        super().clean(*args, **kwargs)
        has_exercise_number = self.exercise_number is not None
        should_have_exercise_number = self.content_type in (
            self.EXERCISE,
            self.PROJECT,
        )
        if has_exercise_number and not should_have_exercise_number:
            raise ValidationError(
                _('Bare øvinger og prosjekter kan ha øvingsnummer'),
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
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


class DocumentInfoSource(models.Model):
    """
    Model used for through relation Pdf.exams.

    It contains information of which users verified the document information,
    if any.
    """

    pdf = models.ForeignKey(
        to='Pdf',
        on_delete=models.PROTECT,
        null=False,
        blank=False,
    )
    document_info = models.ForeignKey(
        to=DocumentInfo,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
    )
    verified_by = models.ManyToManyField(
        to=User,
        help_text=_('Brukere som har verifisert metadataen.'),
        related_name='verified_exam_pdfs',
    )


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
    exams = models.ManyToManyField(
        to=DocumentInfo,
        through=DocumentInfoSource,
        related_name='pdfs',
        help_text=_('Hvilke eksamenssett PDFen trolig inneholder.'),
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
        Parse PDF content and classify the related DocumentInfo model object.

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

        # Early return if this PDF has already a verified DocumentInfo
        if (
            DocumentInfoSource
            .objects
            .filter(pdf=self, verified_by__isnull=False)
            .exists()
        ):
            return True

        pdf_parser = PdfParser(text=first_page.text)

        # All the document informations belonging to URLs which host this PDF
        doc_infos = DocumentInfo.objects.filter(urls__scraped_pdf=self)

        # The solutions parsers are relatively conservative, so we can OR
        # determine it from all the parsers.
        solutions = any([
            pdf_parser.solutions,
            *doc_infos.values_list('solutions', flat=True)
        ])

        # Get course codes from pdf content and URL classifications
        course_codes = set(pdf_parser.course_codes)
        course_codes.update(
            doc_infos.values_list('course_code', flat=True)
        )
        if not course_codes:
            course_codes = {None}

        # Now replace None values from the PDF parser with the most frequent
        # values in the URL parse results.
        for field in ('language', 'year', 'season'):
            parser_field_value = getattr(pdf_parser, field)
            if parser_field_value is not None:
                # The PDF parser is more trusted than the URL parser
                continue

            ordered_field_values = (
                # All the docinfos of the URLs
                doc_infos
                # Collapsed into a list of field values
                .values_list(field)
                # Annotated with the number of occurences of each value
                .annotate(count=models.Count(field))
                # Ordered by decreasing frequency
                .order_by('-' + field)
            )
            if not ordered_field_values.exists():
                # No URLs exist
                continue

            # Extracting the value that occurs the most
            setattr(
                pdf_parser,
                field,
                ordered_field_values.first()[0],
            )

        # Delete old relations that are NOT verified
        DocumentInfoSource.objects.filter(pdf=self, verified_by=None).delete()

        for course_code in course_codes:
            # Get docinfos model object which this PDF is related to
            docinfo, _ = DocumentInfo.objects.get_or_create(
                course_code=course_code,
                language=pdf_parser.language,
                year=pdf_parser.year,
                season=pdf_parser.season,
                solutions=solutions,
                content_type=pdf_parser.content_type,
            )

            # And create the new relation
            DocumentInfoSource.objects.create(document_info=docinfo, pdf=self)

        if save:
            self.save()
        return True

    def clean(self, *args, **kwargs) -> None:
        """Ensure correct SHA1 hash formatting, also for filenames."""
        super().clean(*args, **kwargs)
        sha1_pattern = re.compile(r'^[0-9a-f]{40}$')
        if not sha1_pattern.match(self.sha1_hash):
            raise ValidationError('Not valid SHA1 formatted hash!')

        if (
            len(self.file.name) < 44 or
            self.file and self.file.name[-44:] != self.sha1_hash + '.pdf'
        ):
            raise ValidationError(
                f'Pdf.file must be named "{self.sha1_hash}.pdf"!',
            )

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Return URL to PDF document verification form view."""
        return reverse(
            viewname='examiner:verify_pdf',
            kwargs={'sha1_hash': self.sha1_hash},
        )

    def __repr__(self) -> str:
        """Return programmer representation of Pdf object."""
        return (
            'Pdf('
            f"sha1_hash='{self.sha1_hash}', "
            f'exam={self.exams.all()}, '
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
        to=DocumentInfo,
        on_delete=models.SET_NULL,
        null=True,
        help_text=_('Hvilken innholdstype URLen trolig tjener.'),
        related_name='urls',
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
            file_backup.file.save(name=sha1_hash + '.pdf', content=content_file)
            file_backup.save()

        self.scraped_pdf = file_backup
        self.dead_link = False
        self.save()
        return new

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()

        if not self.exam:
            self.classify(save=False)

        super().save(*args, **kwargs)

    def classify(self, save: bool = True) -> None:
        """Set field attributes by parsing the provided url."""
        if self.id and self.verified_by.count() != 0:
            # The metadata has been verified, so we should not mutate
            return

        parser = ExamURLParser(url=self.url)

        self.probably_exam = parser.probably_exam
        if parser.probably_exam:
            content_type = DocumentInfo.EXAM
        else:
            content_type = DocumentInfo.UNDETERMINED

        self.filename = parser.filename
        self.exam, _ = DocumentInfo.objects.get_or_create(
            language=parser.language,
            year=parser.year,
            season=parser.season,
            solutions=parser.solutions,
            course_code=parser.code,
            content_type=content_type,
            exercise_number=None,
        )
        if save:
            self.save()

    def __repr__(self) -> str:
        """Return programmer representation of PdfUrl object."""
        return f"PdfUrl(url='{self.url}')"
