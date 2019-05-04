import json
import os
import asyncio
import logging
from google.protobuf.json_format import MessageToDict

from deepomatic.rpc.client import Client
from deepomatic.rpc import v07_ImageInput
from deepomatic.rpc.helpers.v07_proto import create_images_input_mix, create_workflow_command_mix

from nats_helper import NATSHelper
from draw import draw_predictions

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #

class Config(object):
    """
    Stores global configuration
    """

    def __init__(self):
        # Should we draw a label or just pass inference results ?
        self.draw_demo = os.getenv('DRAW_DEMO') == "1"

        # Configure frames to process
        self.process_each_n_frames = int(os.getenv('PROCESS_EACH_N_FRAMES', '1'))

        # Setup deepomatic Run RPC client
        amqp_url = os.getenv('AMQP_URL')
        if amqp_url is None:
            raise Exception('AMQP broker not provided in environment var AMQP_URL')
        self.command_queue_name = os.getenv('WORKER_QUEUE', 'worker_queue')
        self.amqp_client = Client(amqp_url)
        self.amqp_client.new_queue(self.command_queue_name)
        self.amqp_response_queue, self.amqp_consumer = self.amqp_client.new_consuming_queue()

# --------------------------------------------------------------------------- #

class MessageHandler(object):

    def __init__(self, config):
        self._config = config

        # Setup Nutanix NATS client
        self._nats_helper = NATSHelper()

        # Internal state
        self._image_counter = 0
        self._last_inference_result = None

    def send_inference_request(self, image):
        """
        Send an inference command to the neural worker and wait for the result
        """
        # Create a recognition command mix
        command = create_workflow_command_mix()

        # This assumes a mono-input network
        image_input = v07_ImageInput(source=b'data:image/*;binary,' + image)
        inputs = create_images_input_mix([image_input])

        # Send the request
        logger.info("Sending inference request to worker")
        correlation_id = self._config.amqp_client.command(
            self._config.command_queue_name,
            self._config.amqp_response_queue.name, inputs, command)

        # Wait for response, `timeout=float('inf')` or `timeout=-1` for infinite wait, `timeout=None` for non blocking
        response = self._config.amqp_consumer.get(correlation_id, timeout=-1)
        # Put data as returned by Deepomatic API v0.7
        data = {'outputs': [MessageToDict(o, preserving_proto_field_name=True, including_default_value_fields=True) for o in response.to_parsed_result_buffer()]}
        logger.info("Got inference response: {}".format(data))
        return data

    async def message_handler(self, image):
        # Perform inference
        if self._image_counter % self._config.process_each_n_frames == 0:
            self._last_inference_result = self.send_inference_request(image)

        if self._config.draw_demo:
            # Draw label on the image
            payload = draw_predictions(image, self._last_inference_result, hcentrate=True, valign=1, draw_only_first_tag=True)
        else:
            payload = json.dumps(self._last_inference_result).encode('utf8')

        # Increment counter and send the result
        self._image_counter += 1
        await self._nats_helper.publish(payload)

    def run_forever(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._nats_helper.connect(loop, self.message_handler))
        try:
            loop.run_forever()
        finally:
            self._nats_helper.close()
            loop.close()


# --------------------------------------------------------------------------- #

if __name__ == '__main__':
    config = Config()
    handler = MessageHandler(config)
    handler.run_forever()
