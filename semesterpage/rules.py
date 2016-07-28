"""
Custom object instance based permissions with django-rules
"""
from rules import predicate, add_perm, is_superuser

@predicate
def has_contributor_access(user, object):
    return user.student.has_contributor_access_to(object)

# Can the following be made more dry somehow? Perhaps a for-loop?
# But that would perhaps make it needlessly obscure...
add_perm('semesterpage.change_studyprogram', has_contributor_access)
add_perm('semesterpage.delete_studyprogram', has_contributor_access)

add_perm('semesterpage.change_mainprofile', has_contributor_access)
add_perm('semesterpage.delete_mainprofile', has_contributor_access)

add_perm('semesterpage.change_semester', has_contributor_access)
add_perm('semesterpage.delete_semester', has_contributor_access)

add_perm('semesterpage.change_course', has_contributor_access)
add_perm('semesterpage.delete_course', has_contributor_access)

add_perm('semesterpage.change_resourcelinklist', has_contributor_access)
add_perm('semesterpage.delete_resourcelinklist', has_contributor_access)

add_perm('semesterpage.change_customlinkcategory', has_contributor_access)
add_perm('semesterpage.delete_customlinkcategory', has_contributor_access)

add_perm('semesterpage.change_courselink', has_contributor_access)
add_perm('semesterpage.delete_courselink', has_contributor_access)

add_perm('semesterpage.change_resourcelink', has_contributor_access)
add_perm('semesterpage.delete_resourcelink', has_contributor_access)

add_perm('semesterpage.change_contributor', is_superuser)
add_perm('semesterpage.delete_contributor', is_superuser)

