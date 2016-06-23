from django.db import models
from django.core.exceptions import ValidationError

from gettext import gettext as _
import os


def upload_path(instance, filename):
    """
    For setting the upload_to parameter of FileFields and ImageFields,
        e.g. field_name = FileField(upload_to=upload_path)
    Returns a MEDIA_ROOT file path that is guaranteed to not collide with
    excisting model instances, as it uses the model class name and the
    model instance's primary key
    """
    return os.path.join(instance.__class__.__name__, instance.pk, filename)


class StudyProgram(models.Model):
    """
    Contains top level information for a specific study program.
    """
    full_name = models.CharField(
        _('fullt navn'),
        max_length=60,
        help_text=_('F.eks. \"Fysikk og matematikk\"')
    )
    display_name = models.CharField(
        _('visningsnavn / kallenavn'),
        max_length=60,
        help_text=_('F.eks. \"Fysmat\"')
    )
    program_code = models.CharField(
        _('programkode'),
        primary_key=True,
        max_length=10,
        help_text=_('F.eks. \"MTFYMA\"')
    )  # TODO: Only upper case?

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['full_name']
        verbose_name = _('studieprogram')
        verbose_name_plural = _('studieprogram')


class MainProfile(models.Model):
    """
    Contains top level information about a main profile within a given study
    program.
    """
    full_name = models.CharField(
        _('fullt navn'),
        max_length=60,
        default=_('felles'),
        help_text=_('F.eks. \"Industriell matematikk\"')
    )
    display_name = models.CharField(
        _('visningsnavn / kallenavn'),
        max_length=60,
        default=_('Felles'),
        help_text=_('F.eks. \"InMat\"')
    )
    study_program = models.ForeignKey(
        StudyProgram,
        on_delete=models.CASCADE,
        related_name='mainProfiles'
    )

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']
        verbose_name = _('hovedprofil')
        verbose_name_plural = _('hovedprofiler')


class Semester(models.Model):
    """
    Contains an instance of a specific semester connected to a main profile.
    """
    number = models.PositiveSmallIntegerField(
        _('semester (nummer)'),
        help_text='F.eks. \"2\"'
    )
    study_program = models.ForeignKey(
        StudyProgram,
        on_delete=models.CASCADE,
        related_name='semesters'
    )
    main_profile = models.ForeignKey(
        MainProfile,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None,
        related_name='semesters'
    )

    def __str__(self):
        return str(self.study_program) + " (" + str(self.number) + '. semester)'

    class Meta:
        ordering = ['study_program', 'number']
        verbose_name = _('semester')
        verbose_name_plural = _('semestere')


class Course(models.Model):
    """
    Contains a specific course with a logo for display on the semesterpage.
    Can be connected to several different semesters.
    """
    full_name = models.CharField(
        _('fullt navn'),
        unique=True,
        max_length=60,
        help_text=_('F.eks. \"Prosedyre- og Objektorientert Programmering\"')
    )
    display_name = models.CharField(
        _('visningsnavn'),
        max_length=60,
        help_text=_('F.eks. \"C++\"')
    )
    course_code = models.CharField(
        'emnekode',
        primary_key=True,
        max_length=10,
        help_text=_('F.eks. \"TDT4102\"')
    )
    semesters = models.ManyToManyField(
        Semester,
        related_name='courses'
    )
    logo = models.FileField(upload_to=upload_path)
    homepage = models.URLField(
        _('Fagets hjemmeside'),
        help_text=_('F.eks. \"http://home.phys.ntnu.no/fysikkfag/eksamensoppgaver\"')
    )

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']
        verbose_name = _('fag')
        verbose_name_plural = _('fag')


class LinkCategory(models.Model):
    """
    Contains a category for the link model, including a thumbnail. The
    thumbnail is used on the semester page for styling the list item containig
    the link.
    """
    name = models.CharField(
        _('Egendefinert kategori'),
        primary_key=True,
        max_length=60
    )
    thumbnail = models.FileField(
        _('ikon for kategori'),
        upload_to=upload_path,
        blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('lenkekategori')
        verbose_name_plural = _('lenkekategorier')


# Filenames for static thumbnails for the default link categories
# The thumbnails must be stored in:
#       semesterpage/static/semesterpage/link_categories/
TASKS = 'tasks.svg'
SOLUTIONS = 'solutions.svg'
VIDEOS = 'videos.svg'
TIMETABLE = 'timetable.svg'
SYLLABUS = 'syllabus.svg'
FORMULAS = 'formulas.svg'
EXAMS = 'exams.svg'
INFO = 'info.svg'
IMPORTANT_INFO = 'important_info.svg'
NTNU = 'ntnu.svg'
WIKIPENDIUM = 'wikipendium.svg'
BOOK = 'book.svg'
QUIZ = 'quiz.svg'
FACEBOOK = 'facebook.svg'
SOFTWARE = 'software.svg'
CHEMISTRY = 'chemistry.svg'

# Descriptive text of the link category choices
DEFAULT_LINK_CATEGORIES = (
    (TASKS, _('Øvinger og prosjekter')),
    (SOLUTIONS, _('Løsningsforslag')),
    (VIDEOS, _('Videoforelesninger')),
    (TIMETABLE, _('Framdrifts- og timeplaner')),
    (SYLLABUS, _('Pensum')),
    (FORMULAS, _('Formelark')),
    (EXAMS, _('Eksamener')),
    (FACEBOOK, _('Facebook')),
    (INFO, _('Informasjon')),
    (IMPORTANT_INFO, _('Viktig informasjon')),
    (NTNU, _('NTNU-lenker')),
    (WIKIPENDIUM, _('Wikipendium')),
    (BOOK, _('Pensumbok')),
    (QUIZ, _('Quiz og punktlister')),
    (SOFTWARE, _('Programvare')),
)


class Link(models.Model):
    """
    Contains a URL link connected to a specific course. The link category
    field determines the mini-icon used when portraying the link as a part
    of a list with custom bullet-point thumbnails
    """
    title = models.CharField(
        _('tittel'),
        max_length=60,
        help_text=_('F.eks \"Gamle eksamenssett\"')
    )
    url = models.URLField(
        'URL',
        help_text=_('F.eks. \"http://www.phys.ntnu.no/fysikkfag/gamleeksamener.html\"')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='links'
    )
    category = models.CharField(
        _('Kateogri'),
        blank=True,
        null=True,
        default=None,
        max_length=60,
        choices=DEFAULT_LINK_CATEGORIES,
        help_text=_('F.eks. "Løsningsforslag". Valget bestemmer hvilket '
                    '"mini-ikon" som plasseres ved siden av lenken.')
    )
    custom_category = models.ForeignKey(
        LinkCategory,
        default=None,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='links',
        verbose_name=_('(Egendefinert kategori)'),
        help_text=_('Hvis du ønsker å bruke et egendefinert "mini-ikon".')
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        blank=False,
        null=False
    )

    def clean(self):
        # Can't allow selection of both a category and a custom category at the
        # same time
        if self.category is not None and self.custom_category is not None:
            raise ValidationError(_('Kan ikke velge både en kateogri '
                                    'og en egendefinert kateogri for en lenke '
                                    'samtidig. Du kan kun velge én av delene, '
                                    'eller ingen av delene.'))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('lenke')
        verbose_name_plural = _('lenker')
        ordering = ('order',)
