# base image
FROM python:3.9-slim

ENV TZ=Europe/Brussels

# install dependencies
RUN apt-get -qq update && \
    apt-get -y -qq upgrade && \
    apt-get -y -qq install netcat-openbsd bash && \
    apt-get -y -qq install gcc python-dev build-essential && \
#    apt-get -y -qq install postgresql-dev && \
    apt-get -y -qq install libxml2 libxml2-dev libxslt1.1 libxslt1-dev libjpeg-dev zlibc poppler-utils && \
    apt-get -y -qq install locales-all

# set working directory
WORKDIR /usr/src/app

# add and install requirements
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# get some space back
#RUN apk del build-deps
RUN apt-get -y -qq autoremove gcc python-dev build-essential

# add entrypoint.sh
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# add app
COPY . /usr/src/app

# run server
ENTRYPOINT ["/bin/bash", "/usr/src/app/entrypoint.sh"]
