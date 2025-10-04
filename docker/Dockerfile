# Latest stable release - should be the same version as the prod server is running
FROM ubuntu:rolling

ENV PYTHONDONTWRITEBYTECODE=1 \
    # Immediately write logs to the console / log file
    PYTHONUNBUFFERED=1 \
    # https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
    UV_COMPILE_BYTECODE=1 \
    # https://docs.astral.sh/uv/guides/integration/docker/#caching
    UV_LINK_MODE=copy \
    # https://docs.astral.sh/uv/concepts/projects/config/#project-environment-path
    # (Prevents using/creating a `.venv` folder inside `PROJECT_DIR` when starting
    # the container)
    UV_PROJECT_ENVIRONMENT=/venv/

# From https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG PROJECT_DIR="/web"
WORKDIR ${PROJECT_DIR}

RUN apt update --fix-missing && \
    apt install --yes \
        # Necessary for `python-ldap`
        build-essential python3-dev libldap2-dev libsasl2-dev libssl-dev \
        # Necessary for running `makemessages`/`compilemessages`
        gettext libgettextpo-dev && \
    # Clean up apt cache lists to reduce image size by removing temporary installation files
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ${PROJECT_DIR}
# https://docs.astral.sh/uv/guides/integration/docker/#caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --group dev

# Create the directories used by `STATIC_ROOT` and `MEDIA_ROOT`
ARG STATIC_DATA_DIR="/vol/web"
RUN mkdir -p ${STATIC_DATA_DIR}/static ${STATIC_DATA_DIR}/media && \
    chmod -R 755 ${STATIC_DATA_DIR}
