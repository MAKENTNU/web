FROM python:3.11
ENV PYTHONUNBUFFERED 1
RUN apt update --fix-missing && apt install -y python3-dev libldap2-dev libsasl2-dev libssl-dev gettext libgettextpo-dev
RUN mkdir /web
WORKDIR /web
COPY requirements.txt /web/
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
