

from PIL import Image
from slugify import slugify
from .config import *
import os


def is_supported_album(path):
    folder_name = os.path.basename(path)
    return not folder_name.startswith(".") and os.path.isdir(path)


def extract_extension(path):
    return os.path.splitext(path)[1].lower()

def is_supported_photo(path):
    ext = extract_extension(path)
    return ext in Config.instance().supported_extensions


def find_unique_slug(unique_slugs, name):

    slug = slugify(name, allow_unicode=False, max_length=30,
                   word_boundary=True, separator="-", save_order=True)
    if slug not in unique_slugs:
        return slug
    count = 1
    while True:
        new_slug = slug + "-" + str(count)
        if new_slug not in unique_slugs:
            return new_slug
        count += 1


def calculate_new_size(input_size, desired_size):
    if input_size[0] <= desired_size[0]:
        return input_size
    reduction_factor = input_size[0] / desired_size[0]
    return int(input_size[0] / reduction_factor), int(input_size[1] / reduction_factor)


def increase_w(left, top, right, bottom, w, h, target_ratio):
    # print("increase width")
    f_l = left
    f_r = right
    f_w = f_r - f_l
    f_h = bottom - top
    next_step_ratio = float((f_w+1)/f_h)
    # print("%d/%d = %f = %f" % (f_w, f_h, next_step_ratio, target_ratio))
    while next_step_ratio < target_ratio and f_l-1 > 0 and f_r+1 < w:
        f_l -= 1
        f_r += 1
        f_w = f_r - f_l
        next_step_ratio = float((f_w+1)/f_h)
        # print("%d/%d = %f = %f" % (f_w, f_h, next_step_ratio, target_ratio))
    return (f_l, top, f_r, bottom)


def increase_h(left, top, right, bottom, w, h, target_ratio):
    # print("increase height")
    f_t = top
    f_b = bottom
    f_w = right - left
    f_h = f_b - f_t
    next_step_ratio = float((f_w+1)/f_h)
    # print("%d/%d = %f = %f" % (f_w, f_h, next_step_ratio, target_ratio))
    while next_step_ratio > target_ratio and f_t-1 > 0 and f_b+1 < h:
        f_t -= 1
        f_b += 1
        f_w = f_b - f_t
        next_step_ratio = float((f_w+1)/f_h)
        # print("%d/%d = %f = %f" % (f_w, f_h, next_step_ratio, target_ratio))
    return (left, f_t, right, f_b)


def increase_size(left, top, right, bottom, w, h, target_ratio):
    # print("increase size")
    f_t = top
    f_b = bottom
    f_l = left
    f_r = right
    f_w = f_r - f_l
    original_f_w = f_r - f_l
    f_h = f_b - f_t
    # print("%d/%d = %f = %f" % (f_w, f_h, float((f_w + 1) / original_f_w), target_ratio))
    next_step_ratio = float((f_w + 1) / original_f_w)
    while next_step_ratio < target_ratio and f_t-1 > 0 and f_b+1 < h and f_l-1 > 0 and f_r+1 < w:
        f_t -= 1
        f_b += 1
        f_l -= 1
        f_r += 1
        f_w = f_r - f_l
        f_h = f_b - f_t
        next_step_ratio = float((f_w + 1) / original_f_w)
        # print("%d/%d = %f = %f" % (f_w, f_h, float((f_w + 1) / original_f_w), target_ratio))
    return (f_l, f_t, f_r, f_b)


def calculate_face_crop_dimensions(input_size, face_size, face_position):

    target_ratio = float(4/3)
    target_upsize_ratio = float(2.5)

    x = int(input_size[0] * float(face_position[0]))
    y = int(input_size[1] * float(face_position[1]))
    w = int(input_size[0] * float(face_size[0]))
    h = int(input_size[1] * float(face_size[1]))

    left = x - int(w/2) + 1
    right = x + int(w/2) - 1
    top = y - int(h/2) + 1
    bottom = y + int(h/2) - 1

    # try to increase
    if float(right - left + 1 / bottom - top - 1) < target_ratio:  # horizontal expansion needed
        left, top, right, bottom = increase_w(
            left, top, right, bottom, input_size[0], input_size[1], target_ratio)
    elif float(right - left + 1 / bottom - top - 1) > target_ratio:  # vertical expansion needed
        left, top, right, bottom = increase_h(
            left, top, right, bottom, input_size[0], input_size[1], target_ratio)

    # attempt to expand photo
    left, top, right, bottom = increase_size(
        left, top, right, bottom, input_size[0], input_size[1], target_upsize_ratio)

    return left, top, right, bottom


def apply_watermark(base_image_path, watermark_image, watermark_ratio):

    with Image.open(base_image_path) as base_image:
        width, height = base_image.size
        orig_watermark_width, orig_watermark_height = watermark_image.size
        watermark_width = int(width * watermark_ratio)
        watermark_height = int(
            watermark_width/orig_watermark_width * orig_watermark_height)
        watermark_image = watermark_image.resize(
            (watermark_width, watermark_height))
        transparent = Image.new(base_image.mode, (width, height), (0, 0, 0, 0))
        transparent.paste(base_image, (0, 0))

        watermark_x = width - watermark_width
        watermark_y = height - watermark_height
        transparent.paste(watermark_image, box=(
            watermark_x, watermark_y), mask=watermark_image)
        transparent.save(base_image_path)


def pick_album_thumbnail(album_photos):
    if len(album_photos) > 0:
        return album_photos[0].thumb
    return ''
