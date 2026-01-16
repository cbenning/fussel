#!/usr/bin/env python3

import os
import shutil
import json
from urllib.parse import quote
from PIL import Image, ImageOps, ImageFile, UnidentifiedImageError
from bs4 import BeautifulSoup
from dataclasses import dataclass
from .config import *
from .util import *
from threading import RLock
from multiprocessing import Pool, Queue
from rich import print

ImageFile.LOAD_TRUNCATED_IMAGES = True


class SimpleEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "json_dump_obj"):
            return obj.json_dump_obj()
        return obj.__dict__


class Site:

    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.__init()
        return cls._instance

    def __init(self):
        self.site_name = Config.instance().site_name
        self.people_enabled = Config.instance().people_enabled


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

    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.__init()
        return cls._instance

    def __init(self):
        self.people: dict = {}
        self.people_lock = RLock()
        self.slugs = set()
        self.slugs_lock = RLock()

    def json_dump_obj(self):
        r = {}
        for v in self.people.values():
            r[v.slug] = v
        return r

    def detect_faces(self, photo, original_src, largest_src, output_path, external_path):

        print(f'Searching in [magenta]{original_src}[/magenta]...')
        faces = self.extract_faces(original_src)

        for face in faces:
            print(f' ------> Found: [cyan]{face.name}[/cyan]')

            if face.name not in self.people.keys():

                unique_person_slug = find_unique_slug(
                    self.slugs, self.slugs_lock, face.name)

                self.people[face.name] = Person(face.name, unique_person_slug)

            person = self.people[face.name]
            person.photos.append(photo)

            if not person.has_thumbnail():
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

        return faces

    def extract_faces(self, photo_path):
        """Extract face tags from image XMP metadata (MWG format).
        Handles variations in namespace prefixes and XML structure."""
        faces = []
        seen_faces = set()  # Track (name, x, y) to avoid duplicates
        
        with Image.open(photo_path) as im:
            if not hasattr(im, 'applist'):
                return faces
                
            for segment, content in im.applist:
                try:
                    # XMP format: \x00http://ns.adobe.com/xap/1.0/\x00<body>
                    # Split by first null to get marker, then split body by second null
                    parts = content.split(bytes('\x00', 'utf-8'), 2)
                    if len(parts) < 3:
                        continue
                    marker = parts[1].decode("utf-8") if len(parts) > 1 else ""
                    body_bytes = parts[2] if len(parts) > 2 else b""
                    
                    if segment != 'APP1' or marker != 'http://ns.adobe.com/xap/1.0/':
                        continue
                        
                    body_str = body_bytes.decode("utf-8")
                    # Use 'xml' parser for better namespace handling
                    try:
                        soup = BeautifulSoup(body_str, 'xml')
                    except:
                        # Fallback to html.parser if xml parser not available
                        import warnings
                        from bs4 import XMLParsedAsHTMLWarning
                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
                            soup = BeautifulSoup(body_str, 'html.parser')
                    
                    # Find all description elements (try both with and without namespace)
                    descriptions = soup.find_all("rdf:description")
                    if not descriptions:
                        descriptions = soup.find_all("description")
                    
                    # Process each description element
                    for desc in descriptions:
                        # Get type and name (try both namespace formats)
                        desc_type = desc.get('mwg-rs:type') or desc.get('type')
                        name = (desc.get('mwg-rs:name') or desc.get('name') or '').strip()
                        
                        # Find areas (try both namespace formats and recursive search)
                        areas = desc.find_all("mwg-rs:area", recursive=False)
                        if not areas:
                            areas = desc.find_all("area", recursive=False)
                        if not areas:
                            areas = desc.find_all("mwg-rs:area")
                            if not areas:
                                areas = desc.find_all("area")
                        
                        # Process if it's a Face type OR if it has a name and areas (some formats don't set type)
                        if (desc_type == 'Face' or (name and areas)):
                            for area in areas:
                                # Get area attributes (try both namespace formats)
                                w = area.get('starea:w') or area.get('w') or ''
                                h = area.get('starea:h') or area.get('h') or ''
                                x = area.get('starea:x') or area.get('x') or ''
                                y = area.get('starea:y') or area.get('y') or ''
                                
                                # Only add if we have valid coordinates and haven't seen this face before
                                if w and h and x and y:
                                    face_key = (name, x, y)
                                    if face_key not in seen_faces:
                                        seen_faces.add(face_key)
                                        faces.append(Face(
                                            name=name,
                                            geometry=FaceGeometry(w=w, h=h, x=x, y=y)
                                        ))
                                        
                except (ValueError, UnicodeDecodeError):
                    # Skip segments that don't match expected format
                    continue
                    
        return faces


class Person:

    def __init__(self, name, slug):

        self.name = name
        self.slug = slug
        self.src = None
        self.photos: list = []

    def has_thumbnail(self):
        return self.src is not None


class Photo:

    def __init__(self, name, width, height, src, thumb, slug, srcSet):

        self.width = width
        self.height = height
        self.name = name
        self.src = src
        self.thumb = thumb
        self.srcSet = srcSet
        self.faces: list = []
        self.slug = slug

    @classmethod
    def process_photo(cls, external_path, photo, filename, slug, output_path, people_q: Queue):
        new_original_photo = os.path.join(
            output_path, "original_%s%s" % (os.path.basename(slug), extract_extension(photo)))

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
        if Config.instance().overwrite or not os.path.exists(new_original_photo):
            print(f' ----> Copying to [magenta]{new_original_photo}[/magenta]')
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
        largest_src = None
        smallest_src = None

        srcSet = {}

        msg = " ------> Generating photo sizes: "
        for i, size in enumerate(sizes):
            new_size = calculate_new_size(original_size, size)
            new_sub_photo = os.path.join(output_path, "%sx%s_%s%s" % (
                new_size[0], new_size[1], os.path.basename(slug), extract_extension(photo)))
            largest_src = new_sub_photo
            if smallest_src is None:
                smallest_src = new_sub_photo

            # Only generate if overwrite explicitly asked for or if doesn't exist
            msg += f'[cyan]{new_size[0]}x{new_size[1]}[/cyan] '
            if Config.instance().overwrite or not os.path.exists(new_sub_photo):
                with Image.open(new_original_photo) as im:
                    im.thumbnail(new_size)
                    if Config.instance().exif_transpose:
                        im = ImageOps.exif_transpose(im)
                    im.save(new_sub_photo)
            srcSet[str(size)+"w"] = ["%s/%s" % (quote(external_path),
                                                quote(os.path.basename(new_sub_photo)))]

        print(msg)

        # Only copy if overwrite explicitly asked for or if doesn't exist
        if Config.instance().watermark_enabled and (Config.instance().overwrite or not os.path.exists(new_original_photo)):
            with Image.open(Config.instance().watermark_path) as watermark_im:
                print(" ------> Adding watermark")
                apply_watermark(largest_src, watermark_im,
                                Config.instance().watermark_ratio)

        photo_obj = Photo(
            filename,
            width,
            height,
            "%s/%s" % (quote(external_path),
                       quote(os.path.basename(largest_src))),
            "%s/%s" % (quote(external_path),
                       quote(os.path.basename(smallest_src))),
            slug,
            srcSet
        )

        # Faces
        if Config.instance().people_enabled:
            # Use original photo file for face detection to preserve all metadata
            people_q.put((photo_obj, photo,  # Use original photo instead of new_original_photo
                         largest_src, output_path, external_path))

        return photo_obj


def _process_photo(t):
    (external_path, photo_file, filename, unique_slug, album_folder) = t
    print(f' --> Processing [magenta]{photo_file}[/magenta]...')
    try:
        return (photo_file, Photo.process_photo(external_path, photo_file, filename, unique_slug, album_folder, _process_photo.people_q))
    except PhotoProcessingFailure as e:
        print(
            f'[yellow]Skipping processing of image file[/yellow] [magenta]{photo_file}[/magenta] Reason: [red]{str(e)}[/red]')
        return (photo_file, None)


def _proces_photo_init(people_q, yaml_config):
    _process_photo.people_q = people_q
    # Re-initialize Config in worker process
    Config.init(yaml_config)


class Albums:

    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.__init()
        return cls._instance

    def __init(self):
        self.albums: dict = {}
        self.slugs = set()
        self.slugs_lock = RLock()

    def json_dump_obj(self):
        return self.albums

    def add_album(self, album):
        self.albums[album.slug] = album

    def __getitem__(self, item):
        return list(self.albums.values())[item]

    def process_path(self, root_path, output_albums_photos_path, external_root, yaml_config):

        entries = list(map(lambda e: os.path.join(
            root_path, e), os.listdir(root_path)))
        paths = list(filter(lambda e: is_supported_album(e), entries))

        for album_path in paths:
            album_name = os.path.basename(album_path)
            if not album_name.startswith('.'):  # skip dotfiles
                self.process_album_path(
                    album_path, album_name, output_albums_photos_path, external_root, yaml_config)

    def process_album_path(self, album_dir, album_name, output_albums_photos_path, external_root, yaml_config):

        unique_album_slug = find_unique_slug(
            self.slugs, self.slugs_lock, album_name)
        print(
            f'Importing [magenta]{album_dir}[/magenta] as [green]{album_name}[/green] ([yellow]{unique_album_slug}[/yellow])')

        album_obj = Album(album_name, unique_album_slug)

        album_name_folder = os.path.basename(unique_album_slug)
        album_folder = os.path.join(
            output_albums_photos_path, album_name_folder)
        # TODO externalize this?
        external_path = os.path.join(external_root, album_name_folder)
        os.makedirs(album_folder, exist_ok=True)

        entries = list(map(lambda e: os.path.join(
            album_dir, e), sorted(os.listdir(album_dir))))
        dirs = list(filter(lambda e: is_supported_album(e), entries))
        files = list(filter(lambda e: is_supported_photo(e), entries))

        unique_slugs_lock = RLock()
        unique_slugs = set()

        jobs = []

        for album_file in files:
            if os.path.basename(album_file).startswith('.'):  # skip dotfiles
                continue
            photo_file = album_file  # album_file is already the full path from entries
            filename = os.path.basename(photo_file)

            # Get a unique slug
            unique_slug = find_unique_slug(
                unique_slugs, unique_slugs_lock, filename)

            jobs.append((external_path, photo_file,
                        filename, unique_slug, album_folder))

        print(f'Found [cyan]{len(jobs)}[/cyan] photos to process')
        results = []
        people_q = Queue()
        if len(jobs) > 0:
            with Pool(processes=Config.instance().parallel_tasks, initializer=_proces_photo_init, initargs=[people_q, yaml_config]) as P:
                results = P.map(_process_photo, jobs)
        else:
            print('[yellow]No photos found in this album[/yellow]')

        people = People.instance()
        print(f'Detecting Faces...')
        while not people_q.empty():
            (photo_obj, new_original_photo, largest_src,
             output_path, external_path) = people_q.get()
            people.detect_faces(photo_obj, new_original_photo,
                                largest_src, output_path, external_path)

        for photo_file, result in results:
            if result is not None:
                album_obj.add_photo(result)

        if len(album_obj.photos) > 0:
            album_obj.src = pick_album_thumbnail(
                album_obj.photos)  # TODO internalize
            self.add_album(album_obj)

        # Recursively process sub-dirs
        if Config.instance().recursive_albums:
            for sub_album_dir in dirs:
                if os.path.basename(sub_album_dir).startswith('.'):  # skip dotfiles
                    continue
                sub_album_name = "%s" % Config.instance().recursive_albums_name_pattern
                sub_album_name = sub_album_name.replace(
                    "{parent_album}", unique_album_slug)
                sub_album_name = sub_album_name.replace(
                    "{album}", os.path.basename(sub_album_dir))
                self.process_album_path(
                    sub_album_dir, sub_album_name, output_albums_photos_path, external_root, yaml_config)


class Album:

    def __init__(self, name, slug):
        self.name = name
        self.slug = slug
        self.photos: list = []
        self.src: str = None

    def add_photo(self, photo):
        self.photos.append(photo)


class SiteGenerator:

    def __init__(self, yaml_config):

        Config.init(yaml_config)

        self.yaml_config = yaml_config
        self.unique_person_slugs = {}

    def generate(self):

        print(
            f'[bold]Generating site from [magenta]{Config.instance().input_photos_dir}[magenta][/bold]')
        output_photos_path = os.path.normpath(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "..", "web", "public", "static", "_gallery"))
        output_data_path = os.path.normpath(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "..", "web", "src", "_gallery"))
        external_root = os.path.normpath(os.path.join(
            Config.instance().http_root, "static", "_gallery", "albums"))
        generated_site_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "web", "build"))

        # Paths
        output_albums_data_file = os.path.join(
            output_data_path, "albums_data.js")
        output_people_data_file = os.path.join(
            output_data_path, "people_data.js")
        output_site_data_file = os.path.join(output_data_path, "site_data.js")
        output_albums_photos_path = os.path.join(output_photos_path, "albums")

        # Cleanup and prep of deploy space
        if Config.instance().overwrite:
            shutil.rmtree(output_photos_path, ignore_errors=True)
            shutil.rmtree(generated_site_path, ignore_errors=True)

        os.makedirs(output_photos_path, exist_ok=True)
        shutil.rmtree(output_data_path, ignore_errors=True)
        os.makedirs(output_data_path, exist_ok=True)

        Albums.instance().process_path(Config.instance().input_photos_dir,
                                       output_albums_photos_path, external_root, self.yaml_config)

        with open(output_albums_data_file, 'w') as outfile:
            output_str = 'export const albums_data = '
            output_str += json.dumps(Albums.instance(),
                                     sort_keys=True, indent=3, cls=SimpleEncoder)
            output_str += ';'
            outfile.write(output_str)

        with open(output_people_data_file, 'w') as outfile:
            output_str = 'export const people_data = '
            output_str += json.dumps(People.instance(),
                                     sort_keys=True, indent=3, cls=SimpleEncoder)
            output_str += ';'
            outfile.write(output_str)

        with open(output_site_data_file, 'w') as outfile:
            output_str = 'export const site_data = '
            output_str += json.dumps(Site.instance(),
                                     sort_keys=True, indent=3, cls=SimpleEncoder)
            output_str += ';'
            outfile.write(output_str)


class PhotoProcessingFailure(Exception):
    def __init__(self, message="Failed to process photo"):
        self.message = message
        super().__init__(self.message)
