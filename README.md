# A Link Portal for NTNU students [![Build Status](https://travis-ci.org/JakobGM/WikiLinks.svg?branch=master)](https://travis-ci.org/JakobGM/WikiLinks) [![Coverage Status](https://coveralls.io/repos/github/JakobGM/WikiLinks/badge.svg?branch=master)](https://coveralls.io/github/JakobGM/WikiLinks?branch=master)

A link portal written in Django. The site features:
- Responsive design using CSS flex box
- An admin dashboard for adding and editing links, courses, semesters, and so on
- Authentication using NTNU username and password, made possible by Dataporten
- Automatic retrieval of courses which the student is enrolled in

## Contributing
Run the following commands in order to set up the project locally

### Download the project
```
git clone https://github.com/JakobGM/django-kokekunster.git kokekunster
pip install -r requirements.txt
```

### Install a development database
Install Postgres.app from [here](http://postgresapp.com/). It is important to
add the command line utilities to your path.
Run `./manage.py migrate`.

### Load a production data dump
In the following instructions, `$USER` refers to your computer's username,
which can be found by writing `echo $USER` in your terminal.

Run `psql` and enter the `$USER` database. Run the following commands:
```
CREATE ROLE koku_user;
GRANT ALL PRIVILEGES ON DATABASE $USER TO koku_user;
```

Receive the db and media dump from @JakobGM and put them in the `tmp` folder
within the project folder. Run the following commands:
```
./manage.py dbrestore
./manage.py mediarestore
```

###
You can run the test suite like this:
```
py.test
```

And you can run CSS linting like so:
```
stylelint "**/*.css"
```

## Production:
### Necessary cronjob for automatic backups
```
SHELL=/bin/bash
*/5 * * * * source /home/jakobgm/kokekunster/koku_env/bin/activate && set -a && source /home/jakobgm/.pam_environment && set +a && /home/jakobgm/kokekunster/koku_env/bin/python /home/jakobgm/kokekunster/manage.py runcrons &> /home/jakobgm/kokekunster/backup.log
```
