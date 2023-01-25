#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from generator import SiteGenerator
import massedit

load_dotenv(verbose=True)

input_path = os.getenv("INPUT_PATH")
if input_path is None or len(input_path) < 1:
    print("Please provide INPUT_PATH in your .env file")
    exit(1)

http_root = os.getenv("HTTP_ROOT")

people_enabled = os.getenv("PEOPLE_ENABLE")
if people_enabled == 'true':
    people_enabled = True
else:
    people_enabled = False

watermark_enabled = os.getenv("WATERMARK_ENABLE")
if watermark_enabled == 'true':
    watermark_enabled = True
else:
    watermark_enabled = False

watermark_path = os.getenv("WATERMARK_PATH")

watermark_ratio = float(os.getenv("WATERMARK_RATIO"))
if watermark_ratio <= 0.0:
    watermark_ratio = 0.0
elif watermark_ratio >= 1.0:
    watermark_ratio = 1.0

site_name = os.getenv("SITE_NAME")

recursive_albums = os.getenv("RECURSIVE_ALBUMS")
if recursive_albums == 'true':
    recursive_albums = True
else:
    recursive_albums = False

recursive_albums_name_pattern = os.getenv("RECURSIVE_ALBUMS_NAME_PATTERN")

overwrite = os.getenv("OVERWRITE")
if overwrite == 'true':
    overwrite = True
else:
    overwrite = False

filenames = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "package.json")]
massedit.edit_files(filenames, ["re.sub(r'^.*\"homepage\":.*$', '  \"homepage\": \""+http_root+"\",', line)"], dry_run=False)

output_photos_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "public", "static", "_gallery")
output_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "src", "_gallery")
external_root = os.path.join(http_root, "static", "_gallery", "albums")

# TODO check exists
input_photo_path = os.path.realpath(input_path)

generator = SiteGenerator(
    site_name,
    input_photo_path,
    people_enabled,
    watermark_enabled,
    watermark_path,
    watermark_ratio,
    recursive_albums,
    recursive_albums_name_pattern,
    overwrite
)
generator.generate_site(output_photos_path, output_data_path, http_root)
