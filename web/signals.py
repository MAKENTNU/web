from django_cleanup.signals import cleanup_pre_delete
from sorl.thumbnail import delete


def connect():
    # Code based on the example at https://github.com/un1t/django-cleanup/tree/2b02f61c151296571e104670c017db98f3d621f9#signals
    def delete_sorl_thumbnail(file, *args, **kwargs):
        delete(
            file,
            # Should not delete the source file, as this is already done by `django-cleanup`
            delete_file=False,
        )

    cleanup_pre_delete.connect(delete_sorl_thumbnail)
