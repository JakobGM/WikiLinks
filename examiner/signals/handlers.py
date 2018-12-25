from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from examiner.models import Pdf


@receiver(pre_delete, sender=Pdf, dispatch_uid='delete_backed_up_pdf')
def delete_pdf_backup_on_deletion(sender, instance, **kwargs):
    """Delete Pdf on disk when Pdf model object is deleted."""
    instance.file.delete(save=False)
