#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from generator import SiteGenerator
import massedit
import yaml
import shutil


class Config:
    def __init__(self, config_file='../config.yml'):

        self.cfg = {}
        with open(config_file,'r') as stream:
            self.cfg = yaml.safe_load(stream)


        input_path = self.getKey('gallery.input_path')
        if not os.path.isdir(input_path):
            print(f'Invalid input path: {input_path}')
            exit(-1)
        
        output_path = self.getKey('gallery.output_path')
        if os.path.exists(output_path) and not os.path.isdir(output_path):
            print(f'Invalid output path: {output_path}')
            exit(-1)
        

    def getKey(self, path: str, default=None):
        keys = path.split(".")
        cursor = self.cfg
        for i, k in enumerate(keys):
            if i >= len(keys) -1 :
                break
            cursor = cursor.get(k, {})
        return cursor.get(k, default)




# load_dotenv(verbose=True)

# input_path = os.getenv("INPUT_PATH")
# if input_path is None or len(input_path) < 1:
#     print("Please provide INPUT_PATH in your .env file")
#     exit(1)

# http_root = os.getenv("HTTP_ROOT")

# people_enabled = os.getenv("PEOPLE_ENABLE")
# if people_enabled == 'true':
#     people_enabled = True
# else:
#     people_enabled = False

# watermark_enabled = os.getenv("WATERMARK_ENABLE")
# if watermark_enabled == 'true':
#     watermark_enabled = True
# else:
#     watermark_enabled = False

# watermark_path = os.getenv("WATERMARK_PATH")

# watermark_ratio = float(os.getenv("WATERMARK_RATIO"))
# if watermark_ratio <= 0.0:
#     watermark_ratio = 0.0
# elif watermark_ratio >= 1.0:
#     watermark_ratio = 1.0

# site_name = os.getenv("SITE_NAME")

# recursive_albums = os.getenv("RECURSIVE_ALBUMS")
# if recursive_albums == 'true':
#     recursive_albums = True
# else:
#     recursive_albums = False

# recursive_albums_name_pattern = os.getenv("RECURSIVE_ALBUMS_NAME_PATTERN")

# overwrite = os.getenv("OVERWRITE")
# if overwrite == 'true':
#     overwrite = True
# else:
#     overwrite = False

# output_photos_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "public", "static", "_gallery")
# output_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "src", "_gallery")
# external_root = os.path.join(http_root, "static", "_gallery", "albums")

# # TODO check exists
# input_photo_path = os.path.realpath(input_path)


def main():
    cfg = Config()


    generator = SiteGenerator(
        cfg
        # site_name,
        # input_photo_path,
        # people_enabled,
        # watermark_enabled,
        # watermark_path,
        # watermark_ratio,
        # recursive_albums,
        # recursive_albums_name_pattern,
        # overwrite
    )
    # generator.generate(output_photos_path, output_data_path, http_root)
    generator.generate()

    # Rebuild node site
    # pushd web
    # yarn build
    # popd

    # printf "Site generated at: ${CURRENT_PATH}/fussel/web/build"
    # printf "\n\n To validate build run: \n   /usr/bin/env python3 -m http.server --directory fussel/web/build\n\n"

    http_root = cfg.getKey('site.http_root', '/')
    filenames = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "package.json")]
    massedit.edit_files(filenames, ["re.sub(r'^.*\"homepage\":.*$', '  \"homepage\": \""+http_root+"\",', line)"], dry_run=False)


    os.chdir('web')
    if os.system('yarn build') != 0:
        print("Failed")
    os.chdir('..')

    site_location = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "build"))

    output_path = cfg.getKey('gallery.output_path', 'site/')
    if os.path.isabs(output_path):
        new_site_location = os.path.normpath(output_path)
    else:
        new_site_location = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", output_path))
    print("Copying site to output location...")
    print(f'  {site_location}  --->  {new_site_location}')
    shutil.copytree(
        site_location,
        new_site_location,
        symlinks=False, 
        ignore=None, 
        ignore_dangling_symlinks=False, 
        dirs_exist_ok=True)

    print(f'site generated at: {new_site_location}/fussel/web/build')
    print(f'\n\n to validate build run: \n   python -m http.server --directory {new_site_location}')

if __name__ == "__main__":
    main()

