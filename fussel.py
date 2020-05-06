#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from generator import SiteGenerator


load_dotenv(verbose=True)

input_path = os.getenv("INPUT_PATH")
http_root = os.getenv("HTTP_ROOT")

output_photos_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "public", "static", "_gallery")
output_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "src", "_gallery")
external_root = os.path.join(http_root, "static", "_gallery", "albums")

# TODO check exists
input_photo_path = os.path.realpath(input_path)

generator = SiteGenerator(input_photo_path)
generator.generate_site(output_photos_path, output_data_path, external_root)

# exit(0)
#
# import os
# import shutil
# import json
# from PIL import Image, ExifTags
# from bs4 import BeautifulSoup
#
# SUPPORTED_EXTENSIONS = ('jpg', 'jpeg', 'gif', 'png')
#
# # TODO
# input_photos_dir = "./example_photos"
# # static_root = "http://localhost:3000/static"
#
# public_folder = "public"
# output_photos_dir = os.path.join(public_folder, "static", "_gallery")
# output_data_dir = os.path.join("src", "_gallery")
#
# output_photos_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), output_photos_dir)
# output_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), output_data_dir)
# # component_output_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "src", "_generated")
#
# output_albums_data_file = os.path.join(output_data_path, "albums_data.js")
# output_people_data_file = os.path.join(output_data_path, "people_data.js")
#
# albums_data = {}
# output_albums_photos_dir = os.path.join(output_photos_dir, "albums")
# output_albums_photos_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), output_albums_photos_dir)
#
# people_data = {}
# output_people_photos_dir = os.path.join(output_photos_dir, "people")
# output_people_photos_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), output_people_photos_dir)
#
# # albums_photo_output_dir = os.path.join(output_photos_path, albums_photo_dir)
# # component_output_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), static_folder, albums_photo_dir)
# # albums_data_output_file = os.path.join(component_output_dir, albums_photo_dir, "albums_data.js")
#
# # people_data = []
# # people_photo_dir = "people"
# # people_photo_output_dir = os.path.join(output_dir, people_photo_dir)
# # people_data_output_file = os.path.join(people_photo_output_dir, "people_data.js")
#
# print(output_photos_path)
# print(output_data_path)
# shutil.rmtree(output_photos_path, ignore_errors=True)
# os.mkdir(output_photos_path)
# shutil.rmtree(output_data_path, ignore_errors=True)
# os.mkdir(output_data_path)
#
# def process_photo(external_path, photo, output_dir):
#     new_original_photo = os.path.join(output_dir, "original_%s" % os.path.basename(photo))
#     print(' ----> Copying... ' + photo + ' --> ' + new_original_photo)
#     shutil.copyfile(photo, new_original_photo)
#
#     sizes = [(360, 360), (720, 720)]
#     prefixes = ['small', 'medium']
#     faces = extract_faces(new_original_photo)
#     for face in faces:
#         print(" ----> Detected face '%s'" % face)
#
#     data = {
#         'src': external_path + '/' + os.path.basename(new_original_photo),
#         'width': 4,
#         'height': 3,
#         'name': os.path.basename(os.path.basename(photo))
#     }
#
#     for i, size in enumerate(sizes):
#         new_thumbnail_photo = os.path.join(output_dir, "%s_%s" % (prefixes[i], os.path.basename(photo)))
#         print(' ----> Generating thumbnail... ' + new_original_photo + ' --> ' + new_thumbnail_photo)
#         im = Image.open(new_original_photo)
#         im.thumbnail(size)
#         im.save(new_thumbnail_photo)
#         data['src_%s' % prefixes[i]] = external_path + '/' + os.path.basename(new_thumbnail_photo)
#
#     return (faces, data)
#
# def extract_faces(photo_path):
#     faces = {}
#
#     with Image.open(photo_path) as im:
#         for segment, content in im.applist:
#             marker, body = content.split(bytes('\x00', 'utf-8'), 1)
#             if segment == 'APP1' and marker.decode("utf-8") == 'http://ns.adobe.com/xap/1.0/':
#                 body_str = body.decode("utf-8")
#                 soup = BeautifulSoup(body_str, 'html.parser')
#
#                 for regions in soup.find_all("mwg-rs:regions"):
#                     for regionlist in regions.find_all("mwg-rs:regionlist"):
#                         for description in regionlist.find_all("rdf:description"):
#                             if description['mwg-rs:type'] == 'Face':
#                                 faces[description['mwg-rs:name']] = ''
#     return faces.keys()
#
#
# def pick_album_thumbnail(album_photos):
#     if(len(album_photos) > 0):
#         return album_photos[0]['src_small']
#     return ''
#
# def add_photo_to_person(person, photo):
#     if not person in people_data.keys():
#         people_data[person] = {
#             'name': person,
#             'photos': []
#         }
#     people_data[person]['photos'].append(photo)
#
# for subdir, input_album_dirs, files in os.walk(input_photos_dir):
#     for input_album_dir in input_album_dirs:
#         album_dir = os.path.join(subdir, input_album_dir)
#         album_name = os.path.basename(input_album_dir)
#         if not album_name.startswith(".") and os.path.isdir(album_dir):
#             print(" > Importing album %s as '%s'" % (album_dir, album_name))
#
#             album_photos = []
#             album_data = {
#                 'name': album_name,
#                 'photos': album_photos
#             }
#
#             album_folder = os.path.join(output_albums_photos_path, album_name)
#             external_path = output_albums_photos_dir[len(public_folder):] + '/' + album_name
#             os.makedirs(album_folder)
#
#             for _, _, album_files in os.walk(album_dir):
#                 for album_file in album_files:
#                     photo_file = os.path.join(album_dir, album_file)
#                     print(" --> Processing %s... " % photo_file)
#                     faces, photo_data = process_photo(external_path, photo_file, album_folder)
#
#                     for person in faces:
#                         add_photo_to_person(person, photo_data)
#                     album_photos.append(photo_data)
#
#             album_data['src'] = pick_album_thumbnail(album_data['photos'])
#             albums_data[album_data['name']] = album_data
#
# for person_name in people_data.keys():
#     people_data[person_name]['src'] = pick_album_thumbnail(people_data[person_name]['photos'])
#
# with open(output_albums_data_file, 'w') as outfile:
#     output_str = 'export const albums_data = '
#     output_str += json.dumps(albums_data, sort_keys=True, indent=4)
#     output_str += ';'
#     outfile.write(output_str)
#
# with open(output_people_data_file, 'w') as outfile:
#     output_str = 'export const people_data = '
#     output_str += json.dumps(people_data, sort_keys=True, indent=4)
#     output_str += ';'
#     outfile.write(output_str)
