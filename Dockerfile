FROM python:2.7

RUN apt-get update && apt-get -y install vim
RUN apt-get install -y gettext

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements /usr/src/app/requirements
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements/local.txt

COPY . /usr/src/app/
