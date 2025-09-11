import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from .utility import decrypt_payload
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from .mixins.managers import HandlerManagerMixin

# Group = {channel_name: str, is_admin: bool}

available_groups = {}

class ChatConsumer(HandlerManagerMixin, AsyncWebsocketConsumer):
    TIMEOUT = 60 * 5  # 5 minutes
    async def connect(self):
        global available_groups
        User = get_user_model()
        print("Connecting to WebSocket")
        encrypted_payload = self.scope["url_route"]["kwargs"]["payload"]
        payload = decrypt_payload(encrypted_payload)
        if not payload:
            await self.close()
            return
        timestamp = payload.get("timestamp")
        if not timestamp or (abs(timezone.now().timestamp() - float(timestamp)) > self.TIMEOUT):
            # Payload is older than TIMEOUT seconds
            await self.close()
            return
        user_id = payload.get("user_id")
        user = await sync_to_async(User.objects.filter(id=user_id).first)()
        if not user:
            await self.close()
            return
        self.is_admin = user.is_staff or user.is_superuser
        self.scope["user"] = user
        self.room_group_name = f"chat_{user_id}"

        user_group = {
            "channel_name": self.channel_name,
            "is_admin": self.is_admin,
        }
        available_groups[self.room_group_name] = user_group

        if self.is_admin:
            # Admin can join all groups
            for group, info in available_groups.items():
                # Add admin to all groups
                await self.channel_layer.group_add(group, self.channel_name)
                if info["is_admin"] and group != self.room_group_name:
                    # Add other admins to this admin's group
                    await self.channel_layer.group_add(
                        self.room_group_name, info["channel_name"])
        else:
            # Regular user can only join their own group and add admin to their group
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            for group, info in available_groups.items():
                if info["is_admin"]:
                    # Add user to the admin's group
                    # await self.channel_layer.group_add(group, self.channel_name)
                    # Add admin to the user's group
                    await self.channel_layer.group_add(self.room_group_name, info["channel_name"])

        await self.accept()
        print(f"Connected to WebSocket as user {user_id} (admin: {self.is_admin})")
        print(f"Available groups after connect: {available_groups}")
        await self.initialize()

    async def disconnect(self, close_code):
        global available_groups
        print("Disconnecting from WebSocket")
        if not hasattr(self, 'is_admin'):
            # Not properly connected, nothing to do
            return
        # Leave room group
        if self.is_admin:
            # Admin leaves all groups
            for group in available_groups:
                await self.channel_layer.group_discard(group, self.channel_name)
            # Admin remove all other admins from their group
            for group, info in available_groups.items():
                if info["is_admin"] and group != self.room_group_name:
                    await self.channel_layer.group_discard(
                        self.room_group_name, info["channel_name"])
            # Delete the group when no one is left
            del available_groups[self.room_group_name]
        else:
            # Regular user leaves their own group
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            # Regular user remove admin from their group
            for group, info in available_groups.items():
                if info["is_admin"]:
                    await self.channel_layer.group_discard(
                        self.room_group_name, info["channel_name"])
            # Delete the group when no one is left
            del available_groups[self.room_group_name]
            # for group, info in available_groups.items():
            #     # Remove user from admin groups
            #     if info["is_admin"]:
            #         await self.channel_layer.group_discard(group, self.channel_name)
        print("Disconnected from WebSocket")
        print(f"Available groups after disconnect: {available_groups}")

    # Receive message from WebSocket

    async def receive(self, text_data):
        text_data_json = {}
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            self.send_error("Invalid JSON format")
            return
        handler = text_data_json.get("handler")
        if not handler:
            # Invalid message format; send back an error
            await self.send_error("Invalid message format: missing handler")
            return

        target = text_data_json.get("target")
        # if self.is_admin and not target: # Admin must specify a target
        #     await self.send_error("Admin must specify a target")
        #     return
        target_group_name = f"chat_{target}" if target else None
        
        if self.is_admin and target_group_name and target_group_name in available_groups:
            # The user is online if their group exists
            # Therefore admin can send message to that user group
            room_group_name = target_group_name
        else:
            # The target user is offline
            # Therefore the admin send to their own group which contains only admins
            # If not admin, send to their own group
            room_group_name = self.room_group_name
        
        message = text_data_json.get("message")
        await self.handler_manager(handler, room_group_name, message)