from django.db import models


class StudyProgram(models.Model):
    full_name = models.CharField('fullt navn',
                                 max_length=30,
                                 help_text='F.eks. \"Fysikk og matematikk\"'
                                 )
    display_name = models.CharField('visningsnavn / kallenavn',
                                    max_length=30,
                                    help_text='F.eks. \"Fysmat\"'
                                    )
    program_code = models.CharField('programkode',
                                    primary_key=True,
                                    max_length=10,
                                    help_text='F.eks. \"MTFYMA\"'
                                    )  # TODO: Only upper case?

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['full_name']


class MainProfile(models.Model):
    full_name = models.CharField('fullt navn',
                                 max_length=40,
                                 default='felles',
                                 help_text='F.eks. \"Industriell matematikk\"'
                                 )
    display_name = models.CharField('visningsnavn / kallenavn',
                                    max_length=30,
                                    default='Felles',
                                    help_text='F.eks. \"InMat\"'
                                    )
    study_program = models.ForeignKey(StudyProgram,
                                      related_name='mainProfiles'
                                      )

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']
        verbose_name_plural = 'main profiles'


class Semester(models.Model):
    number = models.PositiveSmallIntegerField('semester (nummer)',
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


class Course(models.Model):
    full_name = models.CharField('fullt navn',
                                 unique=True,
                                 max_length=50,
                                 help_text='F.eks. \"Prosedyre- og Objektorientert Programmering\"'
                                 )
    display_name = models.CharField('visningsnavn',
                                    max_length=30,
                                    help_text='F.eks. \"C++\"'
                                    )
    course_code = models.CharField('emnekode',
                                   primary_key=True,
                                   max_length=10,
                                   help_text='F.eks. \"TDT4102\"'
                                   )
    semesters = models.ManyToManyField(Semester,
                                       related_name='courses'
                                       )
    logo = models.ImageField(upload_to='semesterpage/static/semesterpage/courses')
    homepage = models.URLField('Fagets hjemmeside',
                               help_text='F.eks. \"http://home.phys.ntnu.no/fysikkfag/eksamensoppgaver\"'
                               )

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']


class LinkCategory(models.Model):
    name = models.CharField('kategorinavn',
                            primary_key=True,
                            max_length=30
                            )
    thumbnail = models.ImageField('ikon for kategori',
                                  upload_to='semesterpage/static/semesterpage/link_categories',
                                  blank=True
                                  )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'link categories'


class Link(models.Model):
    title = models.CharField('tittel',
                             max_length=30,
                             help_text='F.eks \"Gamle eksamenssett\"'
                             )
    url = models.URLField('URL',
                          help_text='F.eks. \"http://www.phys.ntnu.no/fysikkfag/gamleeksamener.html\"'
                          )
    category = models.ForeignKey(LinkCategory)  # e.g. 'Solutions' or 'Plan'
    course = models.ForeignKey(Course,related_name='links')

    def __str__(self):
        return self.title
