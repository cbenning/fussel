#!/usr/bin/env python3

import os
import pathlib
import shutil

import yaml

from .generator import SiteGenerator


class YamlConfig:
    def __init__(self, config_file=None):
        if config_file is None:
            # When running as a module, find config.yml relative to project root
            project_root = pathlib.Path(__file__).parent.parent
            config_file = str(project_root / "config.yml")

        self.cfg = {}
        with open(config_file, "r") as stream:
            self.cfg = yaml.safe_load(stream)

        input_path = self.getKey("gallery.input_path")
        if not os.path.isdir(input_path):
            print(f"Invalid input path: {input_path}")
            exit(-1)

        output_path = self.getKey("gallery.output_path")
        if os.path.exists(output_path) and not os.path.isdir(output_path):
            print(f"Invalid output path: {output_path}")
            exit(-1)

    def __getstate__(self):
        # Make YamlConfig pickleable
        return {"cfg": self.cfg}

    def __setstate__(self, state):
        # Restore YamlConfig from pickled state
        self.cfg = state["cfg"]

    def getKey(self, path: str, default=None):
        if path in self.cfg:
            return self.cfg.get(path)
        keys = path.split(".")
        cursor = self.cfg
        for i, k in enumerate(keys):
            if i >= len(keys) - 1:
                break
            cursor = cursor.get(k, {})
        return cursor.get(k, default)


def main():

    cfg = YamlConfig()

    generator = SiteGenerator(cfg)
    generator.generate()

    http_root = cfg.getKey("site.http_root", "/")
    web_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web")

    original_cwd = os.getcwd()
    os.chdir(web_dir)
    if not shutil.which("yarn"):
        print("Error: yarn is required but not found. Please install yarn first.")
        print("Visit https://yarnpkg.com/getting-started/install for installation instructions.")
        exit(-1)
    os.environ["VITE_BASE_URL"] = http_root
    if os.system("yarn build") != 0:
        print("Failed")
        exit(-1)
    os.chdir(original_cwd)

    site_location = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "web", "build"))

    output_path = cfg.getKey("gallery.output_path", "site/")
    if os.path.isabs(output_path):
        new_site_location = os.path.normpath(output_path)
    else:
        new_site_location = os.path.normpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", output_path)
        )
    print("Copying site to output location...")
    print(f"  {site_location}  --->  {new_site_location}")
    shutil.copytree(
        site_location,
        new_site_location,
        symlinks=False,
        ignore=None,
        ignore_dangling_symlinks=False,
        dirs_exist_ok=True,
    )

    # Prevent GitHub Pages Jekyll processing from ignoring _gallery
    with open(os.path.join(new_site_location, ".nojekyll"), "w") as f:
        pass

    print(f"site generated at: {new_site_location}")
    print("\n\n to preview your site, run: \n   make serve")
    print(f"\n   or manually: \n   python -m http.server --directory {new_site_location}")


if __name__ == "__main__":
    main()
