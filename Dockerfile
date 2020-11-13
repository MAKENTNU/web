FROM python:3
ENV PYTHONUNBUFFERED 1
RUN apt-get update --fix-missing && apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev gettext libgettextpo-dev
RUN mkdir /web
WORKDIR /web
COPY requirements.txt /web/
RUN pip install -r requirements.txt
