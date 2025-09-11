from .dispatcher import DispatcherMixin
from django.db.models import Q
from properties.utility import build_request_from_scope
from asgiref.sync import sync_to_async


class HandlersMixin(DispatcherMixin):
    async def initialize(self):
        '''Initialize interested properties'''
        from properties.models import InterestedProperty
        from properties.serializers import InterestedPropertySerializer
        
        def process():
            if self.is_admin:
                m = InterestedProperty.objects.all()
            else:
                m = InterestedProperty.objects.filter(
                    Q(user_id=self.scope['user'].id)
                )
            print("Scope: ", self.scope, dir(self.scope))
            request = build_request_from_scope(self.scope)
            s = InterestedPropertySerializer(
                m, many=True, context={"request": request})
            return s.data

        serializer_data = await sync_to_async(process)()
        await self.send_message(serializer_data, self.initialize.__name__)
        print(f"Initialized with {len(serializer_data)} interested properties")

    async def add_interested_property(self, message, handler, room_group_name):
        '''Add interested property event'''
        from properties.models import InterestedProperty, InterestedPropertyDialog
        from properties.serializers import InterestedPropertySerializer
        
        if self.is_admin:
            await self.send_error("Admins cannot add interested properties")
            return
        property_id = message.get("property_id")
        if not property_id:
            await self.send_error("Missing property_id in message")
            return
        
        interested_property, created = await InterestedProperty.objects.aget_or_create(
            property_id=property_id,
            user_id=self.scope['user'].id
        )
        if not created:
            await self.send_error("Interested property already exists")
            return
        await InterestedPropertyDialog.objects.acreate(
            interested_property=interested_property,
            message="I am interested in this property.",
            sender=self.scope['user']
        )
        def process():
            interested_property.refresh_from_db()
            request = build_request_from_scope(self.scope)
            s = InterestedPropertySerializer(
                interested_property, context={"request": request})
            return s.data
        
        serialized_data = await sync_to_async(process)()
        # await self.send_message(serialized_data, self.add_interested_property.__name__)
        await self.send_group(serialized_data, handler, room_group_name)
    
    async def dialog_message(self, message, handler, room_group_name):
        '''Dialog message event'''
        from properties.models import InterestedProperty, InterestedPropertyDialog
        from properties.serializers import InterestedPropertyDialogSerializer
        interested_property_id = message.get("interested_property_id")
        dialog_message = message.get("message")
        if not interested_property_id or not dialog_message:
            await self.send_error("Missing interested_property_id or message in dialog_message")
            return
        try:
            interested_property = await InterestedProperty.objects.aget(
                id=interested_property_id
            )
        except InterestedProperty.DoesNotExist:
            await self.send_error("Interested property does not exist")
            return
        if self.is_admin and interested_property.responder_id != self.scope['user'].id:
            await self.send_error("Admins can only respond to their assigned interested properties")
            return
        dialog = await InterestedPropertyDialog.objects.acreate(
            interested_property=interested_property,
            message=dialog_message,
            sender=self.scope['user']
        )
        def process():
            dialog.refresh_from_db()
            request = build_request_from_scope(self.scope)
            s = InterestedPropertyDialogSerializer(
                dialog, context={"request": request})
            return s.data
        serialized_data = await sync_to_async(process)()

        # Send message to WebSocket
        await self.send_group(serialized_data, handler, room_group_name)
    
    async def assume_responder_role(self, message, handler, room_group_name):
        '''Assume responder event'''
        from properties.models import InterestedProperty
        from properties.serializers import InterestedPropertySerializer

        if not self.is_admin:
            await self.send_error("Only admins can assume responder role")
            return
        interested_property_id = message.get("interested_property_id")
        if not interested_property_id:
            await self.send_error("Missing interested_property_id in assume_responder_role")
            return
        try:
            interested_property = await InterestedProperty.objects.aget(
                id=interested_property_id
            )
        except InterestedProperty.DoesNotExist:
            await self.send_error("Interested property does not exist")
            return
        if interested_property.responder_id is not None:
            await self.send_error("Interested property already has a responder")
            return
        interested_property.responder = self.scope['user']
        await sync_to_async(interested_property.save)()
        
        def process():
            interested_property.refresh_from_db()
            request = build_request_from_scope(self.scope)
            s = InterestedPropertySerializer(
                interested_property, context={"request": request})
            return s.data
        
        serialized_data = await sync_to_async(process)()
        # await self.send_message(serialized_data, self.assume_responder.__name__)
        await self.send_group(serialized_data, handler, room_group_name)
