from django.apps import AppConfig


class ExaminerConfig(AppConfig):
    name = 'examiner'

    def ready(self):
        import examiner.signals.handlers  # noqa
