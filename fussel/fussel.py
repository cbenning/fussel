#!/usr/bin/env python3

import os
from generator import SiteGenerator
# import massedit
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

def main():
    cfg = Config()
    generator = SiteGenerator(cfg)
    generator.generate()

    # Is this still needed?
    # http_root = cfg.getKey('site.http_root', '/')
    # filenames = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "package.json")]
    # massedit.edit_files(filenames, ["re.sub(r'^.*\"homepage\":.*$', '  \"homepage\": \""+http_root+"\",', line)"], dry_run=False)

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

