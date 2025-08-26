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
from urllib.parse import parse_qs
import json
from channels.db import database_sync_to_async
from knox.auth import TokenAuthentication
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed


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
        """ Authenticate the user using Knox token before accepting WebSocket connection """
        self.user = await self.authenticate_token()

        if self.user is None or self.user == AnonymousUser():
            print("🔴 WebSocket Authentication Failed: Closing connection")
            await self.close()
        else:
            print(f"🟢 WebSocket Connected: {self.user.username}")
            await self.channel_layer.group_add("openflow_metrics", self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        """ Remove the connection from the WebSocket group """
        print(f"🔴 WebSocket Disconnected: {close_code}")
        await self.channel_layer.group_discard("openflow_metrics", self.channel_name)

    async def receive(self, text_data):
        """ Handle incoming WebSocket messages """
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message", "")

        # Send message to WebSocket group
        await self.channel_layer.group_send(
            "openflow_metrics",
            {
                'type': 'openflow_message',
                'message': message
            }
        )

    async def openflow_message(self, event):
        """ Send a message from the WebSocket group to the client """
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def authenticate_token(self):
        """ Extract and validate the Knox token from WebSocket query params """
        query_params = parse_qs(self.scope["query_string"].decode())
        token_key = query_params.get("token", [None])[0]

        if not token_key:
            print("🔴 No token found in WebSocket request")
            return None

        # Use Knox TokenAuthentication to validate the full token
        try:
            user, _ = TokenAuthentication().authenticate_credentials(token_key.encode())
            print(f"🟢 Authenticated user: {user.username}")
            return user
        except AuthenticationFailed:
            print(f"🔴 Invalid or expired token: {token_key[:8]}")
            return None