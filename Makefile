run:
	python manage.py runserver 0.0.0.0:8000

migrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

superuser:
	python manage.py createsuperuser

startapp:
	python manage.py startapp

shell:
	python manage.py shell

test:
	python manage.py test
