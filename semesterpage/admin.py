from django.contrib import admin
from adminsortable2.admin import SortableInlineAdminMixin
from .models import StudyProgram, MainProfile, Semester, Course, Link, LinkCategory


class StudyProgramAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'display_name', 'program_code',)


class MainProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'display_name',)
    list_filter = ('study_program',)


class SemesterAdmin(admin.ModelAdmin):
    list_filter = ('study_program',)


class LinkInline(SortableInlineAdminMixin, admin.TabularInline):
    """
    Makes it possible to reorder the links when editing a specific course in
    the admin panel.
    This will change the order of the links in the admin panel, but it will
    also change the order in which the links are shown on the semesterpage.
    """
    model = Link


class CourseAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'display_name', 'course_code',)
    list_filter = ('semesters',)
    search_fields = ('full_name', 'display_name', 'program_code',)
    filter_horizontal = ('semesters',)
    inlines = [LinkInline]


class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'course', 'category',)
    list_filter = ('course',)
    search_fields = ('title', 'url', 'course',)
    exclude = ('order',)


class LinkCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(StudyProgram, StudyProgramAdmin)
admin.site.register(MainProfile, MainProfileAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(LinkCategory, LinkCategoryAdmin)
