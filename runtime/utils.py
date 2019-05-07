import io
import numpy as np
from PIL import Image, ImageOps

def crop_and_dump(image, aspect_ratio):
    image, change_of_basis_matrix = crop(image, aspect_ratio)
    with io.BytesIO() as buff:
        image.save(buff, format="JPEG")
        return buff.getvalue(), change_of_basis_matrix

def crop(image, aspect_ratio):
    image = Image.open(io.BytesIO(image))
    W, H = image.size
    current_aspect_ratio = W / H

    # w, h are solutions of:
    # w / h = aspect_ratio
    # w - W = H - h   (or W - w = h - H --> same equation)
    # The solution is:
    h = int(round((W + H) / (aspect_ratio + 1)))
    w = int(round(h * aspect_ratio))

    if current_aspect_ratio < aspect_ratio:
        image, change_of_basis_matrix = crop_V_pad_H(image, w, h)
    else:
        image, change_of_basis_matrix = crop_H_pad_V(image, w, h)

    denorm_old_basis = np.array([
        [W, 0, 0],
        [0, H, 0],
        [0, 0, 1]
    ])
    norm_new_basis = np.array([
        [1. / w, 0,      0],
        [0,      1. / h, 0],
        [0,       0,     1]
    ])
    change_of_basis_matrix = np.dot(np.dot(norm_new_basis, change_of_basis_matrix), denorm_old_basis)

    return image, change_of_basis_matrix

def crop_V_pad_H(image, w, h):
    W, H = image.size
    ymin = int((H - h) / 2)
    ymax = ymin + h
    assert ymin >= 0
    assert ymax <= H

    offset = int((w - W) / 2)
    rest = w - W - offset
    assert offset >= 0
    assert rest >= 0

    new_image = Image.new('RGB', (w, h))
    image = image.crop((0, ymin, W, ymax))
    assert (W, h) == image.size

    new_image.paste(ImageOps.mirror(image.crop((0, 0, offset, h))), (0, 0))
    new_image.paste(image, (offset, 0))
    new_image.paste(ImageOps.mirror(image.crop((W - rest, 0, W, h))), (offset + W, 0))

    # Compute new coordinate system for bboxes
    change_of_basis_matrix = np.array([
        [1, 0, offset],
        [0, 1,  -ymin],
        [0, 0,      1]
    ])

    return new_image, change_of_basis_matrix

def crop_H_pad_V(image, w, h):
    W, H = image.size
    xmin = int((W - w) / 2)
    xmax = xmin + w
    assert xmin >= 0
    assert xmax <= W

    offset = int((h - H) / 2)
    rest = h - H - offset
    assert offset >= 0
    assert rest >= 0

    new_image = Image.new('RGB', (w, h))
    image = image.crop((xmin, 0, xmax, H))
    assert (w, H) == image.size

    new_image.paste(ImageOps.flip(image.crop((0, 0, w, offset))), (0, 0))
    new_image.paste(image, (0, offset))
    new_image.paste(ImageOps.flip(image.crop((0, H - rest, w, H))), (0, offset + H))

    # Compute new coordinate system for bboxes
    change_of_basis_matrix = np.array([
        [1, 0,  -xmin],
        [0, 1, offset],
        [0, 0,      1]
    ])

    return new_image, change_of_basis_matrix

def normalize_roi(roi, change_of_basis_matrix):
    def clip_coord(c):
        return min(max(c, 0), 1)

    def normalize_point(x, y):
        p = np.array([x, y, 1]).reshape((3, 1))
        p = np.dot(change_of_basis_matrix, p)
        return clip_coord(p[0] / p[2]), clip_coord(p[1] / p[2])

    bbox = roi['bbox']
    bbox['xmin'], bbox['ymin'] = normalize_point(bbox['xmin'], bbox['ymin'])
    bbox['xmax'], bbox['ymax'] = normalize_point(bbox['xmax'], bbox['ymax'])
