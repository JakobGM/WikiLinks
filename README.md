# Development postgresql
Install Postgres.app from [here](http://postgresapp.com/). It is important to
add the command line utilities to your path.
Run `./manage.py migrate`.

# Production data dump
Run `psql` and enter the `$USER` database. Run the following commands:
```
CREATE ROLE koku_user;
GRANT ALL PRIVILEGES ON DATABASE jakobgm TO koku_user;
```

Receive the db and media dump from @JakobGM and put them in the /tmp folder.
Run the following commands, but with correct filenames.
```
./manage.py dbrestore -i koku_db-cobalt.kokekunster.no-2017-06-07-010002.psql.0
./manage.py mediarestore -i cobalt.kokekunster.no-2017-06-07-010004.tar.gz.0
```
# Cronjob:
```
SHELL=/bin/bash
*/5 * * * * source /home/jakobgm/kokekunster/koku_env/bin/activate && set -a && source /home/jakobgm/.pam_environment && set +a && /home/jakobgm/kokekunster/koku_env/bin/python /home/jakobgm/kokekunster/manage.py runcrons &> /home/jakobgm/kokekunster/backup.log
```
