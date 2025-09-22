FROM python:3.11
ENV PYTHONUNBUFFERED 1
RUN apt update --fix-missing && apt install -y python3-dev libldap2-dev libsasl2-dev libssl-dev gettext libgettextpo-dev
RUN python -m pip install --upgrade pip
RUN pipx install uv
RUN mkdir /web
WORKDIR /web
COPY pyproject.toml uv.lock /web/
RUN uv sync --locked
