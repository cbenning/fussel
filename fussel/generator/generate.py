#!/usr/bin/env python3

import os
import shutil
import json
import urllib
from PIL import Image, UnidentifiedImageError
from bs4 import BeautifulSoup
from slugify import slugify
from dataclasses import dataclass


# 1. input dir
#    2. for each dir
#         3. create album
#             for each file:
#                 add as file
#                 add as person
#             for each dir:
#                 goto #3

SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.gif', '.png')
DEFAULT_WATERMARK_PATH = 'web/src/images/fussel-watermark.png'
DEFAULT_WATERMARK_SIZE_RATIO = 0.3
DEFAULT_RECURSIVE_ALBUMS_NAME_PATTERN = '{parent_album} > {album}'
DEFAULT_OUTPUT_PHOTOS_PATH = 'site/'
DEFAULT_SITE_TITLE = 'Fussel Gallery'


class SiteConfig:

    def __init__(self, yamlConfig):

        self.input_photos_dir = yamlConfig.getKey('gallery.input_path')
        self.people_enabled = yamlConfig.getKey('gallery.people.enable', True)
        self.watermark_enabled = yamlConfig.getKey(
            'gallery.watermark.enable', True)
        self.watermark_path = yamlConfig.getKey(
            'gallery.watermark.path', DEFAULT_WATERMARK_PATH)
        self.watermark_ratio = yamlConfig.getKey(
            'gallery.watermark.size_ratio', DEFAULT_WATERMARK_SIZE_RATIO)
        self.recursive_albums = yamlConfig.getKey(
            'gallery.albums.recursive', True)
        self.recursive_albums_name_pattern = yamlConfig.getKey(
            'gallery.albums.recursive_name_pattern', DEFAULT_RECURSIVE_ALBUMS_NAME_PATTERN)
        self.overwrite = yamlConfig.getKey('gallery.overwrite', False)
        self.output_photos_path = yamlConfig.getKey(
            'gallery.output_path', DEFAULT_OUTPUT_PHOTOS_PATH)
        self.http_root = yamlConfig.getKey('site.http_root', '/')
        self.site_name = yamlConfig.getKey('site.title', DEFAULT_SITE_TITLE)


def is_supported_album(path):
    folder_name = os.path.basename(path)
    return not folder_name.startswith(".") and os.path.isdir(path)


def is_supported_photo(path):
    ext = os.path.splitext(path)[1].lower()
    return ext in SUPPORTED_EXTENSIONS
    # return os.path.splitext(path)[0].lower() in SUPPORTED_EXTENSIONS


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


def extract_faces(photo_path):
    faces =[] 
    with Image.open(photo_path) as im:
        for segment, content in im.applist:
            marker, body = content.split(bytes('\x00', 'utf-8'), 1)
            if segment == 'APP1' and marker.decode("utf-8") == 'http://ns.adobe.com/xap/1.0/':
                body_str = body.decode("utf-8")
                soup = BeautifulSoup(body_str, 'html.parser')

                for regions in soup.find_all("mwg-rs:regions"):

                    for regionlist in regions.find_all("mwg-rs:regionlist"):
                        for description in regionlist.find_all("rdf:description"):
                            if description['mwg-rs:type'] == 'Face':
                                name = description['mwg-rs:name'].strip()
                                areas = description.findChildren(
                                    "mwg-rs:area", recursive=False)
                                for area in areas:
                                    faces.append(Face(
                                        name=name,
                                        geometry=FaceGeometry(
                                            w= area['starea:w'],
                                            h= area['starea:h'],
                                            x= area['starea:x'],
                                            y= area['starea:y']
                                        )
                                    ))
                                    # faces[name] = {
                                    #     'name': name,
                                    #     'geometry': {
                                    #         'w': area['starea:w'],
                                    #         'h': area['starea:h'],
                                    #         'x': area['starea:x'],
                                    #         'y': area['starea:y']
                                    #     }
                                    # }
    return faces


def pick_album_thumbnail(album_photos):
    if len(album_photos) > 0:
        return album_photos[0].thumb
    return ''


class SimpleEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


class Site:
    def __init__(self, config):
        self.site_name = config.site_name
        self.people_enabled = config.people_enabled


@dataclass
class FaceGeometry:
    w: str
    h: str
    x: str
    y: str


@dataclass
class Face:
    name: str
    geometry: FaceGeometry


class People:

    def __init__(self, config):
        self.config = config
        self.people: dict = {}
        self.slugs: dict = set()

    def detect_faces(self, photo, original_src, largest_src, output_path, external_path):

        faces = extract_faces(original_src)
        for face in faces:
            print(" ------> Detected face '%s'" % face)

            if face.name not in self.people.keys():

                unique_person_slug = find_unique_slug(self.slugs, face.name)
                self.slugs.add(unique_person_slug)
                    # self.people_data[person] = {
                    #     'name': person,
                    #     'slug': unique_person_slug,
                    #     'photos': [],
                    #     'src': None
                    # }
                self.people[face.name] = Person(face.name, unique_person_slug)

            person = self.people[face.name]
            person.photos.append(photo)
            # photo_people.append(person)

            if not person.hasThumbnail():
                with Image.open(largest_src) as im:
                    
                    face_size = face.geometry.w, face.geometry.h
                    face_position = face.geometry.x, face.geometry.y
                    new_face_photo = os.path.join(
                        output_path, "%s_%s" % (person.slug, os.path.basename(original_src)))
                    box = calculate_face_crop_dimensions(
                        im.size, face_size, face_position)
                    im_cropped = im.crop(box)
                    im_cropped.save(new_face_photo)
                    person.src = "%s/%s" % (external_path,
                                        os.path.basename(new_face_photo))
                    # self.pick_person_thumbnail(face, uri)
            
        return faces


    # implemented to allow this class to be iterated on
    def __getitem__(self, item):
        return list(self.people.values())[item] 


class Person:

    def __init__(self, name, slug):

        self.name = name
        self.slug = slug
        self.src = None
        self.photos: list = []


    def hasThumbnail(self):
        return self.src is not None



class Photo:

    def __init__(self, name, width, height, src, thumb, srcSet):

        self.width = width
        self.height = height
        self.name = name
        self.src = src
        self.thumb = thumb
        self.srcSet = srcSet
        self.faces: list = []
        self.slug: str
        # 'sizes': ["(min-width: 480px) 50vw,(min-width: 1024px) 33.3vw,100vw"]
        

class Albums:

    def __init__(self, config):
        self.config = config
        self.slugs: dict = set()
        self.albums: dict = {}

    def add_album(self, album):
        self.albums[album.slug] = album

    def __getitem__(self, item):
        return list(self.albums.values())[item] 


class Album:

    def __init__(self, name, slug):
        self.name = name
        self.slug = slug
        self.photos:list = []
        self.src: str = None

    def add_photo(self, photo):
        self.photos.append(photo)

class SiteGenerator:

    def __init__(self, yamlConfig):

        self.config = SiteConfig(yamlConfig)

        self.site = Site(self.config)

        self.people = People(self.config)
        self.albums = Albums(self.config)
        # self.people_data = {}
        # self.albums_data = {}

        # self.site_data = {
        #     'site_name': self.site_name,
        #     'people_enabled': self.people_enabled,
        # }
        self.unique_album_slugs = {}
        self.unique_person_slugs = {}

    def generate(self):

        output_photos_path = os.path.normpath(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "..", "web", "public", "static", "_gallery"))
        output_data_path = os.path.normpath(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "..", "web", "src", "_gallery"))
        external_root = os.path.normpath(os.path.join(
            self.config.http_root, "..", "static", "_gallery", "albums"))

        # Paths
        output_albums_data_file = os.path.join(
            output_data_path, "albums_data.js")
        output_people_data_file = os.path.join(
            output_data_path, "people_data.js")
        output_site_data_file = os.path.join(output_data_path, "site_data.js")
        output_albums_photos_path = os.path.join(output_photos_path, "albums")

        # Cleanup and prep of deploy space
        if self.config.overwrite:
            shutil.rmtree(output_photos_path, ignore_errors=True)
        os.makedirs(output_photos_path, exist_ok=True)
        shutil.rmtree(output_data_path, ignore_errors=True)
        os.makedirs(output_data_path, exist_ok=True)

        entries = list(map(lambda e: os.path.join(
            self.config.input_photos_dir, e), os.listdir(self.config.input_photos_dir)))
        dirs = list(filter(lambda e: is_supported_album(e), entries))

        for album_dir in dirs:
            album_name = os.path.basename(album_dir)
            if album_name.startswith('.'):  # skip dotfiles
                continue
            self.process_album(album_dir, album_name,
                               output_albums_photos_path, external_root)

        people_data_slugs = {}
        for person in self.people:
            people_data_slugs[person.slug] = person

        with open(output_albums_data_file, 'w') as outfile:
            output_str = 'export const albums_data = '
            # output_str += json.dumps(self.albums_data,
                                    #  sort_keys=True, indent=3)

            output_str += json.dumps(self.albums.albums, sort_keys=True,
                                     indent=3, cls=SimpleEncoder)
            output_str += ';'
            outfile.write(output_str)

        with open(output_people_data_file, 'w') as outfile:
            output_str = 'export const people_data = '
            # output_str += json.dumps(people_data_slugs,
            #                          sort_keys=True, indent=3)
            output_str += json.dumps(people_data_slugs, sort_keys=True,
                            indent=3, cls=SimpleEncoder)
            output_str += ';'
            outfile.write(output_str)

        with open(output_site_data_file, 'w') as outfile:
            output_str = 'export const site_data = '
            # output_str += json.dumps(self.site_data, sort_keys=True, indent=3)
            output_str += json.dumps(self.site, sort_keys=True,
                                     indent=3, cls=SimpleEncoder)
            output_str += ';'
            outfile.write(output_str)

    def process_photo(self, external_path, photo, output_path):
        new_original_photo = os.path.join(
            output_path, "original_%s" % os.path.basename(photo))

        # Verify original first to avoid PIL errors later when generating thumbnails etc
        try:
            with Image.open(photo) as im:
                im.verify()
            # Unfortunately verify only catches a few defective images, this transpose catches more. Verify requires subsequent reopen according to Pillow docs.
            with Image.open(photo) as im2:
                im2.transpose(Image.FLIP_TOP_BOTTOM)
        except Exception as e:
            raise PhotoProcessingFailure(
                message="Image Verification: " + str(e))

        # Only copy if overwrite explicitly asked for or if doesn't exist
        if self.config.overwrite or not os.path.exists(new_original_photo):
            print(" ----> Copying to '%s'" % new_original_photo)
            shutil.copyfile(photo, new_original_photo)

        try:
            with Image.open(new_original_photo) as im:
                original_size = im.size
                width, height = im.size
        except UnidentifiedImageError as e:
            shutil.rmtree(new_original_photo, ignore_errors=True)
            raise PhotoProcessingFailure(message=str(e))

        # TODO expose to config
        sizes = [(500, 500), (800, 800), (1024, 1024), (1600, 1600)]
        filename = os.path.basename(os.path.basename(photo))

        # data = {
        #     'width': x,
        #     'height': y,
        #     'name': filename,
        #     'srcSet': {},
        #     '_thumb': None,
        #     'sizes': ["(min-width: 480px) 50vw,(min-width: 1024px) 33.3vw,100vw"]
        # }

        largest_src = None
        smallest_src = None

        srcSet = {}

        print(" ------> Generating photo sizes: ", end="")
        for i, size in enumerate(sizes):
            new_size = calculate_new_size(original_size, size)
            new_sub_photo = os.path.join(output_path, "%sx%s_%s" % (
                new_size[0], new_size[1], os.path.basename(photo)))
            largest_src = new_sub_photo
            if smallest_src is None:
                smallest_src = new_sub_photo

            # Only generate if overwrite explicitly asked for or if doesn't exist
            print(f'{new_size[0]}x{new_size[1]} ', end="")
            if self.config.overwrite or not os.path.exists(new_sub_photo):
                with Image.open(new_original_photo) as im:
                    im.thumbnail(new_size)
                    im.save(new_sub_photo)
            # data['srcSet'][str(size)+"w"] = ["%s/%s" % (urllib.parse.quote(
                # external_path), urllib.parse.quote(os.path.basename(new_sub_photo)))]
            srcSet[str(size)+"w"] = ["%s/%s" % (urllib.parse.quote(
                external_path), urllib.parse.quote(os.path.basename(new_sub_photo)))]

        print(' ')

        # data['src'] = "%s/%s" % (urllib.parse.quote(external_path),
        #                          urllib.parse.quote(os.path.basename(largest_src)))
        # data['_thumb'] = "%s/%s" % (urllib.parse.quote(external_path),
        #                             urllib.parse.quote(os.path.basename(smallest_src)))

     

        # Only copy if overwrite explicitly asked for or if doesn't exist
        if self.config.watermark_enabled and (self.config.overwrite or not os.path.exists(new_original_photo)):
            with Image.open(self.watermark_path) as watermark_im:
                print(" ------> Adding watermark")
                apply_watermark(largest_src, watermark_im,
                                self.watermark_ratio)




        photo_obj = Photo(
            filename,
            width,
            height,
            "%s/%s" % (urllib.parse.quote(external_path),
                        urllib.parse.quote(os.path.basename(largest_src))),
            "%s/%s" % (urllib.parse.quote(external_path),
                        urllib.parse.quote(os.path.basename(smallest_src))),
            srcSet
        ) 

        # Faces
        if self.config.people_enabled:
            photo_obj.faces = self.people.detect_faces(photo_obj, new_original_photo, largest_src, output_path, external_path)
            # faces = extract_faces(new_original_photo)
            # for face in faces.keys():
            #     print(" ------> Detected face '%s'" % face)

            #     if not self.person_has_thumbnail(face):
            #         with Image.open(largest_src) as im:
            #             face_size = faces[face]['geometry']['w'], faces[face]['geometry']['h']
            #             face_position = faces[face]['geometry']['x'], faces[face]['geometry']['y']
            #             new_face_photo = os.path.join(
            #                 output_path, "%s_%s" % (face, os.path.basename(photo)))
            #             box = calculate_face_crop_dimensions(
            #                 im.size, face_size, face_position)
            #             im_cropped = im.crop(box)
            #             im_cropped.save(new_face_photo)
            #             uri = "%s/%s" % (external_path,
            #                              os.path.basename(new_face_photo))
            #             self.pick_person_thumbnail(face, uri)



        # data['faces'] = faces

        # for person in faces:
        #     self.add_photo_to_person(person, data)

        return photo_obj

    # def init_person(self, person):
    #     if not person in self.people_data.keys():

    #         unique_person_slug = find_unique_slug(
    #             self.unique_person_slugs, person)
    #         self.unique_person_slugs[unique_person_slug] = unique_person_slug
    #         self.people_data[person] = {
    #             'name': person,
    #             'slug': unique_person_slug,
    #             'photos': [],
    #             'src': None
    #         }

    # def add_photo_to_person(self, person, photo):
    #     self.init_person(person)
    #     self.people_data[person]['photos'].append(photo)

    # def person_has_thumbnail(self, person):
    #     self.init_person(person)
    #     return self.people_data[person]['src'] is not None

    # def pick_person_thumbnail(self, person, uri):
    #     self.init_person(person)
    #     self.people_data[person]['src'] = uri

    def process_album(self, album_dir, album_name, output_albums_photos_path, external_root):

        print(" > Importing album %s as '%s'" % (album_dir, album_name))

        # album_photos = []

        unique_album_slug = find_unique_slug(self.unique_album_slugs, album_name)
        self.unique_album_slugs[unique_album_slug] = unique_album_slug

        album_obj = Album(album_name, unique_album_slug)
        # album_data = {
        #     'name': album_name,
        #     'slug': unique_album_slug,
        #     'photos': album_photos
        # }

        unique_slugs = {}

        album_name_folder = os.path.basename(album_dir)
        album_folder = os.path.join(
            output_albums_photos_path, album_name_folder)
        # album_folder = os.path.join(output_albums_photos_path, album_name)
        # TODO externalize this?
        external_path = os.path.join(external_root, album_name_folder)
        # external_path = external_root + "static/_gallery/albums/" + album_name_folder
        os.makedirs(album_folder, exist_ok=True)

        entries = list(map(lambda e: os.path.join(album_dir, e), sorted(os.listdir(album_dir))))
        dirs = list(filter(lambda e: is_supported_album(e), entries))
        files = list(filter(lambda e: is_supported_photo(e), entries))

        for album_file in files:
            if album_file.startswith('.'):  # skip dotfiles
                continue
            photo_file = os.path.join(album_dir, album_file)
            print(" --> Processing %s... " % photo_file)
            try:
                photo_obj = self.process_photo(
                    external_path, photo_file, album_folder)

                # Ensure slug is unique
                unique_slug = find_unique_slug(
                    unique_slugs, photo_obj.name)
                photo_obj.slug = unique_slug
                unique_slugs[unique_slug] = unique_slug

                album_obj.add_photo(photo_obj)
            except PhotoProcessingFailure as e:
                print(
                    f'Skipping processing of image file {photo_file}. Reason: {str(e)}')

        if len(album_obj.photos) > 0:
            album_obj.src = pick_album_thumbnail(album_obj.photos) ## TODO internalize
            self.albums.add_album(album_obj)

        # Recursively process sub-dirs
        if self.config.recursive_albums:
            for sub_album_dir in dirs:
                if os.path.basename(sub_album_dir).startswith('.'):  # skip dotfiles
                    continue
                sub_album_name = "%s" % self.recursive_albums_name_pattern
                sub_album_name = sub_album_name.replace(
                    "{parent_album}", album_name)
                sub_album_name = sub_album_name.replace(
                    "{album}", os.path.basename(sub_album_dir))
                self.process_album(sub_album_dir, sub_album_name,
                                   output_albums_photos_path, external_root)


class PhotoProcessingFailure(Exception):
    def __init__(self, message="Failed to process photo"):
        self.message = message
        super().__init__(self.message)
