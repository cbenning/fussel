#!/usr/bin/env python3

import os
import shutil
import json
from PIL import Image
from bs4 import BeautifulSoup

SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.gif', '.png')

class SiteGenerator:
    
    def __init__(self, site_name, input_photos_dir, people_enabled, watermark_enabled, watermark_path, watermark_ratio):
        self.input_photos_dir = input_photos_dir
        self.people_enabled = people_enabled
        self.watermark_enabled = watermark_enabled
        self.watermark_path = watermark_path
        self.watermark_ratio = watermark_ratio
        self.people_data = {}
        self.albums_data = {}
        self.site_data = {
            'site_name': site_name
        }

    def process_photo(self, external_path, photo, output_dir):
        new_original_photo = os.path.join(output_dir, "original_%s" % os.path.basename(photo))
        print(" ----> Copying to '%s'" % new_original_photo)
        shutil.copyfile(photo, new_original_photo)

        ## Faces
        faces = []
        if self.people_enabled:
            faces = self.extract_faces(new_original_photo)
            for face in faces:
                print(" ------> Detected face '%s'" % face)

        with Image.open(new_original_photo) as im:
            original_size = im.size
            x, y = im.size
            #denominator = gcd(x, y)
            #x = int(x / denominator)
            #y = int(y / denominator)


        # TODO expose to config
        sizes = [(500, 500), (800, 800), (1024, 1024), (1600, 1600)]

        data = {
            'width': x,
            'height': y,
            'name': os.path.basename(os.path.basename(photo)),
            'srcSet': [],
            '_thumb': None,
            'sizes': ["(min-width: 480px) 50vw,(min-width: 1024px) 33.3vw,100vw"],
        }

        largest_src = None
        smallest_src = None
        for i, size in enumerate(sizes):
            new_size = self.calculate_new_size(original_size, size)
            new_sub_photo = os.path.join(output_dir, "%sx%s_%s" % (new_size[0], new_size[1], os.path.basename(photo)))
            largest_src = new_sub_photo
            if smallest_src is None:
                smallest_src = new_sub_photo
            print(" ------> Generating photo size... '%s'" % new_sub_photo)
            with Image.open(new_original_photo) as im:
                im.thumbnail(new_size)
                im.save(new_sub_photo)
                data['srcSet'] += ["%s/%s %sw" % (external_path, os.path.basename(new_sub_photo), new_size[0])]

        data['src'] = "%s/%s" % (external_path, os.path.basename(largest_src))
        data['_thumb'] = "%s/%s" % (external_path, os.path.basename(smallest_src))

        if self.watermark_enabled:
            with Image.open(self.watermark_path) as watermark_im:
                print(" ------> Adding watermark ... '%s'" % largest_src)
                self.apply_watermark(largest_src, watermark_im)

        return faces, data

    def calculate_new_size(self, input_size, desired_size):
        if input_size[0] <= desired_size[0]:
            return input_size
        reduction_factor = input_size[0] / desired_size[0]
        return int(input_size[0] / reduction_factor), int(input_size[1] / reduction_factor)

    def apply_watermark(self, base_image_path, watermark_image):

        with Image.open(base_image_path) as base_image:
            width, height = base_image.size
            orig_watermark_width, orig_watermark_height = watermark_image.size
            watermark_width = int(width * self.watermark_ratio)
            watermark_height = int(watermark_width/orig_watermark_width * orig_watermark_height)
            # watermark_width, watermark_height = (int(width * self.watermark_ratio), int(height * self.watermark_ratio))
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
                                    faces[name] = ''
        return faces.keys()

    def pick_album_thumbnail(self, album_photos):
        if len(album_photos) > 0:
            return album_photos[0]['_thumb']
        return ''

    def add_photo_to_person(self, person, photo):
        if not person in self.people_data.keys():
            self.people_data[person] = {
                'name': person,
                'photos': []
            }
        self.people_data[person]['photos'].append(photo)

    def generate_site(self, output_photos_path, output_data_path, external_root):

        # Paths
        output_albums_data_file = os.path.join(output_data_path, "albums_data.js")
        output_people_data_file = os.path.join(output_data_path, "people_data.js")
        output_site_data_file = os.path.join(output_data_path, "site_data.js")
        output_albums_photos_path = os.path.join(output_photos_path, "albums")

        # Cleanup and prep of deploy space
        shutil.rmtree(output_photos_path, ignore_errors=True)
        os.makedirs(output_photos_path, exist_ok=True)
        shutil.rmtree(output_data_path, ignore_errors=True)
        os.makedirs(output_data_path, exist_ok=True)

        for subdir, input_album_dirs, files in os.walk(self.input_photos_dir):
            for input_album_dir in input_album_dirs:
                album_dir = os.path.join(subdir, input_album_dir)
                album_name = os.path.basename(input_album_dir)
                if not album_name.startswith(".") and os.path.isdir(album_dir):
                    print(" > Importing album %s as '%s'" % (album_dir, album_name))

                    album_photos = []
                    album_data = {
                        'name': album_name,
                        'photos': album_photos
                    }

                    album_folder = os.path.join(output_albums_photos_path, album_name)
                    # TODO externalize this?
                    external_path = external_root + "static/_gallery/albums/" + album_name
                    os.makedirs(album_folder)

                    for _, _, album_files in os.walk(album_dir):
                        for album_file in album_files:
                            if not os.path.splitext(album_file)[1].lower() in SUPPORTED_EXTENSIONS:
                                continue
                            photo_file = os.path.join(album_dir, album_file)
                            print(" --> Processing %s... " % photo_file)
                            faces, photo_data = self.process_photo(external_path, photo_file, album_folder)

                            for person in faces:
                                self.add_photo_to_person(person, photo_data)
                            album_photos.append(photo_data)

                    album_data['src'] = self.pick_album_thumbnail(album_data['photos'])
                    self.albums_data[album_data['name']] = album_data

        for person_name in self.people_data.keys():
            self.people_data[person_name]['src'] = self.pick_album_thumbnail(self.people_data[person_name]['photos'])

        with open(output_albums_data_file, 'w') as outfile:
            output_str = 'export const albums_data = '
            output_str += json.dumps(self.albums_data, sort_keys=True, indent=4)
            output_str += ';'
            outfile.write(output_str)

        with open(output_people_data_file, 'w') as outfile:
            output_str = 'export const people_data = '
            output_str += json.dumps(self.people_data, sort_keys=True, indent=4)
            output_str += ';'
            outfile.write(output_str)

        with open(output_site_data_file, 'w') as outfile:
            output_str = 'export const site_data = '
            output_str += json.dumps(self.site_data, sort_keys=True, indent=4)
            output_str += ';'
            outfile.write(output_str)


