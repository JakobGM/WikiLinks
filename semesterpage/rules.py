"""
Custom object instance based permissions with django-rules
"""
from rules import predicate, add_perm, is_superuser

@predicate
def has_contributor_access(user, object):
    return user.student.has_contributor_access_to(object)

contributor_models = ['studyprogram', 'mainprofile',
                      'semester', 'course',
                      'resourcelinklist', 'customlinkcategory',
                      'courselink', 'resourcelink']

for model in contributor_models:
    add_perm('semesterpage.change_' + model, has_contributor_access)
    add_perm('semesterpage.delete_' + model, has_contributor_access)

add_perm('semesterpage.change_contributor', is_superuser)
add_perm('semesterpage.delete_contributor', is_superuser)

