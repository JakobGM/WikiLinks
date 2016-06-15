from django.db import models

# Create your models here.
class StudyProgram(models.Model):
    full_name = models.CharField(max_length=30)                         # e.g. 'Fysikk og Matematikk'
    abbreviation = models.CharField(primary_key=True, max_length=10)    # e.g. 'MTFYMA'

    def __str__(self):
        return self.full_name + '(' + self.abbreviation + ')'

    class Meta:
        ordering = ['full_name']


class Semester(models.Model):
    number = models.PositiveSmallIntegerField()     # e.g. 2
    study_program = models.ForeignKey(StudyProgram)

    def __str__(self):
        return str(self.number) + '. semester'

    class Meta:
        ordering = ['number']


class Course(models.Model):
    full_name = models.CharField(max_length=50)         # e.g. 'Prosedyre- og Objektorientert Programmering'
    abbreviation = models.CharField(max_length=30)      # e.g. 'C++'
    semesters = models.ManyToManyField(Semester)
    logo = models.ImageField() # TODO: Need to add upload_to field
    homepage = models.URLField()

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']

class LinkCategory(models.Model):
    name = models.CharField(max_length=30)
    thumbnail = models.ImageField() # TODO: Need to add upload_to field

    class Meta:
        verbose_name_plural = "link categories"

class Link(models.Model):
    title = models.CharField(max_length=30)     # e.g. 'Gamle eksamenssett'
    url = models.URLField()                     # e.g. http://www.phys.ntnu.no/SomeCourse/OldExams.html
    category = models.ForeignKey(LinkCategory)  # e.g. 'Solutions' or 'Plan'
    course = models.ForeignKey(Course)
