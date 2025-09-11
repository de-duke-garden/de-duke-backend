import json
from properties.utility import JSONv2Encoder


class DispatcherMixin:
    async def send_error(self, error_message):
        await self.send(text_data=json.dumps(
            {
                "error": error_message, 
                "message": None, 
                "handler": None
            },
            cls=JSONv2Encoder
        ))

    async def send_message(self, message, handler: str):
        try:
            await self.send(text_data=json.dumps(
                {
                    "error": None, 
                    "message": message, 
                    "handler": handler
                },
                cls=JSONv2Encoder
            ))
        except Exception as e:
            await self.send_error(f"Failed to send message: {str(e)}")

    async def send_group(self, message, handler: str, room_group_name: str):
        # Serialize the message using JSONv2Encoder
        message = json.loads(json.dumps(message, cls=JSONv2Encoder))
        await self.channel_layer.group_send(
            room_group_name, {"type": "dispatcher", "message": message, "handler": handler}
        )
    
    async def dispatcher(self, event):
        message = event["message"]
        handler = event["handler"]
        await self.send_message(message, handler)
