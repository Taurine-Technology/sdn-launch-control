from channels.generic.websocket import AsyncWebsocketConsumer
import json


class FlowConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add('flow_updates', self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('flow_updates', self.channel_name)

    async def receive(self, text_data):
        pass

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    async def flow_message(self, event):
        flow = event['flow']

        await self.send_message({
            'flow': flow
        })
