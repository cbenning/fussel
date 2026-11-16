#!/usr/bin/env python3

import argparse
import os
import shutil
from importlib import resources

import yaml

from .generator import Config, SiteGenerator


class YamlConfig:
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = "config.yml"
        if not os.path.isfile(config_file):
            print(f"Config file not found: {config_file}")
            exit(-1)

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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="fussel", description="A static photo gallery generator")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yml",
        help="path to the config file (default: ./config.yml)",
    )
    return parser.parse_args(argv)


def web_dist_dir():
    """The prebuilt web app bundled with the package."""
    return str(resources.files("fussel").joinpath("web_dist"))


def main(argv=None):
    args = parse_args(argv)

    cfg = YamlConfig(args.config)

    generator = SiteGenerator(cfg)
    generator.generate()

    site_location = web_dist_dir()
    if not os.path.isfile(os.path.join(site_location, "index.html")):
        print(f"Error: prebuilt web app not found at {site_location}.")
        print("Run 'make build-web' to build it.")
        exit(-1)

    new_site_location = Config.instance().output_path
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
    with open(os.path.join(new_site_location, ".nojekyll"), "w"):
        pass

    print(f"site generated at: {new_site_location}")
    print(f"\n\n to preview your site, run: \n   python -m http.server --directory {new_site_location}")


if __name__ == "__main__":
    main()
