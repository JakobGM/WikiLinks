from django.apps import AppConfig
from gettext import gettext as _
from .rules import create_contributor_groups


class SemesterpageConfig(AppConfig):
    name = 'semesterpage'
    verbose_name = _('Semesterside')

    def ready(self):
        # Register signal listeners
        import semesterpage.signals.handlers  # noqa

        # Create contributor groups at startup
        create_contributor_groups()