from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from django.urls import path

from mail.email import EmailConsumer
from make_queue.views.stream.stream import StreamConsumer

websocket_urlpatterns = [
    path('ws/stream/<str:stream_name>/', StreamConsumer),
]

channel_routes = {
    "email": EmailConsumer
}

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
    'channel': ChannelNameRouter(
        channel_routes
    )
})
