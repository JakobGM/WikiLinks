from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from semesterpage.models import Student, NO_ACCESS

@receiver(pre_save, sender=Student)
def contributor_save(sender, instance, **kwargs):
    # Get relevant contributor groups and assemble them in a list
    semester_contributors = Group.objects.get(name='semester_contributors')
    mainprofile_contributors = Group.objects.get(name='mainprofile_contributors')
    studyprogram_contributors = Group.objects.get(name='studyprogram_contributors')

    contributor_groups = [semester_contributors, mainprofile_contributors, studyprogram_contributors]

    # Set the groups of the contributor according to his/hers access level
    instance.user.groups = contributor_groups[:instance.access_level]

    # Set staff status if the user has contributor access
    if instance.access_level is not NO_ACCESS and not instance.user.is_staff:
        instance.user.is_staff = True
        # Save the user instance, because this is pre-save of the Student model, and not the User model
        instance.user.save()
    elif instance.access_level is NO_ACCESS and not instance.user.is_superuser:
        instance.user.is_staff = False
        instance.user.save()
