import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.classroom_id = self.scope['url_route']['kwargs']['classroom_id']
        self.room_group_name = f'chat_{self.classroom_id}'

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

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        image_url = text_data_json['image_url']
        file_url = text_data_json['file_url']
        username = self.scope['user'].username

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'image_url': image_url,
                'file_url': file_url,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        image_url = event['image_url']
        file_url = event['file_url']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'image_url': image_url,
            'file_url': file_url,
        }))
