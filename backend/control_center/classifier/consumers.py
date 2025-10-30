# File: consumers.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
# available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.


from channels.generic.websocket import AsyncWebsocketConsumer
import json

from observability.channels_hooks import connection_opened, connection_closed, group_joined, group_left


class FlowConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add('flow_updates', self.channel_name)
        try:
            connection_opened()
            group_joined()
        except Exception:
            pass

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('flow_updates', self.channel_name)
        try:
            group_left()
            connection_closed()
        except Exception:
            pass

    async def receive(self, text_data):
        pass

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    async def flow_message(self, event):
        flow = event['flow']

        await self.send_message({
            'flow': flow
        })
