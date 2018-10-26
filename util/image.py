from wand.image import Image
from PIL.Image import ANTIALIAS as antialias

# The image orientation viewed in terms of rows and columns.
# 274 is exif tag code for orientation
# ref: https://github.com/python-pillow/Pillow/blob/master/PIL/ExifTags.py#L40
# http://www.exiv2.org/tags.html
EXIF_IMAGE_ORIENTATION = 274

# TODO explain a bit what this is about, e.g. why 3 --> 180
# This is exif tag coding, it is exif convention
ROTATION_MAP = {
    3: 180,
    6: 270,
    8: 90,
}


def rotate_jpg_from_exif(image):
    """
    If the image's ``exif`` data does not exist, has no orientation, or the
    orientation isn't one defined in the ``ROTATION_MAP``, just return the
    original image

    """
    exif_dict = image._getexif()

    try:
        image_orientation = exif_dict[EXIF_IMAGE_ORIENTATION]
    except (KeyError, TypeError):
        return image
    try:
        rotation = ROTATION_MAP[image_orientation]
    except KeyError:
        return image

    return image.rotate(rotation, expand=True)


def get_new_size_with_aspect_ratio(original_size, desired_size):
    if original_size[0] < desired_size[0] and original_size[1] < desired_size[1]:
        return tuple(original_size)
    original_size, desired_size = map(float, original_size), map(float, desired_size)
    img_ratio = original_size[0] / original_size[1]
    if img_ratio > 1:
        new_size = [int(desired_size[0]), int(round(desired_size[0] * original_size[1] / original_size[0]))]
    elif img_ratio < 1:
        new_size = [int(round(desired_size[0] * img_ratio)), int(desired_size[1])]
    else:
        new_size = map(int, desired_size)
    return tuple(new_size)


def resize_single_image_with_ratio(image, desired_size):
    new_size = get_new_size_with_aspect_ratio(image.size, desired_size)
    return image.resize(new_size, antialias)


def resize_gif_with_ratio(image, desired_size, destination):
    new_size = get_new_size_with_aspect_ratio(image.size, desired_size)
    with Image(filename=image.filename) as im:
        im.resize(new_size[0], new_size[1])
        im.save(destination)
    return destination
