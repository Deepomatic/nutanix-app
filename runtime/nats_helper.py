import os
import logging
import asyncio

from nats.aio.client import Client as NATS

from proto import xi_iot_pb2

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #

class NATSHelper(object):

    def __init__(self, nats_broker_url=None, nats_src_topic=None, nats_dst_topic=None):
        self.subscribe_id = None
        self.connected = False
        self.nats_client = NATS()

        self._get_config_from_env_var_('nats_broker_url', 'NATS_ENDPOINT', nats_broker_url, 'NATS broker')
        self._get_config_from_env_var_('nats_src_topic', 'NATS_SRC_TOPIC', nats_src_topic, 'NATS source topic')
        self._get_config_from_env_var_('nats_dst_topic', 'NATS_DST_TOPIC', nats_dst_topic, 'NATS destination topic')

        logger.info("broker: {b}, src topic: {s}, dst_topic: {d}".format(
            b=self.nats_broker_url,
            s=self.nats_src_topic,
            d=self.nats_dst_topic))

    def __del__(self):
        self.close()

    def _get_config_from_env_var_(self, attr, var, default, what):
        if default is None:
            value = os.environ.get(var)
        else:
            value = default
        if not value:  # also check empty strings
            raise Exception('{what} not provided in environment var {var}'.format(what=what, var=var))
        setattr(self, attr, value)

    @staticmethod
    def payload_from_message(msg):
        """
        Convert input payload into an image
        """
        _msg = xi_iot_pb2.DataStreamMessage()
        _msg.ParseFromString(msg.data)
        return _msg.payload

    @staticmethod
    def message_from_payload(payload):
        """
        Convert image into output payload
        """
        msg = xi_iot_pb2.DataStreamMessage()
        msg.payload = payload
        return msg.SerializeToString()

    async def publish(self, payload):
        try:
            payload = self.message_from_payload(payload)
            # RFC: We could leverage `reply` topic as the destination topic which would not require NATS_DST_TOPIC to be provided
            # await nc.publish(reply, data)
            logger.info("Sending message to topic '{}'".format(self.nats_dst_topic))
            await self.nats_client.publish(self.nats_dst_topic, payload)
        except Exception as e:
            # Catch an display errors which are otherwise not shown
            logger.error("{}".format(e))
            raise

    async def connect(self, loop, message_handler_cb):
        # Define a helper function to unbox the message and catch errors for display
        async def receive_cb(msg):
            try:
                logger.info("Received a message!")
                payload = self.payload_from_message(msg)
                await message_handler_cb(payload)
            except Exception as e:
                # Catch an display errors which are otherwise not shown
                logger.error("{}".format(e))
                raise

        try:
            # This will return immediately if the server is not listening on the given URL
            await self.nats_client.connect(self.nats_broker_url, loop=loop)
            self.connected = True
            logger.info("Connected to broker, subscribing to topic '{}'".format(self.nats_src_topic))

            self.subscribe_id = await self.nats_client.subscribe(self.nats_src_topic, cb=receive_cb)
        except Exception as e:
            # Catch an display errors which are otherwise not shown
            logger.error("{}".format(e))
            raise

    def close(self):
        # Remove interest in subscription.
        loop = asyncio.get_event_loop()
        if self.subscribe_id is not None:
            loop.run_until_complete(self.nats_client.unsubscribe(self.subscribe_id))
            self.subscribe_id = None

        # Terminate connection to NATS.
        if self.nats_client is not None and self.connected:
            self.nats_client.drain()
            loop.run_until_complete(self.nats_client.close())
            self.nats_client = None
            self.connected = False
