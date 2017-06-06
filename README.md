Cronjob:
```
SHELL=/bin/bash
*/5 * * * * source /home/jakobgm/kokekunster/koku_env/bin/activate && set -a && source /home/jakobgm/.pam_environment && set +a && /home/jakobgm/kokekunster/koku_env/bin/python /home/jakobgm/kokekunster/manage.py runcrons &> /home/jakobgm/kokekunster/backup.log
```
