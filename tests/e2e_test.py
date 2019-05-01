import asyncio
import os
import sys
import io
import logging
import json
import time
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'runtime'))

from nats_helper import NATSHelper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #

class Status(object):
    """
    Tests run in event loop so we can only wait for some time
    before checking for success or not. This class allow to stop
    waiting as soon as we have a result.
    """

    def __init__(self):
        self._success = None
        self._exception = None

    def signal_success(self):
        self._success = True

    def signal_exception(self, exception):
        self._success = False
        self._exception = exception

    async def sleep_early_stop(self, duration):
        count = 0
        while self._success is None and count < duration:
            await asyncio.sleep(1)
            count += 1

    def assert_success(self):
        if self._success is None:
            raise Exception("Did not received a response on time")
        elif not self._success:
            raise self._exception

# --------------------------------------------------------------------------- #

def read_test_image():
    # Read test image
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = os.path.join(os.path.dirname(__file__), 'dog.jpg')
    with open(path, 'rb') as f:
        return f.read()

def run_nats_loop(status, topic_suffix, message_handler):
    # Inversion of SRC and DST is on purpose: the NATS helper is written on the worker point of vue, here we are the producer
    nats_helper = NATSHelper(nats_src_topic=os.getenv('NATS_DST_TOPIC_{}'.format(topic_suffix)),  nats_dst_topic=os.getenv('NATS_SRC_TOPIC_{}'.format(topic_suffix)))
    image = read_test_image()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(nats_helper.connect(loop, message_handler))
    loop.run_until_complete(nats_helper.publish(image))
    loop.run_until_complete(status.sleep_early_stop(10))
    status.assert_success()

# --------------------------------------------------------------------------- #

def test_draw_on_image():
    status = Status()

    async def message_handler(payload):
        nonlocal status
        try:
            img = Image.open(io.BytesIO(payload))
        except Exception as e:
            status.signal_exception(e)
            return
        img.save("result.jpg")
        status.signal_success()

    run_nats_loop(status, 'IMAGE', message_handler)

def test_draw_on_json():
    status = Status()

    async def message_handler(payload):
        nonlocal status
        try:
            json.loads(payload)
        except Exception as e:  # happens if no image can be decoded
            status.signal_exception(e)
            return
        status.signal_success()

    run_nats_loop(status, 'JSON', message_handler)

def test_fps():
    N = 50  # number of frames to send
    expected_fps = 25
    counter = 0
    first_received = None
    last_received = None

    async def message_handler(payload):
        nonlocal N, counter, first_received, last_received
        last_received = time.time()
        if first_received is None:
            first_received = last_received
        try:
            Image.open(io.BytesIO(payload))
        except Exception as e:
            logger.error(str(e))
        counter += 1
        if counter == N:
            loop = asyncio.get_event_loop()
            loop.stop()

    nats_helper = NATSHelper(nats_src_topic=os.getenv('NATS_DST_TOPIC_IMAGE'),  nats_dst_topic=os.getenv('NATS_SRC_TOPIC_IMAGE'))
    image = read_test_image()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(nats_helper.connect(loop, message_handler))

    t = time.time()
    for i in range(N):
        sleep_time = t + i / expected_fps - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        loop.run_until_complete(nats_helper.publish(image))
    effective_send_fps = N / (time.time() - t)
    logger.info("Effective send fps: {}".format(effective_send_fps))

    loop.run_forever()

    effective_process_fps = N / (last_received - first_received)
    logger.info("Effective process fps: {}".format(effective_process_fps))
    assert abs(effective_process_fps - expected_fps) < 5


# --------------------------------------------------------------------------- #

if __name__ == '__main__':
    test_draw_on_image()
    test_draw_on_json()
    test_fps()
