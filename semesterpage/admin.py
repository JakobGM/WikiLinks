from gettext import gettext as _

from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.shortcuts import redirect
from rules.contrib.admin import ObjectPermissionsModelAdmin

from semesterpage.models import (SEMESTER, Contributor, Course, CourseLink, CustomLinkCategory, MainProfile, Options,
                                 ResourceLink, ResourceLinkList, Semester, StudyProgram)


class MainProfileInline(admin.TabularInline):
    """
    MainProfile Inline in StudyProgramAdmin
    """
    model = MainProfile
    fields = ('full_name', 'display_name',)

class SemesterInline(admin.TabularInline):
    """
    Semester Inline in StudyProgramAdmin
    """
    model = Semester
    fields = ('number', 'main_profile', 'published',)

class StudyProgramAdmin(ObjectPermissionsModelAdmin):
    list_display = ('full_name', 'display_name',)
    exclude = ('has_archive',)
    inlines = (MainProfileInline, SemesterInline,)

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as specifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        if request.user.is_superuser:
            return super().get_queryset(request)
        else:
            return request.user.contributor.accessible_study_programs()


class CourseLinkInline(SortableInlineAdminMixin, admin.TabularInline):
    """
    Makes it possible to reorder the links when editing a specific course in
    the admin panel.
    This will change the order of the links in the admin panel, but it will
    also change the order in which the links are shown on the semesterpage.
    """
    model = CourseLink
    # Must include order here in order to prevent a 'required field' bug for empty links in the inline.
    # It is not shown in the admin panel anyhow due to the mixin.

    def get_fields(self, request, obj=None):
        fields = ('title', 'url', 'category', 'order',)
        if request.user.is_superuser:
            # Only show custom category field to superusers
            fields += ('custom_category',)
        return fields


class ResourceLinkInline(SortableInlineAdminMixin, admin.TabularInline):
    """
    See documentation for CourseLinkInline
    """
    model = ResourceLink
    # Must include order here in order to prevent a 'required field' bug for empty links in the inline.
    # It is not shown in the admin panel anyhow due to the mixin.
    fields = ('title', 'url', 'category', 'custom_category', 'order',)


class CourseAdmin(ObjectPermissionsModelAdmin):
    list_display = ('course_code', 'full_name', 'display_name',)
    list_filter = ('semesters',)
    search_fields = ('full_name', 'display_name', 'course_code',)
    filter_horizontal = ('semesters', 'contributors',)
    # Without this  'contributors' exclude, the save_model() method won't work properly,
    # that might be the case for created_by too, but that hasn't been tested yet
    inlines = [CourseLinkInline]

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as specifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        if request.user.is_superuser:
            return super().get_queryset(request)
        else:
            return request.user.contributor.accessible_courses()

    def get_fieldsets(self, request, obj=None):
        fields = ('display_name', 'homepage', 'safe_logo',)
        if request.user.contributor.access_level >= SEMESTER or request.user.is_superuser:
            # Only people with contributor access to semesters need to be able to select semesters on the course object
            fields += ('semesters',)
        if request.user.is_superuser:
            # SVG logos and contributors should only be changed by superusers
            fields += ('full_name', 'course_code', 'unsafe_logo', 'contributors', 'created_by', 'dataporten_uid',)
        return (
            (_('Fagdetaljer'), {
            'classes': ('collapse',),
            'fields': fields,
            }),
        )


    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Restrict the options available for the many-to-many field 'semesters' to model instances that the user should
        have access to. These model instances are found in the semesterpage.models.contributor model, which is related
        one-to-one to the User model (request.user.contributor).
        """
        if db_field.name == 'semesters':
            if not request.user.is_superuser:
                kwargs['queryset'] = request.user.contributor.accessible_semesters()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def response_change(self, request, obj):
        return redirect(obj.get_absolute_url())

    def has_delete_permission(self, request, obj=None):
        # Don't allow students to delete courses
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        obj.save()
        if change is False and not obj.semesters.exists():
            # The user has just created the Course for himself/herself,
            # and should be added as a contributor to that Course
            # For this to work, "exclude = ('contributors',)" must be set for some reason
            # TODO: The second test always evaluates as true
            obj.contributors.add(request.user.contributor.pk)
        if change is False:
            # Set creator without calling save() again by using update() instead
            Course.objects.filter(pk=obj.pk).update(created_by=request.user.contributor)


class ResourceLinkListAdmin(ObjectPermissionsModelAdmin):
    filter_horizontal = ('study_programs',)
    inlines = [ResourceLinkInline]

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as specifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        if request.user.is_superuser:
            return super().get_queryset(request)
        else:
            return request.user.contributor.accessible_resource_link_lists()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Restrict the options available for the many-to-many field 'study_programs' to model instances that the user
        should have access to. These model instances are found in the semesterpage.models.contributor model, which is
        related one-to-one to the User model (request.user.contributor).
        """
        if db_field.name == 'study_programs':
            if not request.user.is_superuser:
                kwargs['queryset'] = request.user.contributor.accessible_study_programs()
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class CustomLinkCategoryAdmin(ObjectPermissionsModelAdmin):
    list_display = ('name',)

    def get_queryset(self, request):
        """
        Restrict the displayed model instances in the admin view as specifically as possible based on the fields in
        semesterpage.models.contributor, which is related one-to-one to the User model.
        """
        if request.user.is_superuser:
            return super().get_queryset(request)
        else:
            return request.user.contributor.accessible_custom_link_categories()


# Define an inline admin descriptor for Contributor model
# which acts a bit like a singleton
class ContributorInline(admin.StackedInline):
    model = Contributor
    can_delete = False
    verbose_name_plural = _('bidragsyter')


class OptionsInline(admin.StackedInline):
    model = Options
    can_delete = False
    filter_horizontal = ('self_chosen_courses',)
    verbose_name_plural = _('instillinger')


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ContributorInline, OptionsInline,)


class OptionsAdmin(ObjectPermissionsModelAdmin):
    model = Options
    can_delete = False
    filter_horizontal = ('self_chosen_courses',)
    exclude = ('user', 'active_dataporten_courses',)

    def get_queryset(self, request):
        """
        Only show the user's own settings in the admin view
        """
        if request.user.is_superuser:
            return super().get_queryset(request)
        else:
            return Options.objects.filter(pk=request.user.options.pk)

    def response_change(self, request, obj):
        return redirect(obj.get_absolute_url())

    def has_delete_permission(self, request, obj=None):
        # Don't allow students to delete their own options model object
        return request.user.is_superuser


admin.site.register(StudyProgram, StudyProgramAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(ResourceLinkList, ResourceLinkListAdmin)
admin.site.register(CustomLinkCategory, CustomLinkCategoryAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Options, OptionsAdmin)
