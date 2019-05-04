import asyncio
import os
import sys
import io
import logging
import json
import time
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'runtime'))

import draw

tagging_payload = {
    "outputs": [{
        "labels": {
            "predicted": [{
                "label_name": "sunglasses",
                "label_id": 9,
                "score": 0.801353174,
                "threshold": 0.347
            }, {
                "label_name": "glasses",
                "label_id": 8,
                "score": 0.175235228,
                "threshold": 0.139
            }],
            "discarded": []
        }
    }]
}

detection_payload = {
    "outputs": [{
        "labels": {
            "predicted": [{
                "label_name": "sunglasses",
                "label_id": 9,
                "roi": {
                    "region_id": 1,
                    "bbox": {
                        "xmin": 0.312604159,
                        "ymin": 0.366485775,
                        "ymax": 0.5318923,
                        "xmax": 0.666821837
                    }
                },
                "score": 0.990304172,
                "threshold": 0.347
            }],
            "discarded": []
        }
    }]
}

def read_test_image():
    path = os.path.join(os.path.dirname(__file__), 'screenshot.jpg')
    with open(path, 'rb') as f:
        return f.read()

def display_draw_classif_result(kwargs):
    draw.FONT = None
    img = read_test_image()
    payload = draw.draw_predictions(img, tagging_payload, **kwargs)
    img = Image.open(io.BytesIO(payload))
    img.save("result_classif.jpg")

def display_draw_detect_result(kwargs):
    draw.FONT = None
    img = read_test_image()
    payload = draw.draw_predictions(img, detection_payload, **kwargs)
    img = Image.open(io.BytesIO(payload))
    img.save("result_detect.jpg")


if __name__ == '__main__':
    kwargs = {
        'hcentrate': True,
        'valign': 1,
        'draw_only_first_tag': True,
    }
    display_draw_classif_result(kwargs)
    display_draw_detect_result(kwargs)
