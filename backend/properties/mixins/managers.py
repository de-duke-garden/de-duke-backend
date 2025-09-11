from .handlers import HandlersMixin

class HandlerManagerMixin(HandlersMixin):
    async def handler_manager(self, handler: str, room_group_name: str, message=None):
        match handler:
            case self.dialog_message.__name__:
                # Send message to room group
                print(
                    f"Sending message to group {room_group_name}: {message}")
                # await self.send_group(message, handler, room_group_name)
                await self.dialog_message(message, handler, room_group_name)
            case self.add_interested_property.__name__:
                # await self.send_group(message, handler, room_group_name)
                await self.add_interested_property(message, handler, room_group_name)
            case self.assume_responder_role.__name__:
                await self.assume_responder_role(message, handler, room_group_name)
            case _:
                await self.send_error(f"Unknown handler: {handler}")
                return
