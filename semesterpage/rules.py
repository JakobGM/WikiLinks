"""
Custom object instance based permissions with django-rules
"""
from rules import predicate, add_perm, is_superuser

@predicate
def has_contributor_access(user, object):
    return user.contributor.has_contributor_access_to(object)

contributor_models = ['studyprogram', 'mainprofile',
                      'semester', 'course',
                      'resourcelinklist', 'customlinkcategory',
                      'courselink', 'resourcelink',
                      'options']

for model in contributor_models:
    add_perm('semesterpage.change_' + model, has_contributor_access)
    add_perm('semesterpage.delete_' + model, has_contributor_access)

add_perm('semesterpage.change_contributor', is_superuser)
add_perm('semesterpage.delete_contributor', is_superuser)

def create_contributor_groups():
    """
    Add the three permission level groups related to contributors. Is invoked by the AppConfig.ready() method.
    """
    # Important to import here to ensure that all apps have been loaded on invocation
    from django.contrib.auth.models import Group, Permission

    students, created = Group.objects.get_or_create(name='students')
    if created:
        students.permissions = [
            Permission.objects.get(codename='change_options'),
        ]

    course_contributors, created = Group.objects.get_or_create(name='course_contributors')
    if created:
        course_contributors.permissions = [
            Permission.objects.get(codename='add_course'),
            Permission.objects.get(codename='change_course'),
            Permission.objects.get(codename='delete_course'),
            Permission.objects.get(codename='add_courselink'),
            Permission.objects.get(codename='change_courselink'),
            Permission.objects.get(codename='delete_courselink'),
        ]

    # In case of semester-level specific permissions in the future
    semester_contributors, created = Group.objects.get_or_create(name='semester_contributors')
    if created:
        semester_contributors.permissions = []

    mainprofile_contributors, created = Group.objects.get_or_create(name='mainprofile_contributors')
    if created:
        mainprofile_contributors.permissions = [
            Permission.objects.get(codename='change_mainprofile'),
            Permission.objects.get(codename='add_mainprofile'),
            Permission.objects.get(codename='add_semester'),
            Permission.objects.get(codename='change_semester'),
            Permission.objects.get(codename='delete_semester')
        ]

    studyprogram_contributors, created = Group.objects.get_or_create(name='studyprogram_contributors')
    if created:
        studyprogram_contributors.permissions = [
            Permission.objects.get(codename='change_studyprogram'),
            Permission.objects.get(codename='add_mainprofile'),
            Permission.objects.get(codename='delete_mainprofile'),
            Permission.objects.get(codename='change_course'),
            Permission.objects.get(codename='delete_course'),
            Permission.objects.get(codename='add_resourcelinklist'),
            Permission.objects.get(codename='change_resourcelinklist'),
            Permission.objects.get(codename='add_customlinkcategory'),
            Permission.objects.get(codename='delete_resourcelinklist'),
            Permission.objects.get(codename='add_resourcelink'),
            Permission.objects.get(codename='change_resourcelink'),
            Permission.objects.get(codename='delete_resourcelink')
        ]