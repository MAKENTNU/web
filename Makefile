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
