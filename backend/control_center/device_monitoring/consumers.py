from channels.generic.websocket import AsyncWebsocketConsumer
import json


class DeviceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add('device_stats', self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('device_stats', self.channel_name)

    async def receive(self, text_data):
        # Handle incoming WebSocket messages
        # You can access the WebSocket data via the `text_data` parameter
        pass

    async def send_message(self, message):
        # Send a message to the WebSocket connection
        await self.send(text_data=json.dumps(message))

    async def device_message(self, event):
        # Fetch data from the event and send it to WebSocket clients
        device_data = event['device']
        await self.send_message({
            'type': 'stats',
            'data': device_data
        })
