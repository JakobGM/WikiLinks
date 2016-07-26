from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from gettext import gettext as _
from autoslug import AutoSlugField
import os


def upload_path(instance, filename):
    """
    For setting the upload_to parameter of FileFields and ImageFields,
        e.g. field_name = FileField(upload_to=upload_path)
    Returns a MEDIA_ROOT file path that is guaranteed to not collide with
    excisting model instances, as it uses the model class name and the
    model instance's primary key
    """
    if instance.pk:
        return os.path.join(instance.__class__.__name__, instance.pk, filename)
    else:
        # When ResourceLinkList instance doesn't have a primary key at invocation
        return os.path.join(instance.__class__.__name__, instance.full_name, filename)


class StudyProgram(models.Model):
    """
    Contains top level information for a specific study program.
    """
    full_name = models.CharField(
        _('fullt navn'),
        max_length=60,
        help_text=_('F.eks. "Fysikk og matematikk"')
    )
    display_name = models.CharField(
        _('visningsnavn / kallenavn'),
        max_length=60,
        help_text=_('F.eks. "Fysmat"')
    )
    slug = AutoSlugField(
        populate_from='display_name',
        unique=True
    )

    def __str__(self):
        return self.full_name + ' A.K.A. ' + self.display_name

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
        help_text=_('F.eks. "Industriell matematikk"')
    )
    display_name = models.CharField(
        _('visningsnavn / kallenavn'),
        max_length=60,
        help_text=_('F.eks. "InMat"')
    )
    study_program = models.ForeignKey(
        StudyProgram,
        on_delete=models.CASCADE,
        related_name='mainProfiles'
    )
    slug = AutoSlugField(
        populate_from='display_name',
        unique_with='study_program'
    )

    def __str__(self):
        return self.display_name + _(' på ') + str(self.study_program)

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
        help_text=_('F.eks. "2"')
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
        string = str(self.number) + '. semester på '
        string += str(self.study_program)
        if self.main_profile is not None:
            string += ' (' + str(self.main_profile) + ')'
        else:
            string += ' (Felles)'

        return string

    class Meta:
        ordering = ['study_program', 'main_profile', 'number']
        verbose_name = _('semester')
        verbose_name_plural = _('semestere')


class LinkList(models.Model):
    """
    An abstract model which Course and ResourceLinkList derive from. It is
    displayed as an article element on the semesterpage view / courses template.
    """
    full_name = models.CharField(
        _('fullt navn'),
        unique=True,
        max_length=60,
        help_text=_('F.eks. "Prosedyre- og Objektorientert Programmering"')
    )
    display_name = models.CharField(
        _('visningsnavn'),
        max_length=60,
        help_text=_('F.eks. "C++"')
    )
    logo = models.FileField(
        upload_to=upload_path,
        help_text=_('Bildet vises over alle lenkene knyttet til faget. '
                    'Bør være kvadratisk for å unngå uheldige skaleringseffekter.')
    )
    homepage = models.URLField(
        _('Fagets hjemmeside'),
        help_text=_('F.eks. "http://www.phys.ntnu.no/fysikkfag/"')
    )

    def __str__(self):
        return self.full_name

    class Meta:
        abstract = True

class Course(LinkList):
    """
    Contains a specific course with a logo for display on the semesterpage.
    Can be connected to several different semesters.
    """
    course_code = models.CharField(
        _('emnekode'),
        unique=True,
        max_length=10,
        help_text=_('F.eks. "TDT4102"')
    )
    semesters = models.ManyToManyField(
        Semester,
        related_name='courses'
    )

    def __str__(self):
        return self.course_code + ': ' + self.full_name

    class Meta:
        ordering = ['full_name']
        verbose_name = _('fag')
        verbose_name_plural = _('fag')


class ResourceLinkList(LinkList):
    """
    Used to portray resource links which are common across all the semesters.
    Almost identical to Course, except for not being connected to any specific
    semester, but a study program instead, and not having a course code.
    """
    study_programs = models.ManyToManyField(
        StudyProgram,
        blank=True,
        null=True,
        related_name='resource_link_lists'
    )
    default = models.BooleanField(
        default=False,
        help_text=_('Skal denne ressurslenkelisten brukes i alle studieprogram som ikke har satt sine egendefinerte '
                    'ressurslenkelister?')
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        blank=False,
        null=False
    )

    class Meta:
        ordering = ['order']
        verbose_name = _('Ressurslenkeliste')
        verbose_name_plural = _('Ressurslenkelister')


class CustomLinkCategory(models.Model):
    """
    Contains a category for the link model, including a thumbnail. The
    thumbnail is used on the semester page for styling the list item containig
    the link. Allows a custom thumbnail when none of the defaults will do.
    Only available in ResourceLinkList.
    """
    name = models.CharField(
        _('Egendefinert kategori'),
        unique=True,
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
        help_text=_('F.eks "Gamle eksamenssett"')
    )
    url = models.URLField(
        'URL',
        help_text=_('F.eks. "http://www.phys.ntnu.no/fysikkfag/gamleeksamener.html"')
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
    order = models.PositiveSmallIntegerField(
        default=0,
        blank=False,
        null=False
    )

    def __str__(self):
        return self.title

    class Meta:
        abstract = True
        ordering = ('order',)


class CourseLink(Link):
    """
    A link connected to a course, without the ability to add custom thumbnails.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='links'
    )

    def __str__(self):
        return self.title + ' ['+ str(self.course) + ']'

    class Meta(Link.Meta):
        verbose_name = _('lenke')
        verbose_name_plural = _('lenker')


class ResourceLink(Link):
    """
    A link connected to one of the two ResourceLinkList elements displayed on
    each semesterpage, with the ability to add custom thumbnails.
    """
    resource_link_list = models.ForeignKey(
        ResourceLinkList,
        on_delete=models.CASCADE,
        related_name='links'
    )
    custom_category = models.ForeignKey(
        CustomLinkCategory,
        default=None,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='links',
        verbose_name=_('(Egendefinert kategori)'),
        help_text=_('Hvis du ønsker å bruke et egendefinert "mini-ikon".')
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
        return self.title + _(' [Ressurslenkeliste: ') + str(self.resource_link_list) + ']'


    class Meta(Link.Meta):
        verbose_name = _('ressurslenke')
        verbose_name_plural = _('ressurslenker')


class Contributor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    study_program = models.ForeignKey(
        StudyProgram,
        blank=False,
        related_name='contributors'
    )
    main_profile = models.ForeignKey(
        MainProfile,
        blank=True,
        null=True,
        related_name='contributors'
    )
    semester = models.ForeignKey(
        Semester,
        blank=True,
        null=True,
        related_name='contributors'
    )
