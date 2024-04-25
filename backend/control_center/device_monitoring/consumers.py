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


class OpenFlowMetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join room
        await self.channel_layer.group_add("openflow_metrics", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room
        await self.channel_layer.group_discard("openflow_metrics", self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to WebSocket
        await self.channel_layer.group_send(
            "openflow_metrics",
            {
                'type': 'openflow_message',
                'message': message
            }
        )

    # Receive message from room group
    async def openflow_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
