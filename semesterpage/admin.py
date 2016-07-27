from django.contrib import admin
from adminsortable2.admin import SortableInlineAdminMixin
from .models import StudyProgram, MainProfile, Semester, Course, \
                    ResourceLinkList, CourseLink, ResourceLink, \
                    CustomLinkCategory, Contributor

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


class StudyProgramAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'display_name',)

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as spesifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        qs = super(StudyProgramAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(pk=request.user.contributor.study_program.pk)


class MainProfileAdmin(admin.ModelAdmin):
    list_filter = ('study_program',)

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as spesifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        qs = super(MainProfileAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.contributor.main_profile is not None:
            return qs.filter(pk=request.user.contributor.main_profile.pk)
        else:
            return qs.filter(study_program=request.user.contributor.study_program)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Restrict the options available for the foreign key field 'study_program' to model instances that the user should
        have access to. These model instances are found in the semesterpage.models.contributor model, which is related
        one-to-one to the User model (request.user.contributor).
        """
        if not request.user.is_superuser:
            if db_field.name == 'study_program':
                kwargs['queryset'] = StudyProgram.objects.filter(pk=request.user.contributor.study_program.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SemesterAdmin(admin.ModelAdmin):
    list_filter = ('study_program',)

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as spesifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        qs = super(SemesterAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.contributor.semester is not None:
            return qs.filter(pk=request.user.contributor.semester.pk)
        elif request.user.contributor.main_profile is not None:
            return qs.filter(main_profile=request.user.contributor.main_profile)
        else:
            return qs.filter(study_program=request.user.contributor.study_program)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Restrict the options available for the foreign key fields 'study_program' and 'main_profile' to model instances
        that the user should have access to. These model instances are found in the semesterpage.models.contributor
        model, which is related one-to-one to the User model (request.user.contributor).
        """
        if not request.user.is_superuser:
            if db_field.name == 'study_program':
                kwargs['queryset'] = StudyProgram.objects.filter(pk=request.user.contributor.study_program.pk)
            if db_field.name == 'main_profile':
                kwargs['queryset'] = request.user.contributor.main_profiles()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as spesifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        qs = super(CourseAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.contributor.semester is not None:
            return qs.filter(semesters__in=[request.user.contributor.semester])
        elif request.user.contributor.main_profile is not None:
            return qs.filter(semesters__main_profile__in=[request.user.contributor.main_profile])
        else:
            return qs.filter(semesters__study_program__in=[request.user.contributor.study_program])

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Restrict the options available for the many-to-many field 'semesters' to model instances that the user should
        have access to. These model instances are found in the semesterpage.models.contributor model, which is related
        one-to-one to the User model (request.user.contributor).
        """
        if db_field.name == 'semesters':
            if not request.user.is_superuser:
                kwargs['queryset'] = request.user.contributor.semesters()
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class ResourceLinkListAdmin(admin.ModelAdmin):
    filter_horizontal = ('study_programs',)
    inlines = [ResourceLinkInline]

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as spesifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        qs = super(ResourceLinkListAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.contributor.semester is not None:
            return qs.filter(study_programs__in=[request.user.contributor.semester.study_program])
        elif request.user.contributor.main_profile is not None:
            return qs.filter(study_programs__in=[request.user.contributor.main_profile.study_program])
        else:
            return qs.filter(study_programs__in=[request.user.contributor.study_program])

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Restrict the options available for the many-to-many field 'study_programs' to model instances that the user
        should have access to. These model instances are found in the semesterpage.models.contributor model, which is
        related one-to-one to the User model (request.user.contributor).
        """
        if db_field.name == 'study_programs':
            if not request.user.is_superuser:
                kwargs['queryset'] = StudyProgram.objects.filter(pk=request.user.contributor.study_program.pk)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class CourseLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'course', 'category',)
    list_filter = ('course',)
    search_fields = ('title', 'url', 'course',)
    exclude = ('order',)

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as spesifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        qs = super(CourseLinkAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.contributor.semester is not None:
            return qs.filter(course__semesters__in=[request.user.contributor.semester])
        elif request.user.contributor.main_profile is not None:
            return qs.filter(course__semesters__main_profile__in=[request.user.contributor.main_profile])
        else:
            return qs.filter(course__semesters__study_program__in=[request.user.contributor.study_program])

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Restrict the options available for the foreign key field 'course' to model instances that the user should
        have access to. These model instances are found in the semesterpage.models.contributor model, which is related
        one-to-one to the User model (request.user.contributor).
        """
        if not request.user.is_superuser:
            if db_field.name == 'course':
                kwargs['queryset'] = request.user.contributor.courses()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ResourceLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'resource_link_list', 'category', 'custom_category',)
    list_filter = ('resource_link_list',)
    search_fields = ('title', 'url', 'resource_link_list',)
    exclude = ('order',)

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as spesifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        qs = super(ResourceLinkAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.contributor.semester is not None:
            return qs.filter(resource_link_list__study_programs__in=[request.user.contributor.semester.study_program])
        elif request.user.contributor.main_profile is not None:
            return qs.filter(resource_link_list__study_programs__in=[request.user.contributor.main_profile.study_program])
        else:
            return qs.filter(resource_link_list__study_programs__in=[request.user.contributor.study_program])

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Restrict the options available for the foreign key field 'resource_link_list' to model instances that the user should
        have access to. These model instances are found in the semesterpage.models.contributor model, which is related
        one-to-one to the User model (request.user.contributor).
        """
        if not request.user.is_superuser:
            if db_field.name == 'resource_link_list':
                kwargs['queryset'] = request.user.contributor.study_program.resource_link_lists
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CustomLinkCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


# Define an inline admin descriptor for Contributor model
# which acts a bit like a singleton
class ContributorInline(admin.StackedInline):
    model = Contributor
    can_delete = False
    verbose_name_plural = 'contributor'


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ContributorInline,)


admin.site.register(StudyProgram, StudyProgramAdmin)
admin.site.register(MainProfile, MainProfileAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(ResourceLinkList, ResourceLinkListAdmin)
admin.site.register(CourseLink, CourseLinkAdmin)
admin.site.register(ResourceLink, ResourceLinkAdmin)
admin.site.register(CustomLinkCategory, CustomLinkCategoryAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)