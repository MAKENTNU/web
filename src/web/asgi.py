"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os

# Should come before any of the other imports, in case they use the settings in some way
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")

from channels.routing import ChannelNameRouter, ProtocolTypeRouter
from django.core.asgi import get_asgi_application

# Initialize the Django ASGI application early to ensure the `AppRegistry`
# is populated before importing code that may import ORM models
# (based on https://github.com/django/channels/commit/0539bcf5be30a8f6ad7cabec794219879e43ab89#diff-d9b149498982c0663c3b7170398773361ed5678f1a627e9c2fd8d2c955c563db)
django_asgi_app = get_asgi_application()

from mail.email import EmailConsumer


channel_routes = {
    "email": EmailConsumer.as_asgi(),
}

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "channel": ChannelNameRouter(channel_routes),
    }
)
