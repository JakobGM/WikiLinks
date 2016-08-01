from django.apps import AppConfig
from gettext import gettext as _
from .rules import create_contributor_groups
from .adminstyle import set_admin_theme


class SemesterpageConfig(AppConfig):
    name = 'semesterpage'
    verbose_name = _('Semesterside')

    def ready(self):
        # Register signal listeners
        import semesterpage.signals.handlers  # noqa

        # Create contributor groups at startup
        create_contributor_groups()

        # Style the admin utility according to the kokekunster style
        set_admin_theme()