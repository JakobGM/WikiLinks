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
git clone https://github.com/JakobGM/WikiLinks.git wikilinks
pip install -r requirements.txt
```

### Installing requirements

#### Tesseract and tesserocr

WikiLinks uses [tesserocr](https://github.com/sirfz/tesserocr) for character
recognition of PDF files. Follow the up-to-date instructions
[here](https://github.com/sirfz/tesserocr), which at the time of this writing
boils down to:

```
$ apt-get install tesseract-ocr libtesseract-dev libleptonica-dev
```

Take care that you install version 4 of tesseract, you can check the installed
version by running:

```
tesseract --version
```

If you had to upgrade tesseract to 4.0, you might have to reinstall tesserocr
without cache:

```
pip install --no-cache-dir tesserocr
```

Or else, you might get the following error message:

```
ImportError: libtesseract.so.3: cannot open shared object file:
No such file or directory
```

If python crashes on `import tesserocr` with the following error message:

```
!strcmp(locale, "C"):Error:Assert failed:in file baseapi.cpp, line 209
```

Set the following environment variables:

```
export LC_ALL=C
export PYTHONIOENCODING="UTF-8"
```

This issue is tracked [here](https://github.com/sirfz/tesserocr/issues/137).

#### Wand

WikiLinks must also convert `.pdf` files to `.tiff` files before passing them
on to `tesserocr`. The [Wand](http://docs.wand-py.org/en) python package is
used for this purpose, and also requires some additional dependencies.
Read installation instructions
[here](http://docs.wand-py.org/en/0.4.5/guide/install.html).

As of this writing this entails:

```
$ sudo apt-get install libmagickwand-dev  # debian/ubuntu
$ brew install imagemagick                # MacOS
```

If you get the following exception:

```
wand.exceptions.PolicyError:
attempt to perform an operation not allowed by the security policy
`PDF' @ error/constitute.c/IsCoderAuthorized/408
```

Then you need to tweak an ImageMagick policy.
See instructions [here](https://askubuntu.com/a/1081907).


#### pdftotext

Lastly, you must install the dependencies of
[pdftotext](https://github.com/jalan/pdftotext). This utility extracts text
from PDFs that already contain text overlay information, so no OCR is needed.
See instructions [here](https://github.com/jalan/pdftotext#os-dependencies).


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
