import asyncio
import os
import sys
import io
import requests
import logging
from PIL import Image
import xi_iot_pb2
from nats.aio.client import Client as NATS
#from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

src_nats_topic = os.environ.get('SRC_NATS_TOPIC')
if src_nats_topic is None:
    logger.error("please set SRC_NATS_TOPIC in environment variables")

dst_nats_topic = os.environ.get('DST_NATS_TOPIC')
if dst_nats_topic is None:
    logger.error("please set DST_NATS_TOPIC in environment variables")

nats_broker_url = os.environ.get('NATS_BROKER_URL')
if nats_broker_url is None:
    logger.error("please set NATS_BROKER_URL in environment variables")

if len(sys.argv) > 1:
    url = sys.argv[1]
else:
    url = "https://storage.googleapis.com/dp-vulcan/tests/imgs/dog.jpg"
response = requests.get(url)
assert response.status_code == 200
image = response.content

success = False

async def message_handler(msg):
    global success
    try:
        logger.info("Received image from runtime")
        _msg = xi_iot_pb2.DataStreamMessage()
        _msg.ParseFromString(msg.data)

        img = Image.open(io.BytesIO(_msg.payload))
        img.save("result.jpg")
        success = True
    except Exception as e:
        logger.error("{}".format(e))

async def publish(loop):
    nc = NATS()

    logging.info("broker: {b}, src topic: {s}, dst_topic: {d}".format(b=nats_broker_url, s=src_nats_topic, d=dst_nats_topic))
    await nc.connect(nats_broker_url, loop=loop)

    _msg = xi_iot_pb2.DataStreamMessage()
    _msg.payload = image

    logger.info("Subscribe to result topic: {}".format(dst_nats_topic))
    sid = await nc.subscribe(dst_nats_topic, cb=message_handler)

    logger.info("Sending image to source topic: {}".format(src_nats_topic))
    await nc.publish(src_nats_topic, _msg.SerializeToString())

    # Wait one second until message_handler is called
    await asyncio.sleep(10)

    # Remove interest in subscription.
    await nc.unsubscribe(sid)

    # Terminate connection to NATS.
    await nc.close()

logger.info("Starting loop")
loop = asyncio.get_event_loop()
loop.run_until_complete(publish(loop))
loop.close()

if not success:
    raise Exception("FAILED: did not received an image on time")




