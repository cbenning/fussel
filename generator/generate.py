#!/usr/bin/env python3

import os
import shutil
import json
import urllib
from PIL import Image, UnidentifiedImageError
from bs4 import BeautifulSoup
from slugify import slugify

SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.gif', '.png')


class SiteGenerator:
    
    def __init__(self, site_name, input_photos_dir, people_enabled, watermark_enabled, watermark_path, watermark_ratio,
                 recursive_albums, recursive_albums_name_pattern, overwrite):
        self.input_photos_dir = input_photos_dir
        self.people_enabled = people_enabled
        self.watermark_enabled = watermark_enabled
        self.watermark_path = watermark_path
        self.watermark_ratio = watermark_ratio
        self.recursive_albums = recursive_albums
        self.recursive_albums_name_pattern = recursive_albums_name_pattern
        self.overwrite = overwrite
        self.people_data = {}
        self.albums_data = {}
        self.site_data = {
            'site_name': site_name,
            'people_enabled': people_enabled,
        }
        self.unique_album_slugs = {}
        self.unique_person_slugs = {}

    def process_photo(self, external_path, photo, output_dir):
        new_original_photo = os.path.join(output_dir, "original_%s" % os.path.basename(photo))
        
        # Verify original first to avoid PIL errors later when generating thumbnails etc
        try:
            with Image.open(photo) as im:
                im.verify()
            # Unfortunately verify only catches a few defective images, this transpose catches more. Verify requires subsequent reopen according to Pillow docs.
            with Image.open(photo) as im2:
                im2.transpose(Image.FLIP_TOP_BOTTOM)
        except Exception as e:
            raise PhotoProcessingFailure(message="Image Verification: " + str(e))

        # Only copy if overwrite explicitly asked for or if doesn't exist
        if self.overwrite or not os.path.exists(new_original_photo):
            print(" ----> Copying to '%s'" % new_original_photo)
            shutil.copyfile(photo, new_original_photo)

        try:
            with Image.open(new_original_photo) as im:
                original_size = im.size
                x, y = im.size
        except UnidentifiedImageError as e:
            shutil.rmtree(new_original_photo, ignore_errors=True)
            raise PhotoProcessingFailure(message=str(e))

        # TODO expose to config
        sizes = [(500, 500), (800, 800), (1024, 1024), (1600, 1600)]
        filename = os.path.basename(os.path.basename(photo))

        data = {
            'width': x,
            'height': y,
            'name': filename,
            'srcSet': {},
            '_thumb': None,
            'sizes': ["(min-width: 480px) 50vw,(min-width: 1024px) 33.3vw,100vw"]
        }

        largest_src = None
        smallest_src = None

        print(" ------> Generating photo sizes: ", end="")
        for i, size in enumerate(sizes):
            new_size = self.calculate_new_size(original_size, size)
            new_sub_photo = os.path.join(output_dir, "%sx%s_%s" % (new_size[0], new_size[1], os.path.basename(photo)))
            largest_src = new_sub_photo
            if smallest_src is None:
                smallest_src = new_sub_photo

            # Only generate if overwrite explicitly asked for or if doesn't exist
            print(f'{new_size[0]}x{new_size[1]} ', end="")
            if self.overwrite or not os.path.exists(new_sub_photo):
                with Image.open(new_original_photo) as im:
                    im.thumbnail(new_size)
                    im.save(new_sub_photo)
            data['srcSet'][str(size)+"w"] = ["%s/%s" % (urllib.parse.quote(external_path), urllib.parse.quote(os.path.basename(new_sub_photo)))]

        print(' ')

        data['src'] = "%s/%s" % (urllib.parse.quote(external_path), urllib.parse.quote(os.path.basename(largest_src)))
        data['_thumb'] = "%s/%s" % (urllib.parse.quote(external_path), urllib.parse.quote(os.path.basename(smallest_src)))

        # Only copy if overwrite explicitly asked for or if doesn't exist
        if self.watermark_enabled and (self.overwrite or not os.path.exists(new_original_photo)):
            with Image.open(self.watermark_path) as watermark_im:
                print(" ------> Adding watermark")
                self.apply_watermark(largest_src, watermark_im)

        ## Faces
        faces = {}
        if self.people_enabled:
            faces = self.extract_faces(new_original_photo)
            for face in faces.keys():
                print(" ------> Detected face '%s'" % face)

                if not self.person_has_thumbnail(face):
                    with Image.open(largest_src) as im:
                        face_size = faces[face]['geometry']['w'], faces[face]['geometry']['h']
                        face_position = faces[face]['geometry']['x'], faces[face]['geometry']['y']
                        new_face_photo = os.path.join(output_dir, "%s_%s" % (face, os.path.basename(photo)))
                        box = self.calculate_face_crop_dimensions(im.size, face_size, face_position)
                        im_cropped = im.crop(box)
                        im_cropped.save(new_face_photo)
                        uri = "%s/%s" % (external_path, os.path.basename(new_face_photo))
                        self.pick_person_thumbnail(face, uri)

        data['faces'] = faces

        for person in faces:
            self.add_photo_to_person(person, data)

        return data



    def calculate_new_size(self, input_size, desired_size):
        if input_size[0] <= desired_size[0]:
            return input_size
        reduction_factor = input_size[0] / desired_size[0]
        return int(input_size[0] / reduction_factor), int(input_size[1] / reduction_factor)

    def _increase_w(self, left, top, right, bottom, w, h, target_ratio):
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

    def _increase_h(self, left, top, right, bottom, w, h, target_ratio):
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

    def _increase_size(self, left, top, right, bottom, w, h, target_ratio):
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

    def calculate_face_crop_dimensions(self, input_size, face_size, face_position):

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
            left, top, right, bottom = self._increase_w(left, top, right, bottom, input_size[0], input_size[1], target_ratio)
        elif float(right - left + 1 / bottom - top - 1) > target_ratio:  # vertical expansion needed
            left, top, right, bottom = self._increase_h(left, top, right, bottom, input_size[0], input_size[1], target_ratio)

        # attempt to expand photo
        left, top, right, bottom = self._increase_size(left, top, right, bottom, input_size[0], input_size[1], target_upsize_ratio)

        return left, top, right, bottom


    def apply_watermark(self, base_image_path, watermark_image):

        with Image.open(base_image_path) as base_image:
            width, height = base_image.size
            orig_watermark_width, orig_watermark_height = watermark_image.size
            watermark_width = int(width * self.watermark_ratio)
            watermark_height = int(watermark_width/orig_watermark_width * orig_watermark_height)
            watermark_image = watermark_image.resize((watermark_width, watermark_height))
            transparent = Image.new(base_image.mode, (width, height), (0, 0, 0, 0))
            transparent.paste(base_image, (0, 0))

            watermark_x = width - watermark_width
            watermark_y = height - watermark_height
            transparent.paste(watermark_image, box=(watermark_x, watermark_y), mask=watermark_image)
            transparent.save(base_image_path)

    def extract_faces(self, photo_path):
        faces = {}
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
                                    areas = description.findChildren("mwg-rs:area", recursive=False)
                                    for area in areas:
                                        faces[name] = {
                                            'name': name,
                                            'geometry': {
                                                'w': area['starea:w'],
                                                'h': area['starea:h'],
                                                'x': area['starea:x'],
                                                'y': area['starea:y']
                                            }
                                        }

        return faces

    def pick_album_thumbnail(self, album_photos):
        if len(album_photos) > 0:
            return album_photos[0]['_thumb']
        return ''

    def init_person(self, person):
        if not person in self.people_data.keys():

            unique_person_slug = self.find_unique_slug(self.unique_person_slugs, person)
            self.unique_person_slugs[unique_person_slug] = unique_person_slug
            self.people_data[person] = {
                'name': person,
                'slug': unique_person_slug,
                'photos': [],
                'src': None
            }

    def add_photo_to_person(self, person, photo):
        self.init_person(person)
        self.people_data[person]['photos'].append(photo)

    def person_has_thumbnail(self, person):
        self.init_person(person)
        return self.people_data[person]['src'] is not None

    def pick_person_thumbnail(self, person, uri):
        self.init_person(person)
        self.people_data[person]['src'] = uri

    def is_supported_album(self, path):
        folder_name = os.path.basename(path)
        return not folder_name.startswith(".") and os.path.isdir(path)

    def is_supported_photo(self, path):
        return os.path.splitext(path)[1].lower() in SUPPORTED_EXTENSIONS

    def process_album(self, album_dir, album_name, output_albums_photos_path, external_root):

        print(" > Importing album %s as '%s'" % (album_dir, album_name))

        album_photos = []

        unique_album_slug = self.find_unique_slug(self.unique_album_slugs, album_name)
        self.unique_album_slugs[unique_album_slug] = unique_album_slug

        album_data = {
            'name': album_name,
            'slug': unique_album_slug,
            'photos': album_photos
        }

        unique_slugs = {}

        album_name_folder = os.path.basename(album_dir)
        album_folder = os.path.join(output_albums_photos_path, album_name_folder)
        #album_folder = os.path.join(output_albums_photos_path, album_name)
        # TODO externalize this?
        external_path = external_root + "static/_gallery/albums/" + album_name_folder
        #external_path = external_root + "static/_gallery/albums/" + album_name
        os.makedirs(album_folder, exist_ok=True)

        entries = list(map(lambda e: os.path.join(album_dir, e), sorted(os.listdir(album_dir))))
        dirs = list(filter(lambda e: self.is_supported_album(e), entries))
        files = list(filter(lambda e: self.is_supported_photo(e), entries))

        for album_file in files:
            if album_file.startswith('.'):  # skip dotfiles
                continue
            photo_file = os.path.join(album_dir, album_file)
            print(" --> Processing %s... " % photo_file)
            try:
                photo_data = self.process_photo(external_path, photo_file, album_folder)

                ## Ensure slug is unique
                unique_slug = self.find_unique_slug(unique_slugs, photo_data['name'])
                photo_data['slug'] = unique_slug
                unique_slugs[unique_slug] = unique_slug

                album_photos.append(photo_data)
            except PhotoProcessingFailure as e:
                print(f'Skipping processing of image file {photo_file}. Reason: {str(e)}')

        if len(album_data['photos']) > 0:
            album_data['src'] = self.pick_album_thumbnail(album_data['photos'])
            self.albums_data[album_data['slug']] = album_data

        # Recursively process sub-dirs
        if self.recursive_albums:
            for sub_album_dir in dirs:
                if os.path.basename(sub_album_dir).startswith('.'):  # skip dotfiles
                    continue
                sub_album_name = "%s" % self.recursive_albums_name_pattern
                sub_album_name = sub_album_name.replace("{parent_album}", album_name)
                sub_album_name = sub_album_name.replace("{album}", os.path.basename(sub_album_dir))
                self.process_album(sub_album_dir, sub_album_name, output_albums_photos_path, external_root)


    def find_unique_slug(self, unique_slugs, name):

        slug = slugify(name, allow_unicode=False, max_length=30, word_boundary=True, separator="-", save_order=True)
        if slug not in unique_slugs:
            return slug
        count = 1
        while True:
            new_slug = slug + "-" + str(count)
            if new_slug not in unique_slugs:
                return new_slug
            count += 1
        

    def generate_site(self, output_photos_path, output_data_path, external_root):

        # Paths
        output_albums_data_file = os.path.join(output_data_path, "albums_data.js")
        output_people_data_file = os.path.join(output_data_path, "people_data.js")
        output_site_data_file = os.path.join(output_data_path, "site_data.js")
        output_albums_photos_path = os.path.join(output_photos_path, "albums")

        # Cleanup and prep of deploy space
        if self.overwrite:
            shutil.rmtree(output_photos_path, ignore_errors=True)
        os.makedirs(output_photos_path, exist_ok=True)
        shutil.rmtree(output_data_path, ignore_errors=True)
        os.makedirs(output_data_path, exist_ok=True)

        entries = list(map(lambda e: os.path.join(self.input_photos_dir, e), os.listdir(self.input_photos_dir)))
        dirs = list(filter(lambda e: self.is_supported_album(e), entries))

        for album_dir in dirs:
            album_name = os.path.basename(album_dir)
            if album_name.startswith('.'):  # skip dotfiles
                continue
            self.process_album(album_dir, album_name, output_albums_photos_path, external_root)

        people_data_slugs = {}
        for person in self.people_data.values():
            people_data_slugs[person['slug']] = person

        with open(output_albums_data_file, 'w') as outfile:
            output_str = 'export const albums_data = '
            output_str += json.dumps(self.albums_data, sort_keys=True, indent=4)
            output_str += ';'
            outfile.write(output_str)

        with open(output_people_data_file, 'w') as outfile:
            output_str = 'export const people_data = '
            output_str += json.dumps(people_data_slugs, sort_keys=True, indent=4)
            output_str += ';'
            outfile.write(output_str)

        with open(output_site_data_file, 'w') as outfile:
            output_str = 'export const site_data = '
            output_str += json.dumps(self.site_data, sort_keys=True, indent=4)
            output_str += ';'
            outfile.write(output_str)


class PhotoProcessingFailure(Exception):
    def __init__(self, message="Failed to process photo"):
        self.message = message
        super().__init__(self.message)
