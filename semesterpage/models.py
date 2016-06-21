from django.db import models

from gettext import gettext as _


class StudyProgram(models.Model):
    """
    Contains top level information for a specific study program.
    """
    full_name = models.CharField(_('fullt navn'),
                                 max_length=60,
                                 help_text=_('F.eks. \"Fysikk og matematikk\"')
                                 )
    display_name = models.CharField(_('visningsnavn / kallenavn'),
                                    max_length=60,
                                    help_text=_('F.eks. \"Fysmat\"')
                                    )
    program_code = models.CharField(_('programkode'),
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
    full_name = models.CharField(_('fullt navn'),
                                 max_length=60,
                                 default=_('felles'),
                                 help_text=_('F.eks. \"Industriell matematikk\"')
                                 )
    display_name = models.CharField(_('visningsnavn / kallenavn'),
                                    max_length=60,
                                    default=_('Felles'),
                                    help_text=_('F.eks. \"InMat\"')
                                    )
    study_program = models.ForeignKey(StudyProgram,
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
    number = models.PositiveSmallIntegerField(_('semester (nummer)'),
                                              help_text='F.eks. \"2\"'
                                              )
    study_program = models.ForeignKey(StudyProgram,
                                      related_name='semesters'
                                      )
    main_profile = models.ForeignKey(MainProfile,
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
    full_name = models.CharField(_('fullt navn'),
                                 unique=True,
                                 max_length=60,
                                 help_text=_('F.eks. \"Prosedyre- og Objektorientert Programmering\"')
                                 )
    display_name = models.CharField(_('visningsnavn'),
                                    max_length=60,
                                    help_text=_('F.eks. \"C++\"')
                                    )
    course_code = models.CharField('emnekode',
                                   primary_key=True,
                                   max_length=10,
                                   help_text=_('F.eks. \"TDT4102\"')
                                   )
    semesters = models.ManyToManyField(Semester,
                                       related_name='courses'
                                       )
    logo = models.ImageField(upload_to='semesterpage/static/semesterpage/courses')
    homepage = models.URLField(_('Fagets hjemmeside'),
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
    name = models.CharField(_('kategorinavn'),
                            primary_key=True,
                            max_length=60
                            )
    thumbnail = models.ImageField(_('ikon for kategori'),
                                  upload_to='semesterpage/static/semesterpage/link_categories',
                                  blank=True
                                  )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('lenkekategori')
        verbose_name_plural = _('lenkekategorier')


class Link(models.Model):
    """
    Contains a URL link connected to a specific course.
    """
    title = models.CharField(_('tittel'),
                             max_length=60,
                             help_text=_('F.eks \"Gamle eksamenssett\"')
                             )
    url = models.URLField('URL',
                          help_text=_('F.eks. \"http://www.phys.ntnu.no/fysikkfag/gamleeksamener.html\"')
                          )
    category = models.ForeignKey(LinkCategory)  # e.g. 'Solutions' or 'Plan'
    course = models.ForeignKey(Course,related_name='links')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('lenke')
        verbose_name_plural = _('lenker')
