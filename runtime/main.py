import os
import asyncio
import logging
import io
from PIL import Image, ImageFont, ImageDraw
from google.protobuf.json_format import MessageToDict

import xi_iot_pb2
from nats.aio.client import Client as NATS
#from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

from deepomatic.rpc.client import Client
from deepomatic.rpc import v07_ImageInput
from deepomatic.rpc.helpers.v07_proto import create_images_input_mix, create_workflow_command_mix

logger = logging.getLogger(__name__)

# Configure worker queue
command_queue_name = 'worker_queue'
amqp_url = os.getenv('AMQP_URL')

# configure drawing font
font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "arial.ttf"), 48)

# Setup global variables
client = Client(amqp_url)
command_queue = client.new_queue(command_queue_name)
response_queue, consumer = client.new_consuming_queue()

nc = None
nats_broker_url = ""
src_nats_topic = ""
dst_nats_topic = ""

def get_nats_meta():
    global nats_broker_url, src_nats_topic, dst_nats_topic
    nats_broker_url = os.environ.get('NATS_BROKER_URL')
    if nats_broker_url is None:
        logger.error('nats broker not provided in environment var NATS_BROKER_URL')
        exit(1)

    src_nats_topic = os.environ.get('SRC_NATS_TOPIC')
    if src_nats_topic is None:
        logger.error('src nats topic not provided in environment var SRC_NATS_TOPIC')
        exit(1)
    dst_nats_topic = os.environ.get('DST_NATS_TOPIC')

    if dst_nats_topic is None:
        logger.error('dst nats broker not provided in environment var DST_NATS_TOPIC')
        exit(1)
    return nats_broker_url, src_nats_topic, dst_nats_topic

async def message_handler(msg):
    try:
        logger.info("Received a message!")
        _msg = xi_iot_pb2.DataStreamMessage()
        _msg.ParseFromString(msg.data)

        # Create a recognition command mix
        command = create_workflow_command_mix()

        # This assumes a mono-input network
        image_input = v07_ImageInput(source=b'data:image/*;binary,' + _msg.payload)
        inputs = create_images_input_mix([image_input])

        # Send the request
        logger.info("Sending inference request to worker")
        correlation_id = client.command(command_queue_name, response_queue.name, inputs, command)

        # Wait for response, `timeout=float('inf')` or `timeout=-1` for infinite wait, `timeout=None` for non blocking
        response = consumer.get(correlation_id, timeout=-1)
        # Put data as returned by Deepomatic API v0.7
        data = {'outputs': [MessageToDict(o, preserving_proto_field_name=True, including_default_value_fields=True) for o in response.to_parsed_result_buffer()]}
        logger.info("Got inference response: {}".format(data))

        # Drawn label on image
        label = data['outputs'][0]['labels']['predicted'][0]['label_name']
        img = Image.open(io.BytesIO(_msg.payload))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), label, (255, 255, 255), font=font)
        with io.BytesIO() as buff:
            img.save(buff, format="JPEG")
            _msg = xi_iot_pb2.DataStreamMessage()
            _msg.payload = buff.getvalue()

        # RFC: We could leverage `reply` topic as the destination topic which would not require DST_NATS_TOPIC to be provided
        # await nc.publish(reply, data)
        await nc.publish(dst_nats_topic, _msg.SerializeToString())
    except Exception as e:
        logger.error("{}".format(e))

async def run(loop):
    nats_broker_url, src_nats_topic, dst_nats_topic = get_nats_meta()
    logger.info("broker: {b}, src topic: {s}, dst_topic: {d}".format(b=nats_broker_url, s=src_nats_topic, d=dst_nats_topic))

    global nc
    nc = NATS()

    # This will return immediately if the server is not listening on the given URL
    await nc.connect(nats_broker_url, loop=loop)
    logger.info("Connected to broker")

    await nc.subscribe(src_nats_topic, cb=message_handler)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.run_forever()
    try:
        loop.run_until_complete(run(loop))
        loop.run_forever()
    finally:
        nc.drain()
        loop.close()
