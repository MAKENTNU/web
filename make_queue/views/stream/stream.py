import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['stream_name']
        self.room_group_name = 'stream_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        image = text_data_json['image']
        key = text_data_json['key']

        if key == settings.STREAM_KEY:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'image',
                    'image': image
                }
            )

    # Receive message from room group
    async def image(self, event):
        image = event['image']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'image': image
        }))
