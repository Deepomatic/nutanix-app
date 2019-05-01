import json
import os
import asyncio
import logging
import textwrap
import io
from PIL import Image, ImageFont, ImageDraw
from google.protobuf.json_format import MessageToDict

from deepomatic.rpc.client import Client
from deepomatic.rpc import v07_ImageInput
from deepomatic.rpc.helpers.v07_proto import create_images_input_mix, create_workflow_command_mix

from nats_helper import NATSHelper

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #

class Config(object):
    """
    Stores global configuration
    """

    def __init__(self):
        # Should we draw a label or just pass inference results ?
        self.draw_demo = os.getenv('DRAW_DEMO') == "1"

        # configure drawing font
        self.font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "assets", "fonts", "arial.ttf"), 48)
        self.font_color = self.get_font_color()

        # Setup deepomatic Run RPC client
        amqp_url = os.getenv('AMQP_URL')
        if amqp_url is None:
            raise Exception('AMQP broker not provided in environment var AMQP_URL')
        self.command_queue_name = os.getenv('WORKER_QUEUE', 'worker_queue')
        self.amqp_client = Client(amqp_url)
        self.amqp_client.new_queue(self.command_queue_name)
        self.amqp_response_queue, self.amqp_consumer = self.amqp_client.new_consuming_queue()

    @staticmethod
    def get_font_color():
        """
        Convert environment variable FONT_COLOR from RRGGBB or RGB in hexadecimal format
        to a tuple (R, G, B).
        """
        color = os.getenv('FONT_COLOR', None)
        if color is not None:
            try:
                if len(color) == 6:
                    return tuple([int(c, 16) for c in textwrap.wrap(color, 2)])
                elif len(color) == 3:
                    return tuple([int(c, 16) * 17 for c in color])
            except ValueError:
                pass
            logger.error("Error parsing font color, defaulting to light blue")

        return (34, 165, 247)

# --------------------------------------------------------------------------- #

class MessageHandler(object):

    def __init__(self, config):
        self._config = config

        # Setup Nutanix NATS client
        self.nats_helper = NATSHelper()

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

    def draw_label(self, image, inference_result):
        """
        Draw infered label in top-left corner of the image
        """
        label = inference_result['outputs'][0]['labels']['predicted'][0]['label_name']
        img = Image.open(io.BytesIO(image))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), label, self._config.font_color, font=self._config.font)
        with io.BytesIO() as buff:
            img.save(buff, format="JPEG")
            return buff.getvalue()

    async def message_handler(self, image):
        # Perform inference
        inference_result = self.send_inference_request(image)

        if self._config.draw_demo:
            # Draw label on the image
            payload = self.draw_label(image, inference_result)
        else:
            payload = json.dumps(inference_result).encode('utf8')

        # Send the result image
        await self.nats_helper.publish(payload)

    def run_forever(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.nats_helper.connect(loop, self.message_handler))
        try:
            loop.run_forever()
        finally:
            self.nats_helper.close()
            loop.close()


# --------------------------------------------------------------------------- #

if __name__ == '__main__':
    config = Config()
    handler = MessageHandler(config)
    handler.run_forever()
