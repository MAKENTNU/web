sync: ## Makes your locally installed packages match the ones specified in `pyproject.toml`.
	uv sync --group dev

manage: ## Runs the Django management command specified by passing `args`.
	uv run $(uv_args) manage.py $(args)

shell: ## Enters a Django shell, with most common classes automatically imported.
	make manage args="shell_plus"

migrate: ## Updates the database schema from the migration files.
	make manage args="migrate $(args)"

makemigrations: ## Creates migration files from the models, if there are any changes.
	make manage args="makemigrations $(args)"

makemessages: ## Extracts all translatable strings from the codebase and updates the `.po` files with them.
	make manage args="makemessages $(args)"

makemessages-all: ## Runs `makemessages` for all languages and domains.
	make makemessages args="-a"
	make makemessages args="-a -d djangojs"

compilemessages: ## Updates the `.mo` files from the `.po` files.
	make manage args="compilemessages $(args)"

collectstatic: ## "Compiles" the static files (CSS and JS files, images, etc.) into the `STATIC_ROOT` folder.
	make manage args="collectstatic --no-input"

update: ## Updates the installed packages, database and static files.
	make sync
	make migrate
	make collectstatic

createsuperuser: ## Creates a superuser.
	make manage args="createsuperuser"

start: ## Starts the Django webserver.
	make manage args="runserver $(args)"

test: ## Runs the test suite. Pass extra arguments with `args`, e.g. `args="-k 'test_function'"`.
	make manage args="test $(args)"

### Docker ###

COMPOSE_FILE := docker/compose.dev.yaml

d-compose: ## Run Docker Compose for development with `make_ntnu` as project name. Helper command to run any compose command.
	docker compose -f '$(COMPOSE_FILE)' -p make_ntnu $(args)

d-build: ## Rebuilds the container image. Use when changes are made to the Dockerfile or the dependencies in `pyproject.toml`.
	make d-compose args="build"

d-down: ## Stops and removes the container.
	make d-compose args="down"

d-bash: ## Enters a bash shell in an already-running `web` container.
	make d-compose args="exec web bash"

d-manage: ## Runs the Django management command specified by passing `args`.
	make d-compose args="run --rm web uv run manage.py $(args)"

d-shell: ## Enters a Django shell, with most common classes automatically imported.
	make d-manage args="shell_plus"

d-migrate: ## Updates the database schema from the migration files.
	make d-manage args="migrate $(args)"

d-makemigrations: ## Creates migration files from the models, if there are any changes.
	make d-manage args="makemigrations $(args)"

d-makemessages: ## Extracts all translatable strings from the codebase and updates the `.po` files with them.
	make d-manage args="makemessages $(args)"

d-makemessages-all: ## Runs `makemessages` for all languages and domains.
	make d-makemessages args="-a"
	make d-makemessages args="-a -d djangojs"

d-compilemessages: ## Updates the `.mo` files from the `.po` files.
	make d-manage args="compilemessages $(args)"

d-collectstatic: ## "Compiles" the static files (CSS and JS files, images, etc.) into the `STATIC_ROOT` folder.
	make d-manage args="collectstatic --no-input"

d-update: ## Updates the container, database and static files.
	make d-build
	make d-migrate
	make d-collectstatic

d-createsuperuser: ## Creates a superuser.
	make d-manage args="createsuperuser"

d-start: ## Starts the Django webserver.
	make d-compose args="up $(args)"

d-test: ## Runs the test suite. Pass extra arguments with `args`, e.g. `args="-k 'test_function'"`.
	make d-manage args="test $(args)"
