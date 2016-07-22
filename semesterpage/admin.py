from django.contrib import admin
from adminsortable2.admin import SortableInlineAdminMixin
from .models import StudyProgram, MainProfile, Semester, Course, \
                    ResourceLinkList, CourseLink, ResourceLink, \
                    CustomLinkCategory


class StudyProgramAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'display_name',)


class MainProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'display_name',)
    list_filter = ('study_program',)


class SemesterAdmin(admin.ModelAdmin):
    list_filter = ('study_program',)


class CourseLinkInline(SortableInlineAdminMixin, admin.TabularInline):
    """
    Makes it possible to reorder the links when editing a specific course in
    the admin panel.
    This will change the order of the links in the admin panel, but it will
    also change the order in which the links are shown on the semesterpage.
    """
    model = CourseLink


class ResourceLinkInline(SortableInlineAdminMixin, admin.TabularInline):
    """
    See documentation for CourseLinkInline
    """
    model = ResourceLink


class CourseAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'display_name', 'course_code',)
    list_filter = ('semesters',)
    search_fields = ('full_name', 'display_name',)
    filter_horizontal = ('semesters',)
    inlines = [CourseLinkInline]


class ResourceLinkListAdmin(admin.ModelAdmin):
    inlines = [ResourceLinkInline]


class CourseLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'course', 'category',)
    list_filter = ('course',)
    search_fields = ('title', 'url', 'course',)
    exclude = ('order',)


class ResourceLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'resource_link_list', 'category', 'custom_category',)
    list_filter = ('resource_link_list',)
    search_fields = ('title', 'url', 'resource_link_list',)
    exclude = ('order',)


class CustomLinkCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(StudyProgram, StudyProgramAdmin)
admin.site.register(MainProfile, MainProfileAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(ResourceLinkList, ResourceLinkListAdmin)
admin.site.register(CourseLink, CourseLinkAdmin)
admin.site.register(ResourceLink, ResourceLinkAdmin)
admin.site.register(CustomLinkCategory, CustomLinkCategoryAdmin)
