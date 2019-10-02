# base image
FROM python:3.7-alpine3.9

# install dependencies
RUN apk update \
    apk add netcat-openbsd bash && \
    apk add --virtual build-deps gcc python-dev musl-dev && \
    apk add postgresql-dev && \
    apk add libxml2 libxml2-dev libxslt libxslt-dev jpeg jpeg-dev zlib poppler-utils

# set working directory
WORKDIR /usr/src/app

# add and install requirements
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# get some space back
RUN apk del build-deps

# add entrypoint.sh
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# add app
COPY . /usr/src/app

# run server
ENTRYPOINT ["/bin/sh", "/usr/src/app/entrypoint.sh"]
