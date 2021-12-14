from channels.auth import AuthMiddlewareStack
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from mail.email import EmailConsumer
from make_queue.views.stream.stream import StreamConsumer


websocket_urlpatterns = [
    path("ws/stream/<str:stream_name>/", StreamConsumer.as_asgi()),
]

channel_routes = {
    'email': EmailConsumer.as_asgi(),
}

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
    'channel': ChannelNameRouter(
        channel_routes
    )
})
