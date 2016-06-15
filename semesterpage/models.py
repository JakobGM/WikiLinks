from django.db import models

class StudyProgram(models.Model):
    full_name = models.CharField(max_length=30)                         # e.g. 'Fysikk og Matematikk'
    nickname = models.CharField(max_length=30)                          # e.g. 'Fysmat'
    program_code = models.CharField(primary_key=True, max_length=10)     # e.g. 'MTFYMA'

    def __str__(self):
        return self.nickname

    class Meta:
        ordering = ['full_name']


class Semester(models.Model):
    number = models.PositiveSmallIntegerField()     # e.g. 2
    study_program = models.ForeignKey(StudyProgram)

    def __str__(self):
        return str(self.study_program) + " (" + str(self.number) + '. semester)'

    class Meta:
        ordering = ['number']


class Course(models.Model):
    full_name = models.CharField(max_length=50)         # e.g. 'Prosedyre- og Objektorientert Programmering'
    nickname = models.CharField(max_length=30)          # e.g. 'C++'
    course_code = models.CharField(max_length=10)       # e.g. 'TDT4102'
    semesters = models.ManyToManyField(Semester)
    logo = models.ImageField(upload_to='static/courses') 
    homepage = models.URLField()

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']


class LinkCategory(models.Model):
    name = models.CharField(max_length=30)
    thumbnail = models.ImageField(upload_to='static/link_categories')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "link categories"


class Link(models.Model):
    title = models.CharField(max_length=30)     # e.g. 'Gamle eksamenssett'
    url = models.URLField()                     # e.g. http://www.phys.ntnu.no/SomeCourse/OldExams.html
    category = models.ForeignKey(LinkCategory)  # e.g. 'Solutions' or 'Plan'
    course = models.ForeignKey(Course)

    def __str__(self):
        return self.title
