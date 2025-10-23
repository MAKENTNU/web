run:
	uv run manage.py runserver 0.0.0.0:8000

migrations:
	uv run manage.py makemigrations ${A}

migrate:
	uv run manage.py migrate

superuser:
	uv run manage.py createsuperuser

startapp:
	uv run manage.py startapp

shell:
	uv run manage.py shell

test:
	uv run manage.py test
