"""
Custom object instance based permissions with django-rules
"""
from rules import add_perm, is_superuser, predicate

from dataporten.models import DataportenUser


@predicate
def has_contributor_access(user, object):
    return user.is_authenticated \
            and user.contributor.has_contributor_access_to(object)

contributor_models = [
        'course',
        'courseupload',
        'courselink',
        'customlinkcategory',
        'mainprofile',
        'options',
        'resourcelink',
        'resourcelinklist',
        'semester',
        'studyprogram',
]

for model in contributor_models:
    add_perm('semesterpage.change_' + model, has_contributor_access)
    add_perm('semesterpage.delete_' + model, has_contributor_access)

add_perm('semesterpage.change_contributor', is_superuser)
add_perm('semesterpage.delete_contributor', is_superuser)

# We need to enable users to _add_ new course upload files
add_perm('semesterpage.add_courseupload', has_contributor_access)
