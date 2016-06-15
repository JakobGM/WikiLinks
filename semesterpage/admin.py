from django.contrib import admin
from .models import StudyProgram, Semester, Course, Link, LinkCategory

class StudyProgramAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'nickname', 'program_code',)

class SemesterAdmin(admin.ModelAdmin):
    list_filter = ('study_program',)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'nickname', 'course_code',)
    list_filter = ('semesters',)
    search_fields = ('full_name', 'nickname', 'program_code',)
    filter_horizontal = ('semesters',)

class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'course', 'category',)
    list_filter = ('course',)
    search_fields = ('title', 'url', 'course',)

class LinkCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(StudyProgram, StudyProgramAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(LinkCategory, LinkCategoryAdmin)
