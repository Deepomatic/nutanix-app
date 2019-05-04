import os
import io
import textwrap
import logging
from colorsys import rgb_to_hls, hls_to_rgb

from PIL import Image, ImageFont, ImageDraw

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #

# Draw parameters
SCORE_DECIMAL_PRECISION = 4   # Prediction score decimal number precision
FONT_SCALE_PCT = None         # Size of the font we draw in the image_output
BOX_THICKNESS = 5             # Box thickness
TAG_TEXT_CORNER = (10, 10)    # Beginning of text tag column (pixel)
TAG_TEXT_INTERSPACE = 5       # Vertical space between tags in tag column (pixel)

# --------------------------------------------------------------------------- #

# Configure drawing font
def get_color(env_var, default):
    """
    Convert environment variable FONT_COLOR from RRGGBB or RGB in hexadecimal format
    to a tuple (R, G, B).
    """
    color = os.getenv(env_var, None)
    if color is not None:
        try:
            if len(color) == 6:
                return tuple([int(c, 16) for c in textwrap.wrap(color, 2)])
            elif len(color) == 3:
                return tuple([int(c, 16) * 17 for c in color])
        except ValueError:
            pass
        logger.error("Error parsing font color, defaulting to light blue")

    return default

def get_font_size():
    try:
        return int(os.getenv('FONT_SCALE_PCT', 100))
    except ValueError:
        return 100

def adjust_color_lightness(r, g, b, factor):
    h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(min(l * factor, 1.0), 0.0)
    r, g, b = hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)

def lighten_color(r, g, b, factor=0.1):
    return adjust_color_lightness(r, g, b, 1 + factor)

def darken_color(r, g, b, factor=0.1):
    return adjust_color_lightness(r, g, b, 1 - factor)

def set_opacity(r, g, b, opacity):
    a = int(255 * opacity)
    return (r, g, b, a)

FONT_SIZE_RATIO = 1.
FONT_SCALE_PCT = get_font_size()
FONT_SIZE = None
FONT = None
FONT_COLOR = get_color('FONT_COLOR', (255, 255, 255))
BOX_COLOR = get_color('BOX_COLOR', (34, 165, 247))
BACKGROUND_COLOR = darken_color(*BOX_COLOR, factor=0.4)
BACKGROUND_COLOR = set_opacity(*BACKGROUND_COLOR, opacity=0.8)

# --------------------------------------------------------------------------- #

if False:  # use cv2
    import cv2
    import numpy as np

    def set_font(ratio):
        global FONT, FONT_SIZE_RATIO, FONT_SIZE
        FONT_SIZE_RATIO = ratio * FONT_SCALE_PCT / 100
        FONT_SIZE = int(5 * FONT_SIZE_RATIO)
        FONT = cv2.FONT_HERSHEY_SIMPLEX

    def get_text_size(text):
        thickness = max(1, int(FONT_SIZE) * 2)
        ret, baseline_to_bottom = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, FONT_SIZE, thickness)
        return (ret[0], ret[1] + baseline_to_bottom), baseline_to_bottom

    def draw_text(image, text, corner):
        thickness = max(1, int(FONT_SIZE) * 2)
        cv2.putText(image, text, corner, FONT, FONT_SIZE, FONT_COLOR, thickness)

    def draw_box(image, corner1, corner2, color, tickness=1):
        cv2.rectangle(image, corner1, corner2, color, tickness)

    def load_img(image):
        image = cv2.imdecode(np.asarray(bytearray(image), dtype=np.uint8), 1)
        output_image = image.copy()
        height = output_image.shape[0]
        width = output_image.shape[1]
        return image, output_image, width, height

    def save_img(image, output_image):
        retval, buf = cv2.imencode('.jpeg', output_image)
        return buf

else:  # use PIL
    def set_font(ratio):
        global FONT, FONT_SIZE_RATIO, FONT_SIZE
        FONT_SIZE_RATIO = ratio * FONT_SCALE_PCT / 100
        FONT_SIZE = int(48 * FONT_SIZE_RATIO)
        FONT = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "assets", "fonts", "arial.ttf"), FONT_SIZE)

    def get_text_size(text):
        (width, height) = FONT.getsize(text)
        return (width, height), -3

    def draw_text(image, text, corner):
        image.text(corner, text, FONT_COLOR, font=FONT)

    def draw_box(image, corner1, corner2, color, tickness=3):
        image.rectangle([corner1, corner2], color if tickness < 0 else None, outline=color, width=tickness)

    def load_img(image):
        img = Image.open(io.BytesIO(image))
        draw = ImageDraw.Draw(img, mode='RGBA')
        width, height = img.size
        return img, draw, width, height

    def save_img(image, draw):
        with io.BytesIO() as buff:
            image.save(buff, format="JPEG")
            return buff.getvalue()

# --------------------------------------------------------------------------- #

def add_tuple(tuple1, tuple2):
    return tuple(x + y for x, y in zip(tuple1, tuple2))

def get_coordinates_from_roi(roi, width, height):
    bbox = roi['bbox']
    xmin = int(bbox['xmin'] * width)
    ymin = int(bbox['ymin'] * height)
    xmax = int(bbox['xmax'] * width)
    ymax = int(bbox['ymax'] * height)
    return (xmin, ymin, xmax, ymax)

def draw_predictions(image, inference_result, draw_labels=True, draw_scores=False, draw_only_first_tag=True, hcentrate=False, valign=-1):
    img, output_image, width, height = load_img(image)
    tag_drawn = 0
    is_classification = None
    for pred in inference_result['outputs'][0]['labels']['predicted']:
        # Build legend
        label = u''
        if draw_labels:
            label = pred['label_name']
        if draw_labels and draw_scores:
            label += ' '
        if draw_scores:
            label += str(round(pred['score'], SCORE_DECIMAL_PRECISION))
        if label == '':
            continue

        roi = pred.get('roi')
        is_classification = roi is None
        if FONT is None:
            set_font(1 if is_classification else 0.6)

        # Get text draw parameters
        text_size, baseline_offset = get_text_size(label)
        text_offset = (0, baseline_offset)
        text_margin_height = max(1, 0.1 * text_size[1])
        text_margin_width = text_margin_height + 4
        text_margin_x2 = (text_margin_width * 2, text_margin_height * 2)
        text_margin = (text_margin_width, text_margin_height)

        # If we have a bounding box
        if is_classification:
            # First get ideal corners
            vertical_offset = (0, tag_drawn * (text_size[1] + TAG_TEXT_INTERSPACE))
            if hcentrate:
                left = (width - text_size[0] - text_margin_width * 2) / 2
            else:
                left = TAG_TEXT_CORNER[0]
            if valign < 0:
                top = TAG_TEXT_CORNER[1]
            elif valign == 0:
                top = (height - text_size[1]) / 2
            else:
                # We use 3.8/5 for phones to see the label via Nutanix app
                top = height * 3.8 / 5 - text_size[1] / 2
            text_top_left = add_tuple((left, top), vertical_offset)
        else:
            # Retrieve coordinates
            xmin, ymin, xmax, ymax = get_coordinates_from_roi(roi, width, height)

            # Draw bounding box
            draw_box(output_image, (xmin, ymin), (xmax, ymax), BOX_COLOR, tickness=BOX_THICKNESS)

            # Get text top left corner
            if hcentrate:
                left = xmin + (xmax - xmin - text_size[0] - text_margin_width * 2) / 2
            else:
                left = xmin + 10
            text_top_left = (left, ymin + BOX_THICKNESS + 10)

        text_bottom_right = add_tuple(text_top_left, text_size)
        text_corner = add_tuple(text_top_left, text_offset)

        # Then make sure they fit in the image
        # For x-axis, simply shift the box to the left
        # For y-axis, put the label at the top if it doesn't fit under the box
        x_offset = max(0, text_bottom_right[0] - width + 1)
        y_offset = max(0, text_bottom_right[1] - height + 1)
        offset = (-x_offset, -y_offset)
        text_top_left = add_tuple(text_top_left, offset)
        text_bottom_right = add_tuple(add_tuple(text_bottom_right, offset), text_margin_x2)
        text_corner = add_tuple(add_tuple(text_corner, offset), text_margin)

        # Finally draw everything
        draw_box(output_image, text_top_left, text_bottom_right, BACKGROUND_COLOR, -1)
        draw_text(output_image, label, text_corner)
        tag_drawn += 1
        if is_classification and draw_only_first_tag:  # if is_detection is None we should continue
            break

    return save_img(img, output_image)
