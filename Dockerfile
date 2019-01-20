FROM inetsoftware/alpine-tesseract as builder
# ^ Container used to install tesseract from

# Python 3.6 in a lightweight linux environment
FROM python:3.6-alpine

# Proper python STDOUT behaviour in docker
ENV PYTHONUNBUFFERED 1

# Required for tesseract compilation and use
ENV LC_ALL C

# Copy tesseract v4.0 package from the builder
# See: https://hub.docker.com/r/inetsoftware/alpine-tesseract/
COPY --from=builder /tesseract/tesseract-git-* /tesseract/

# Install this version of tesseract
RUN set -x \
    && echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories \
    && apk add --update --allow-untrusted /tesseract/tesseract-git-* \
    && rm  -rf /tesseract \
    && echo "done"

# Required for pdftotext
RUN apk add --no-cache \
    poppler \
    poppler-dev \
    poppler-utils

# Required for pillow
RUN apk add --no-cache build-base jpeg-dev zlib-dev

# Required for psycopg2
RUN apk add --no-cache postgresql postgresql-dev

# Create working directory for application code
RUN mkdir /code
WORKDIR /code

# First only copy python requirements to prevent cache invalidation
COPY ./requirements.txt /code/requirements.txt

# Install all python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into container
COPY . /code/

# Expose port 8000 for gunicorn server
EXPOSE 8000

# Prepare and startup django gunicorn server
CMD ["./config/django/docker-entrypoint.sh"]
