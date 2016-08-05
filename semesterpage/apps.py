from django.apps import AppConfig
from gettext import gettext as _

class SemesterpageConfig(AppConfig):
    name = 'semesterpage'
    verbose_name = _('Semesterside')

    def ready(self):
        # Register signal listeners
        import semesterpage.signals.handlers  # noqa