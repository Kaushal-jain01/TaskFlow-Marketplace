# from channels.generic.websocket import AsyncJsonWebsocketConsumer
# import logging

# logger = logging.getLogger("django")

# class NotificationConsumer(AsyncJsonWebsocketConsumer):
#     async def connect(self):
#         logger.info(f"WS scope user: {self.scope['user']}")

#         if self.scope["user"].is_anonymous:
#             logger.warning("WS rejected: anonymous user")
#             await self.close()
#             return

#         self.group_name = f"user_{self.scope['user'].id}"

#         await self.channel_layer.group_add(
#             self.group_name,
#             self.channel_name
#         )

#         await self.accept()

#         logger.info(f"WS connected: {self.group_name}")

#     async def disconnect(self, close_code):
#         if hasattr(self, "group_name"):
#             await self.channel_layer.group_discard(
#                 self.group_name,
#                 self.channel_name
#             )
#             logger.info(f"WS disconnected: {self.group_name}")

#     async def send_notification(self, event):
#         logger.info(f"WS send_notification: {event['data']}")
#         await self.send_json(event["data"])
