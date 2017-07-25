from django.conf import settings
from django.core import management
from django_cron import CronJobBase, Schedule


class Backup(CronJobBase):
    '''
    Run the django-dbbackup module every night at 03:00, saving the entire
    datase and all media to Dropbox
    '''
    RUN_AT_TIMES = getattr(settings, 'BACKUP_TIMES', ['3:00',])
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'kokekunster.db_backup_cron'  # Unique identifier

    def do(self):
        management.call_command('dbbackup')
        management.call_command('mediabackup')
