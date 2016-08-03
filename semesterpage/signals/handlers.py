from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from semesterpage.models import Student, Options


@receiver(post_save, sender=User)
def user_save(sender, instance, created, raw, **kwargs):
    if raw:
        # Fixtures needs to be ignored
        return
    elif created:
        # Add staff status to have access to admin
        User.objects.filter(pk=instance.pk).update(is_staff=True)
        # Add to basic student permission group
        Group.objects.get(name='students').user_set.add(instance)
        # Create the one-to-one instances related to User
        Student.objects.create(user=instance)
        Options.objects.create(user=instance)
    elif not created:
        set_groups(instance)


@receiver(post_save, sender=Student)
def contributor_save(sender, instance, created, raw, **kwargs):
    # This signal is probably never sent as there is no Student object registered in the admin,
    # but is left here in case Student instances are altered directly in the code in the future
    if not created and not raw:
        set_groups(instance.user)


def set_groups(user):
    """
    Sets the necessary contributor groups according to the users access level
    """
    try:
        user.student
    except ObjectDoesNotExist:
        # Incase student has not been created yet, although user_save() should handle that
        return

    students = Group.objects.get(name='students')
    course_contributors = Group.objects.get(name='course_contributors')
    semester_contributors = Group.objects.get(name='semester_contributors')
    mainprofile_contributors = Group.objects.get(name='mainprofile_contributors')
    studyprogram_contributors = Group.objects.get(name='studyprogram_contributors')

    contributor_groups = [students, course_contributors, semester_contributors,
                          mainprofile_contributors, studyprogram_contributors]

    # Set the groups of the contributor according to his/hers access level
    for group in contributor_groups[:user.student.access_level+1]:
        group.user_set.add(user)
    for group in contributor_groups[user.student.access_level+1:]:
        group.user_set.remove(user)