import pytest
import os
import sys
import io
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'runtime'))

import draw
import utils

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

TEST_KWARGS = {
    'hcentrate': True,
    'valign': 1,
    'draw_only_first_tag': True,
}

def read_test_image(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, 'rb') as f:
        return f.read()

@pytest.mark.parametrize(
    'kwargs', [TEST_KWARGS]
)
def test_display_draw_classif_result(kwargs):
    draw.FONT = None
    img = read_test_image('screenshot.jpg')
    payload = draw.draw_predictions(img, tagging_payload, **kwargs)
    img = Image.open(io.BytesIO(payload))
    img.save("result_classif.jpg")

@pytest.mark.parametrize(
    'kwargs', [TEST_KWARGS]
)
def test_display_draw_detect_result(kwargs):
    draw.FONT = None
    img = read_test_image('screenshot.jpg')
    payload = draw.draw_predictions(img, detection_payload, **kwargs)
    img = Image.open(io.BytesIO(payload))
    img.save("result_detect.jpg")

def test_crop_h():
    img = read_test_image('dog.jpg')
    aspect_ratio = 4 / 3
    img, _ = utils.crop(img, aspect_ratio)
    w, h = img.size
    assert w / h == pytest.approx(aspect_ratio)
    img.save("result_crop_h.jpg")

def test_crop_v():
    img = read_test_image('dog.jpg')
    aspect_ratio = 3 / 4
    img, _ = utils.crop(img, aspect_ratio)
    w, h = img.size
    assert w / h == pytest.approx(aspect_ratio)
    img.save("result_crop_v.jpg")

def test_crop_change_coords():
    def make_roi(margin=0):
        return {
            'bbox': {
                'xmin': 0 + margin,
                'ymin': 0 + margin,
                'xmax': 1 - margin,
                'ymax': 1 - margin,
            }
        }

    img = read_test_image('dog.jpg')

    _, change_of_basis_matrix = utils.crop(img, 3 / 2)
    roi = make_roi()
    utils.normalize_roi(roi, change_of_basis_matrix)
    assert roi['bbox'] == {
        'xmin': pytest.approx(0.08208955),
        'ymin': pytest.approx(0),  # clipped to [0, 1]
        'xmax': pytest.approx(0.91791045),
        'ymax': pytest.approx(1),  # clipped to [0, 1]
    }

    roi = make_roi(margin=0.2)
    utils.normalize_roi(roi, change_of_basis_matrix)
    assert roi['bbox'] == {
        'xmin': pytest.approx(0.24925373),
        'ymin': pytest.approx(0.1273743),
        'xmax': pytest.approx(0.75074627),
        'ymax': pytest.approx(0.87821229),
    }

    _, change_of_basis_matrix = utils.crop(img, 2 / 3)
    roi = make_roi(margin=0.2)
    utils.normalize_roi(roi, change_of_basis_matrix)
    assert roi['bbox'] == {
        'xmin': pytest.approx(0.1273743),
        'ymin': pytest.approx(0.24832714),
        'xmax': pytest.approx(0.87821229),
        'ymax': pytest.approx(0.74795539),
    }


if __name__ == '__main__':
    kwargs = {
        'hcentrate': True,
        'valign': 1,
        'draw_only_first_tag': True,
    }
    test_display_draw_classif_result(kwargs)
    test_display_draw_detect_result(kwargs)
    test_crop_h()
    test_crop_v()
