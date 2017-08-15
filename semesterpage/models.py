import os
from os.path import basename
from collections import defaultdict
from gettext import gettext as _

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q

import subdomains.utils
from autoslug import AutoSlugField
from autoslug.utils import slugify
from sanitizer.models import SanitizedCharField

from dataporten.models import DataportenUser

DEFAULT_STUDY_PROGRAM_SLUG = getattr(settings, 'DEFAULT_STUDY_PROGRAM_SLUG', 'fysmat')

def upload_path(instance, filename):
    """
    For setting the upload_to parameter of FileFields and ImageFields,
        e.g. field_name = FileField(upload_to=upload_path)
    Returns a MEDIA_ROOT file path that is quite descriptive as it uses
    the instance.__str__ method. It is assumed that this method is defined.
    """
    return os.path.join(instance.__class__.__name__, slugify(str(instance)), filename)

def norwegian_slugify(instance: models.Model) -> str:
    """
    Given a norwegian phrase instance.display_name,
    replace norwegian characters with latin characters
    """
    text = instance.display_name
    replacements = [('æ', 'e'), ('ø', 'o'), ('å', 'a')]
    for (nor, eng) in replacements:
        text = text.replace(nor, eng)

    return text


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
        populate_from=norwegian_slugify,
        always_update=True,
        unique=True
    )
    has_archive = models.BooleanField(
        _('har arkiv'),
        default=False,
        help_text=_('Huk av hvis studieprogrammet har filer i arkivet på kokekunster.no/arkiv.')
    )
    published = models.BooleanField(
        _('publisert'),
        default=False,
        help_text=_('Studieprogrammet dukker ikke opp i studieprogramlisten i navigasjonsbaren før det er publisert, '
                    'men det er fortsatt mulig å besøke studieprogrammet manuelt (URL: visningsnavn.kokekunster.no) '
                    'for å teste resultatet før du publiserer.')
    )

    @property
    def simple_semesters(self):
        """
        Returns all of the study program's semesters that are not part of any main profile
        """
        return self.semesters.filter(main_profile=None, published=True)

    @property
    def grouped_split_semesters(self):
        """
        Grouping the split semesters (semesters part of a main profile) by semester.number
        """
        split_semesters = self.semesters.exclude(main_profile=None).filter(published=True)
        _grouped_split_semesters = defaultdict(list)
        for split_semester in split_semesters:
            _grouped_split_semesters[split_semester.number].append(split_semester)
        return _grouped_split_semesters.items()

    @property
    def resource_link_lists(self):
        """
        Get the ResourceLinkLists, falling back on the default ones if there are no custom ones for the study program
        """
        # TODO: Return QuerySets instead, making prefetch_related possible.
        if self._resource_link_lists.exists():
            _resource_link_lists = self._resource_link_lists.all()
        else:
            _resource_link_lists = ResourceLinkList.objects.filter(default=True)[:2]
        return _resource_link_lists

    def check_access(self, user):
        return self in user.contributor.accessible_study_programs()

    def get_absolute_url(self):
        return reverse('semesterpage-studyprogram', args=[self.slug])

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['display_name']
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
        related_name='main_profiles',
        verbose_name=_('studieprogram')
    )
    slug = AutoSlugField(
        populate_from=norwegian_slugify,
        always_update=True,
        unique_with='study_program'
    )

    def check_access(self, user):
        return self in user.contributor.accessible_main_profiles()

    def get_absolute_url(self):
        return reverse('semesterpage-mainprofile', args=[self.study_program.slug, self.slug])

    def __str__(self):
        return self.display_name + ', ' + str(self.study_program)

    class Meta:
        ordering = ['display_name']
        verbose_name = _('hovedprofil')
        verbose_name_plural = _('hovedprofiler')


class Semester(models.Model):
    """
    Contains an instance of a specific semester connected to a main profile.
    """
    number = models.PositiveSmallIntegerField(
        _('semesternummer'),
        help_text=_('F.eks. "2"')
    )
    study_program = models.ForeignKey(
        StudyProgram,
        on_delete=models.CASCADE,
        related_name='semesters',
        verbose_name=_('studieprogram')
    )
    main_profile = models.ForeignKey(
        MainProfile,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None,
        related_name='semesters',
        verbose_name=_('hovedprofil')
    )
    has_electives = models.BooleanField(
        _('valgfag'),
        default=False,
        help_text=_('Huk av hvis dette semesteret har valgfag. I så fall vises et ekstra generisk "valgfag" på '
                    'nettsiden til semesteret, hvor brukeren bes om å logge på for å velge valgfagene.'),
    )
    published = models.BooleanField(
        _('publisert'),
        default=False,
        help_text=_('Semesteret dukker ikke opp i navigasjonsbaren før det er publisert, men det er fortsatt mulig å '
                    'besøke semesteret manuelt (URL: kokekunster.no/studieprogram/hovedprofil/semesternummer) for å '
                    'teste resultatet før du publiserer.'),
    )


    def check_access(self, user):
        return self in user.contributor.accessible_semesters()

    def get_archive_url(self):
        # Returns the url to the archive section for the semester. Note the use of title().
        if self.main_profile:
            return subdomains.utils.reverse(
                'semesterpage-splitarchive',
                subdomain='arkiv',
                args=[self.study_program.slug.title(), self.number, self.main_profile.slug.title()]
            )
        else:
            return subdomains.utils.reverse(
                'semesterpage-simplearchive',
                subdomain='arkiv',
                args=[self.study_program.slug.title(), self.number]
                )

    def get_absolute_url(self):
        if self.main_profile:
            return reverse('semesterpage-semester', args=[self.study_program.slug, self.main_profile.slug, self.number])
        else:
            return reverse('semesterpage-simplesemester', args=[self.study_program.slug, self.number])

    def __str__(self):
        if self.main_profile is not None:
            string = self.main_profile.display_name + ' '
        else:
            string = 'Felles '
        string += str(self.number) + '. semester, '
        string += self.study_program.full_name

        return string

    class Meta:
        ordering = ['main_profile__display_name', 'number']
        verbose_name = _('semester')
        verbose_name_plural = _('semestere')


class LinkList(models.Model):
    """
    An abstract model which Course and ResourceLinkList derive from. It is
    displayed as an article element on the semesterpage view / courses template.
    """
    full_name = models.CharField(
        _('fullt navn'),
        max_length=120,
        help_text=_('F.eks. "Prosedyre- og Objektorientert Programmering"')
    )
    # When display name is set as blank, the display name is deduced
    # from full_name instead
    display_name = models.CharField(
        _('visningsnavn'),
        blank=True,
        max_length=60,
        help_text=_('F.eks. "C++"')
    )
    safe_logo = models.ImageField(
        verbose_name=_('logo'),
        upload_to=upload_path,
        help_text=_('Bildet vises over alle lenkene knyttet til faget. '
                    'NB! Bildet skaleres automatisk til å bli kvadratisk, '
                    'SVG bilder er ikke tillatt.'),
        blank=True,
        null=True
    )
    # Allows admins to upload potentially unsafe SVG logos if so desired
    unsafe_logo = models.FileField(
        verbose_name=_('SVG logo'),
        upload_to=upload_path,
        blank=True,
        null=True
    )
    homepage = models.URLField(
        _('Fagets hjemmeside'),
        blank=True,
        help_text=_('F.eks. "http://www.phys.ntnu.no/fysikkfag/". '
                    'Denne lenken kan besøkes ved å trykke på ikonet til faget.')
    )

    @property
    def logo(self):
        # If an 'unsafe' SVG is uploaded by the admin, use that one
        if self.unsafe_logo:
            return self.unsafe_logo
        else:
            return self.safe_logo

    def __str__(self):
        return self.full_name

    def clean(self):
        # Can't allow upload of both a safe logo and an unsafe one
        if self.safe_logo and self.unsafe_logo:
            raise ValidationError(_('En administrator har allerede satt en logo for dette faget, '
                                    'og du kan derfor ikke velge en ny logo.'))

    class Meta:
        abstract = True


class Course(LinkList):
    """
    Contains a specific course with a logo for display on the semesterpage.
    Can be connected to several different semesters.
    """
    # We do a lot of filtering by course_code, so we index this collumn
    course_code = models.CharField(
        _('emnekode'),
        unique=True,
        db_index=True,
        max_length=10,
        help_text=_('F.eks. "TDT4102"')
    )
    semesters = models.ManyToManyField(
        Semester,
        blank=True,
        related_name='courses',
        verbose_name=_('semestre'),
        help_text=_('Hvis du lager et fag for deg selv, så kan du bare hoppe over dette valget.')
    )
    contributors = models.ManyToManyField(
        'Contributor',
        related_name='courses',
        blank=True,
        help_text=_('Bidragsytere som har redigeringstilgang til faget.')
    )
    created_by = models.ForeignKey(
        'Contributor',
        related_name='created_courses',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_('Hvem som opprettet faget.')
    )
    # The unique id provided from dataporten, intended for future db_index when the entire
    # database has been provided with dataporten_uid
    dataporten_uid = models.CharField(
        _('dataporten uid'),
        unique=True,
        null=True,
        max_length=60,
        help_text=_('Dataporten unik id'),
    )

    def check_access(self, user):
        return self in user.contributor.accessible_courses()

    def get_admin_url(self):
        info = (self._meta.app_label, self._meta.model_name)
        return reverse('admin:%s_%s_change' % info, args=(self.pk,))

    def get_absolute_url(self):
        if self.semesters.exists():
            return self.semesters.all()[0].get_absolute_url()
        else:
            try:
                return Options.objects.filter(self_chosen_courses__in=[self])[0].get_absolute_url()
            except IndexError:
                return reverse('semesterpage-homepage')

    def save(self, *args, **kwargs):
        """
        Custom save method in order to guarantee that the course code 'TMA2400'
        is entirely capaitalized.
        """
        self.course_code = self.course_code.upper()
        super(Course, self).save(*args, **kwargs)

    @property
    def short_name(self):
        """
        Gives the name of the course, used as the title of the course in templates.
        Is generated such that it does fit in the column representation in the HTML/CSS.
        """
        # If display name is set, use this in the template
        if self.display_name:
            return self.display_name

        # If the full name is short enough, just use it
        if len(self.full_name) <= 12:
            return self.full_name

        # Upper case acronym of the full name
        acronym = ''.join(
            word[0]
            for word
            in self.full_name.split()
        ).upper()

        # One letter acronyms don't make sense
        if len(acronym) > 1:
            return acronym

        # Last option:
        # Truncate the full name with ellipses
        return self.full_name[0:11] + '...'

    @property
    def url(self) -> str:
        """
        Gives the url which the course logo and header should redirect to. If
        the course has no homepage url set, it should redirect to the course
        admin instead.
        """
        if self.homepage:
            return self.homepage
        else:
            return self.get_admin_url()

    def __str__(self):
        return self.course_code + ' - ' + self.full_name

    class Meta:
        ordering = ['display_name']
        verbose_name = _('fag')
        verbose_name_plural = _('fag')


def course_file_path(instance: 'CourseUpload', filename: str) -> str:
    """
    Returns the file path of a user uploaded course file, used in the upload_to
    parameter of the FileField.
    """
    return os.path.join(
        'fagfiler',
        slugify(instance.course.course_code).upper(),
        filename,
    )


class CourseUpload(models.Model):
    course = models.ForeignKey(
        Course,
        related_name='uploads',
    )
    file = models.FileField(
        upload_to=course_file_path,
    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name='course_uploads',
    )
    display_name = models.CharField(
        _('visningsnavn'),
        blank=True,
        null=False,
        max_length=60,
        help_text=_('F.eks. "Kompendium"'),
    )
    order = models.PositiveSmallIntegerField(
        _('rekkefølge'),
        default=0,
        blank=False,
        null=False,
        help_text=_(
            'Bestemmer hvilken rekkefølge filene skal vises i. Lavest kommer '
            'først.'
        ),
    )

    @property
    def url(self) -> str:
        return self.file.url

    @property
    def filename(self) -> str:
        return basename(self.file.name)

    def check_access(self, user):
        return self in user.contributor.accessible_course_uploads()

    def __str__(self) -> str:
        if self.display_name:
            return self.display_name
        else:
            return self.filename


    class Meta:
        verbose_name = _('fil')
        verbose_name_plural = _('filer')
        ordering = ('order',)


class ResourceLinkList(LinkList):
    """
    Used to portray resource links which are common across all the semesters.
    Almost identical to Course, except for not being connected to any specific
    semester, but a study program instead, and not having a course code.
    """
    study_programs = models.ManyToManyField(
        StudyProgram,
        blank=True,
        related_name='_resource_link_lists',
        verbose_name=_('studieprogram')
    )
    default = models.BooleanField(
        default=False,
        verbose_name=_('standard ressurslenkeliste'),
        help_text=_('Skal denne ressurslenkelisten brukes i alle studieprogram som ikke har satt sine egendefinerte '
                    'ressurslenkelister?')
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        blank=False,
        null=False,
        verbose_name=_('Rekkefølge'),
        help_text=_('Bestemmer hvilken rekkefølge ressurslenkelistene skal vises i. Lavest kommer først.')
    )

    def check_access(self, user):
        return self in user.contributor.accessible_resource_link_lists()

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

    def check_access(self, user):
        return self in user.contributor.accessible_custom_link_categories()

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
    custom_category = models.ForeignKey(
        CustomLinkCategory,
        default=None,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('(Egendefinert kategori)'),
        help_text=_('Hvis du ønsker å bruke et egendefinert "mini-ikon".')
    )
    order = models.PositiveSmallIntegerField(
        _('rekkefølge'),
        default=0,
        blank=False,
        null=False,
        help_text=_('Bestemmer hvilken rekkefølge lenkene skal vises i. Lavest kommer først.')
    )

    def __str__(self):
        return self.title

    def clean(self):
        # Can't allow selection of both a category and a custom category at the
        # same time
        if self.category is not None and self.custom_category is not None:
            raise ValidationError(_('Kan ikke velge både en kateogri '
                                    'og en egendefinert kateogri for en lenke '
                                    'samtidig. Du kan kun velge én av delene, '
                                    'eller ingen av delene. Denne meldingen kan '
                                    'dukke opp når en administrator allerede har '
                                    'satt en kategori for denne lenken.'))

    class Meta:
        abstract = True
        ordering = ('order',)


class CourseLink(Link):
    """
    A link connected to a course, without the ability to add custom thumbnails.
    """
    title = SanitizedCharField(
        verbose_name=_('tittel'),
        allowed_tags=['em', 'strong', 'i', 'b'],
        max_length=100,
        strip=False,
        help_text=_('F.eks "Gamle eksamenssett"')
    )
    course = models.ForeignKey(
        Course,
        verbose_name=_('fag'),
        on_delete=models.CASCADE,
        related_name='links'
    )

    def check_access(self, user):
        return self in user.contributor.accessible_course_links()

    def __str__(self):
        return self.title + ' ('+ str(self.course.course_code) + ')'

    class Meta(Link.Meta):
        verbose_name = _('lenke')
        verbose_name_plural = _('lenker')


class ResourceLink(Link):
    """
    A link connected to one of the two ResourceLinkList elements displayed on
    each semesterpage, with the ability to add custom thumbnails.
    """
    title = SanitizedCharField(
        verbose_name=_('tittel'),
        allowed_tags=['em', 'strong', 'i', 'b'],
        max_length=100,
        strip=False,
        help_text=_('F.eks "Wolfram Alpha"')
    )
    resource_link_list = models.ForeignKey(
        ResourceLinkList,
        on_delete=models.CASCADE,
        related_name='links',
        verbose_name=_('ressurslenkeliste')
    )

    def check_access(self, user):
        return self in user.contributor.accessible_resource_links()


    def __str__(self):
        return self.title + ' (' + str(self.resource_link_list.full_name) + ')'


    class Meta(Link.Meta):
        verbose_name = _('ressurslenke')
        verbose_name_plural = _('ressurslenker')


NO_ACCESS = 0
COURSES = 1
SEMESTER = 2
MAIN_PROFILE = 3
STUDY_PROGRAM = 4
ACCESS_LEVELS = (
    (NO_ACCESS, _('Ingen tilgang')),
    (COURSES, _('Opprettede fag')),
    (SEMESTER, _('Kun semesteret')),
    (MAIN_PROFILE, _('Hele hovedprofilen')),
    (STUDY_PROGRAM, _('Hele studieprogrammet')),
)


class Contributor(models.Model):
    """
    A student contributor connected to a given semester, with a one-to-one relationship to the User model. Has an access_level
    field used to grant edit and delete permissions to Semesterpage models in the admin panel.
    All permissions relevant data goes into this model, while any user preference related data goes into Options.
    """
    user = models.OneToOneField(
        User,
        related_name='contributor',
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        verbose_name=_('bruker')
    )
    access_level = models.SmallIntegerField(
        _('tilgangsnivå'),
        choices=ACCESS_LEVELS,
        default=COURSES,
        help_text=_('Gir muligheten til å endre på lenker o.l. knyttet til semesteret spesifisert nedenfor.')
    )
    semester = models.ForeignKey(
        Semester,
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name='contributors',
        verbose_name=_('bidragsytersemester')
    )


    @property
    def study_program(self):
        try:
            return self.semester.study_program
        except AttributeError:
            # Contributor semester not set by the site administrator
            return StudyProgram.objects.none()

    @property
    def main_profile(self):
        try:
            return self.semester.main_profile
        except AttributeError:
            # Contributor semester not set by the site administrator
            return MainProfile.objects.none()

    """
    Methods for retrieving the model instances that should be accessible to the contributor.
    """
    def has_contributor_access_to(self, object):
        if self.user.is_superuser:
            return True
        else:
            # This check was the only way to fix a bug related to
            # CourseUploadInline for non superusers. The inline never appears
            # if this is not done. TODO: Find the reason why.
            if object is None:
                return True
            try:
                return object.check_access(self.user)
            except AttributeError:
                return False


    def accessible_study_programs(self):
        if self.access_level == STUDY_PROGRAM:
            return StudyProgram.objects.filter(pk=self.study_program.pk)
        else:
            return StudyProgram.objects.none()

    def accessible_main_profiles(self):
        if self.access_level == SEMESTER or self.access_level == COURSES:
            return MainProfile.objects.none()
        elif self.access_level == MAIN_PROFILE:
            return MainProfile.objects.filter(semesters__in=[self.semester])
        elif self.access_level == STUDY_PROGRAM:
            return self.study_program.main_profiles.all()
        else:
            raise RuntimeError('Invalid contributor access level.')

    def accessible_semesters(self):
        if self.access_level == SEMESTER:
            return Semester.objects.filter(pk=self.semester.pk)
        elif self.access_level == MAIN_PROFILE:
            return Semester.objects.filter(study_program=self.study_program, main_profile=self.main_profile)
        elif self.access_level == STUDY_PROGRAM:
            return self.study_program.semesters.all()
        elif self.access_level == COURSES:
            return Semester.objects.none()
        else:
            raise RuntimeError('Invalid contributor access level.')

    def accessible_courses(self):
        # If the user has access to a 'parent object', i.e. the related
        # semester, then we grant access to all children
        parent_access = Q(semesters__in=self.accessible_semesters())

        # Also includes courses where the contributor is part of the contributors ManyToManyField,
        # which the user is added to if he/she created the course
        earlier_contributor = Q(contributors__in=[self])
        access_criterion = parent_access | earlier_contributor

        # If the user has recently taken the course, according to dataporten,
        # we grant access. Here, recently means either the current semester,
        # or the last one
        if isinstance(self.user, DataportenUser):
            recent_course = Q(course_code__in=self.user.dataporten.courses.less_semesters_ago(than=2))
            access_criterion = access_criterion | recent_course

        return Course.objects.filter(access_criterion)

    def accessible_resource_link_lists(self):
        return ResourceLinkList.objects.filter(study_programs__in=self.accessible_study_programs())

    def accessible_custom_link_categories(self):
        return CustomLinkCategory.objects.filter(links__resource_link_list__study_programs__in=self.accessible_study_programs())

    def accessible_course_links(self):
        return CourseLink.objects.filter(course__in=self.accessible_courses())

    def accessible_course_uploads(self):
        return CourseUpload.objects.filter(course__in=self.accessible_courses())

    def accessible_resource_links(self):
        return ResourceLink.objects.filter(resource_link_list__study_programs__in=self.accessible_study_programs())

    def __str__(self):
        return str(self.user.options)

    class Meta:
        verbose_name = _('bidragsyter')
        verbose_name_plural = _('bidragsytere')


class Options(models.Model):
    """
    Fields that should be available to the student. It is important to notice that Options is a stand in for
    Semester in the template rendering of the userpage view, and thus needs many of the same methods and member
    variables
    """
    user = models.OneToOneField(
        User,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('bruker')
    )
    self_chosen_courses = models.ManyToManyField(
        Course,
        default=None,
        related_name='students',
        blank=True,
        verbose_name=_('fag'),
        help_text=_('Dette er fagene som vises på profilsiden din.'),
    )

    # The following dataporten field saves the last observed data from dataporten.
    # This is not intended for authentification, but rather for knowing when the
    # dataporten data has changed, such that 'self_chosen_courses' can be updated.
    # See .adapters.sync_options_of_user_with_dataporten
    active_dataporten_courses = models.ManyToManyField(
        Course,
        default=None,
        related_name='active_students',
        blank=True,
        verbose_name=_('dataporten fag'),
        help_text=_('Aktive fag fra dataporten'),
    )
    calendar_name = models.CharField(
        _('1024-kalendernavn'),
        max_length=60,
        blank=True,
        null=True,
        default=None,
        help_text=_('Tast inn ditt kalendernavn på ntnu.1024.no.')
    )

    @property
    def study_program(self):
        return StudyProgram.objects.get(slug=DEFAULT_STUDY_PROGRAM_SLUG)

    @property
    def main_profile(self):
        return MainProfile.objects.none()

    def get_archive_url(self):
        # Returns the link to the root of the archive site
        return subdomains.utils.reverse(
            'semesterpage-homepage',
            subdomain='arkiv',
        )

    @property
    def courses(self):
        """
        The courses that should be displayed to the user on their homepage.
        """
        return self.self_chosen_courses.all()

    def check_access(self, user):
        return self.user.username == user.username

    def get_admin_url(self):
        info = (self._meta.app_label, self._meta.model_name)
        return reverse('admin:%s_%s_change' % info, args=(self.pk,))

    def get_absolute_url(self):
        return reverse('semesterpage-studyprogram', args=(self.user.username,))

    def __str__(self):
        return self.user.username.title()

    class Meta(Link.Meta):
        verbose_name = _('instillinger')
        verbose_name_plural = _('instillinger')
        ordering = ('user__username',)
