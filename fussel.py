#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from generator import SiteGenerator
import massedit

load_dotenv(verbose=True)

input_path = os.getenv("INPUT_PATH")
http_root = os.getenv("HTTP_ROOT")

filenames = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "package.json")]
massedit.edit_files(filenames, ["re.sub(r'^.*\"homepage\":.*$', '  \"homepage\": \""+http_root+"\",', line)"], dry_run=False)

output_photos_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "public", "static", "_gallery")
output_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "src", "_gallery")
external_root = os.path.join(http_root, "static", "_gallery", "albums")

# TODO check exists
input_photo_path = os.path.realpath(input_path)

generator = SiteGenerator(input_photo_path)
#generator.generate_site(output_photos_path, output_data_path, external_root)
generator.generate_site(output_photos_path, output_data_path, http_root)
