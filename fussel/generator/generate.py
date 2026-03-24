#!/usr/bin/env python3

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from multiprocessing import Pool, Queue
from threading import RLock
from urllib.parse import quote

from bs4 import BeautifulSoup
from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError
from PIL.ExifTags import TAGS
from rich import print

from .config import Config
from .util import (
    apply_watermark,
    calculate_face_crop_dimensions,
    calculate_new_size,
    extract_extension,
    find_unique_slug,
    is_supported_album,
    is_supported_photo,
    pick_album_thumbnail,
)

ImageFile.LOAD_TRUNCATED_IMAGES = True


class SimpleEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "json_dump_obj"):
            return obj.json_dump_obj()
        return obj.__dict__


class Site:
    _instance = None

    def __init__(self):
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.__init()
        return cls._instance

    def __init(self):
        self.site_name = Config.instance().site_name
        self.people_enabled = Config.instance().people_enabled
        self.albums_enabled = Config.instance().albums_enabled
        self.photos_enabled = Config.instance().photos_enabled
        self.allow_download = Config.instance().allow_download


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
        raise RuntimeError("Call instance() instead")

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

        print(f"Searching in [magenta]{original_src}[/magenta]...")
        faces = self.extract_faces(original_src)

        # Store face data on the photo object
        photo.faces = []
        for face in faces:
            print(f" ------> Found: [cyan]{face.name}[/cyan]")

            if face.name not in self.people.keys():
                unique_person_slug = find_unique_slug(self.slugs, self.slugs_lock, face.name)

                self.people[face.name] = Person(face.name, unique_person_slug)

            person = self.people[face.name]
            person.photos.append(photo)

            # Store face data (name + slug + geometry) on photo
            photo.faces.append(
                {
                    "name": face.name,
                    "slug": person.slug,
                    "geometry": {
                        "x": float(face.geometry.x),
                        "y": float(face.geometry.y),
                        "w": float(face.geometry.w),
                        "h": float(face.geometry.h),
                    },
                }
            )

            if not person.has_thumbnail():
                with Image.open(largest_src) as im:
                    face_size = face.geometry.w, face.geometry.h
                    face_position = face.geometry.x, face.geometry.y
                    new_face_photo = os.path.join(output_path, "%s_%s" % (person.slug, os.path.basename(original_src)))
                    box = calculate_face_crop_dimensions(im.size, face_size, face_position)
                    im_cropped = im.crop(box)
                    im_cropped.save(new_face_photo)
                    person.src = "%s/%s" % (external_path, os.path.basename(new_face_photo))

        return faces

    def extract_faces(self, photo_path):
        """Extract face tags from image XMP metadata (MWG format).
        Handles variations in namespace prefixes and XML structure."""
        faces = []
        seen_faces = set()  # Track (name, x, y) to avoid duplicates

        with Image.open(photo_path) as im:
            if not hasattr(im, "applist"):
                return faces

            for segment, content in im.applist:
                try:
                    # XMP format can be either:
                    # 1. \x00http://ns.adobe.com/xap/1.0/\x00<body> (starts with null)
                    # 2. http://ns.adobe.com/xap/1.0/\x00<body> (doesn't start with null)
                    parts = content.split(bytes("\x00", "utf-8"), 2)

                    # Determine marker and body based on format
                    if len(parts) >= 3:
                        # Format 1: starts with null, parts[0] is empty, parts[1] is marker, parts[2] is body
                        marker = parts[1].decode("utf-8", errors="ignore") if len(parts) > 1 else ""
                        body_bytes = parts[2] if len(parts) > 2 else b""
                    elif len(parts) == 2:
                        # Format 2: doesn't start with null, parts[0] is marker, parts[1] is body
                        marker = parts[0].decode("utf-8", errors="ignore")
                        body_bytes = parts[1]
                    else:
                        continue

                    if segment != "APP1" or marker != "http://ns.adobe.com/xap/1.0/":
                        continue

                    body_str = body_bytes.decode("utf-8")
                    # Use 'xml' parser for better namespace handling
                    try:
                        soup = BeautifulSoup(body_str, "xml")
                    except Exception:
                        # Fallback to html.parser if xml parser not available
                        import warnings

                        from bs4 import XMLParsedAsHTMLWarning

                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
                            soup = BeautifulSoup(body_str, "html.parser")

                    # Find all description elements (try both with and without namespace)
                    descriptions = soup.find_all("rdf:description")
                    if not descriptions:
                        descriptions = soup.find_all("description")

                    # Process each description element
                    for desc in descriptions:
                        # Get type and name (try both namespace formats)
                        desc_type = desc.get("mwg-rs:type") or desc.get("type")
                        name = (desc.get("mwg-rs:name") or desc.get("name") or "").strip()

                        # Find areas (try both namespace formats and recursive search)
                        areas = desc.find_all("mwg-rs:area", recursive=False)
                        if not areas:
                            areas = desc.find_all("area", recursive=False)
                        if not areas:
                            areas = desc.find_all("mwg-rs:area")
                            if not areas:
                                areas = desc.find_all("area")

                        # Process if it's a Face type OR if it has a name and areas (some formats don't set type)
                        if desc_type == "Face" or (name and areas):
                            for area in areas:
                                # Get area attributes (try both namespace formats)
                                w = area.get("starea:w") or area.get("w") or ""
                                h = area.get("starea:h") or area.get("h") or ""
                                x = area.get("starea:x") or area.get("x") or ""
                                y = area.get("starea:y") or area.get("y") or ""

                                # Only add if we have valid coordinates and haven't seen this face before
                                if w and h and x and y:
                                    face_key = (name, x, y)
                                    if face_key not in seen_faces:
                                        seen_faces.add(face_key)
                                        faces.append(Face(name=name, geometry=FaceGeometry(w=w, h=h, x=x, y=y)))

                except (ValueError, UnicodeDecodeError, AttributeError, KeyError):
                    # Skip segments that don't match expected format
                    # Silently continue to next segment
                    continue
                except Exception:
                    # Log unexpected errors but continue processing
                    # This prevents one bad segment from breaking entire face detection
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
    def __init__(self, name, width, height, src, thumb, slug, srcSet, originalSrc=None, date=None):

        self.width = width
        self.height = height
        self.name = name
        self.src = src
        self.thumb = thumb
        self.srcSet = srcSet
        self.faces: list = []
        self.slug = slug
        self.originalSrc = originalSrc
        self.date = date
        self.exif = {}

    @classmethod
    def _extract_date(cls, photo):
        """Extract the capture date from a photo file.

        Tries four methods in order: getexif(), _getexif(), XMP APP1 segment,
        and finally the file modification time.  Returns an ISO-format date
        string, or None if nothing could be found.
        """
        date_str = None

        # Method 1: Try getexif() (PIL 8.0+)
        try:
            with Image.open(photo) as im:
                if hasattr(im, "getexif"):
                    exif = im.getexif()
                    if exif is not None and len(exif) > 0:
                        # 36867 = DateTimeOriginal, 36868 = DateTimeDigitized, 306 = DateTime
                        for tag_id in [36867, 36868, 306]:
                            if tag_id in exif:
                                value = exif[tag_id]
                                if value and isinstance(value, str):
                                    try:
                                        date_str = datetime.strptime(value, "%Y:%m:%d %H:%M:%S").isoformat()
                                        break
                                    except (ValueError, TypeError):
                                        pass

                        if not date_str:
                            for tag_id, value in exif.items():
                                if not value or not isinstance(value, str):
                                    continue
                                tag_name = TAGS.get(tag_id, "")
                                if tag_name in ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]:
                                    try:
                                        date_str = datetime.strptime(value, "%Y:%m:%d %H:%M:%S").isoformat()
                                        break
                                    except (ValueError, TypeError):
                                        pass
        except Exception:
            pass

        # Method 2: Fallback to _getexif()
        if not date_str:
            try:
                with Image.open(photo) as im:
                    if hasattr(im, "_getexif"):
                        exif_old = im._getexif()
                        if exif_old is not None:
                            for tag_id in [36867, 36868, 306]:
                                if tag_id in exif_old:
                                    value = exif_old[tag_id]
                                    if value and isinstance(value, str):
                                        try:
                                            date_str = datetime.strptime(value, "%Y:%m:%d %H:%M:%S").isoformat()
                                            break
                                        except (ValueError, TypeError):
                                            pass
            except Exception:
                pass

        # Method 3: Try XMP metadata
        if not date_str:
            try:
                with Image.open(photo) as im:
                    if hasattr(im, "applist"):
                        for segment, content in im.applist:
                            try:
                                # XMP can be: \x00<marker>\x00<body>  or  <marker>\x00<body>
                                parts = content.split(bytes("\x00", "utf-8"), 2)
                                if len(parts) >= 3:
                                    marker = parts[1].decode("utf-8", errors="ignore")
                                    body_bytes = parts[2]
                                elif len(parts) == 2:
                                    marker = parts[0].decode("utf-8", errors="ignore")
                                    body_bytes = parts[1]
                                else:
                                    continue

                                if segment != "APP1" or marker != "http://ns.adobe.com/xap/1.0/":
                                    continue

                                body_str = body_bytes.decode("utf-8")

                                try:
                                    soup = BeautifulSoup(body_str, "xml")
                                except Exception:
                                    import warnings

                                    from bs4 import XMLParsedAsHTMLWarning

                                    with warnings.catch_warnings():
                                        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
                                        soup = BeautifulSoup(body_str, "html.parser")

                                descriptions = soup.find_all("rdf:description")
                                if not descriptions:
                                    descriptions = soup.find_all("description")

                                date_fields = [
                                    "photoshop:DateCreated",
                                    "DateCreated",
                                    "xmp:CreateDate",
                                    "CreateDate",
                                    "exif:DateTimeOriginal",
                                    "DateTimeOriginal",
                                    "xmp:ModifyDate",
                                    "ModifyDate",
                                    "xmp:MetadataDate",
                                    "MetadataDate",
                                    "dc:date",
                                    "date",
                                ]

                                for desc in descriptions:
                                    for field in date_fields:
                                        date_value = (
                                            desc.get(field)
                                            or desc.get(field.split(":")[-1] if ":" in field else field)
                                            or None
                                        )
                                        if date_value:
                                            date_value_str = str(date_value).strip()
                                            if date_value_str.endswith("Z"):
                                                date_value_str = date_value_str[:-1] + "+00:00"
                                            try:
                                                date_str = datetime.fromisoformat(
                                                    date_value_str.replace("Z", "+00:00")
                                                ).isoformat()
                                                break
                                            except (ValueError, TypeError):
                                                try:
                                                    date_str = datetime.strptime(
                                                        date_value_str, "%Y:%m:%d %H:%M:%S"
                                                    ).isoformat()
                                                    break
                                                except (ValueError, TypeError):
                                                    for fmt in [
                                                        "%Y-%m-%d %H:%M:%S",
                                                        "%Y-%m-%dT%H:%M:%S",
                                                        "%Y/%m/%d %H:%M:%S",
                                                    ]:
                                                        try:
                                                            date_str = datetime.strptime(
                                                                date_value_str, fmt
                                                            ).isoformat()
                                                            break
                                                        except (ValueError, TypeError):
                                                            continue
                                        if date_str:
                                            break
                                    if date_str:
                                        break
                                if date_str:
                                    break
                            except (ValueError, UnicodeDecodeError, AttributeError, KeyError):
                                continue
                            except Exception:
                                continue
            except Exception:
                pass

        # Method 4: Fallback to file modification time
        if not date_str:
            try:
                mtime = os.path.getmtime(photo)
                date_str = datetime.fromtimestamp(mtime).isoformat()
            except Exception:
                pass

        return date_str

    @classmethod
    def _extract_exif(cls, photo):
        """Extract camera and shot metadata from a photo's EXIF data."""
        result = {}

        exposure_programs = {
            0: "Not defined",
            1: "Manual",
            2: "Normal",
            3: "Aperture priority",
            4: "Shutter priority",
            5: "Creative",
            6: "Action",
            7: "Portrait",
            8: "Landscape",
        }
        metering_modes = {
            0: "Unknown",
            1: "Average",
            2: "Center-weighted",
            3: "Spot",
            4: "Multi-spot",
            5: "Multi-segment",
            6: "Partial",
        }
        flash_values = {
            0x00: "No flash",
            0x01: "Flash fired",
            0x05: "Flash fired, no return",
            0x07: "Flash fired, return",
            0x09: "Flash on, compulsory",
            0x10: "Flash off",
            0x18: "Flash off, auto",
            0x19: "Flash auto",
            0x1D: "Flash auto, no return",
            0x1F: "Flash auto, return",
            0x20: "No flash function",
            0x41: "Flash fired, red-eye",
            0x45: "Flash fired, red-eye, no return",
            0x47: "Flash fired, red-eye, return",
        }

        try:
            with Image.open(photo) as im:
                if not hasattr(im, "getexif"):
                    return result
                exif = im.getexif()
                if not exif:
                    return result

                # Camera
                camera = {}
                for tag_id, field in [(271, "make"), (272, "model"), (42036, "lens"), (305, "software")]:
                    val = exif.get(tag_id)
                    if val and isinstance(val, str) and val.strip():
                        camera[field] = val.strip()
                if camera:
                    result["camera"] = camera

                # Shot
                shot = {}

                exp = exif.get(33434)
                if exp is not None:
                    try:
                        f = float(exp)
                        if 0 < f < 1:
                            shot["exposure"] = f"1/{round(1 / f)}s"
                        elif f >= 1:
                            shot["exposure"] = f"{f:.1f}s"
                    except Exception:
                        pass

                fnumber = exif.get(33437)
                if fnumber is not None:
                    try:
                        shot["aperture"] = f"f/{float(fnumber):.1f}"
                    except Exception:
                        pass

                iso = exif.get(34855)
                if iso is not None:
                    shot["iso"] = str(iso)

                fl = exif.get(37386)
                if fl is not None:
                    try:
                        shot["focal_length"] = f"{float(fl):.0f}mm"
                    except Exception:
                        pass

                ep = exif.get(34850)
                if ep is not None:
                    shot["exposure_program"] = exposure_programs.get(ep, str(ep))

                ec = exif.get(37380)
                if ec is not None:
                    try:
                        shot["exposure_compensation"] = f"{float(ec):+.1f} EV"
                    except Exception:
                        pass

                mm = exif.get(37383)
                if mm is not None:
                    shot["metering_mode"] = metering_modes.get(mm, str(mm))

                wb = exif.get(41987)
                if wb is not None:
                    shot["white_balance"] = "Auto" if wb == 0 else "Manual"

                flash = exif.get(37385)
                if flash is not None:
                    shot["flash"] = flash_values.get(flash, f"0x{flash:02x}")

                if shot:
                    result["shot"] = shot

                # Image
                cs = exif.get(40961)
                if cs is not None:
                    if cs == 1:
                        result["image"] = {"color_space": "sRGB"}
                    elif cs == 65535:
                        result["image"] = {"color_space": "Uncalibrated"}
                    else:
                        result["image"] = {"color_space": str(cs)}

                # Rights
                rights = {}
                artist = exif.get(315)
                if artist and isinstance(artist, str) and artist.strip():
                    rights["artist"] = artist.strip()
                copyright_val = exif.get(33432)
                if copyright_val and isinstance(copyright_val, str) and copyright_val.strip():
                    rights["copyright"] = copyright_val.strip()
                if rights:
                    result["rights"] = rights

                # GPS
                try:
                    gps_ifd = exif.get_ifd(34853)
                    if gps_ifd:
                        gps = {}
                        lat_ref = gps_ifd.get(1)
                        lat = gps_ifd.get(2)
                        lon_ref = gps_ifd.get(3)
                        lon = gps_ifd.get(4)
                        alt_ref = gps_ifd.get(5)
                        alt = gps_ifd.get(6)

                        if lat and lon and lat_ref and lon_ref:

                            def _dms(dms, ref):
                                dec = float(dms[0]) + float(dms[1]) / 60 + float(dms[2]) / 3600
                                return -dec if ref in ("S", "W") else dec

                            lat_dec = _dms(lat, lat_ref)
                            lon_dec = _dms(lon, lon_ref)
                            gps["latitude"] = f"{abs(lat_dec):.6f}° {'N' if lat_dec >= 0 else 'S'}"
                            gps["longitude"] = f"{abs(lon_dec):.6f}° {'E' if lon_dec >= 0 else 'W'}"

                        if alt is not None:
                            try:
                                gps["altitude"] = f"{float(alt):.0f}m {'below' if alt_ref else 'above'} sea level"
                            except Exception:
                                pass

                        if gps:
                            result["gps"] = gps
                except Exception:
                    pass

        except Exception:
            pass

        return result

    @classmethod
    def process_photo(cls, external_path, photo, filename, slug, output_path, people_q: Queue):
        new_original_photo = os.path.join(
            output_path, "original_%s%s" % (os.path.basename(slug), extract_extension(photo))
        )

        # Extract date and EXIF metadata from ORIGINAL file (before copying/modifying)
        date_str = cls._extract_date(photo)
        exif_data = cls._extract_exif(photo)

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
        if Config.instance().overwrite or not os.path.exists(new_original_photo):
            print(f" ----> Copying to [magenta]{new_original_photo}[/magenta]")
            shutil.copyfile(photo, new_original_photo)

        try:
            with Image.open(new_original_photo) as im:
                original_size = im.size
                width, height = im.size
        except UnidentifiedImageError as e:
            if os.path.exists(new_original_photo):
                os.remove(new_original_photo)
            raise PhotoProcessingFailure(message=str(e))

        sizes = Config.instance().photo_sizes
        largest_src = None
        smallest_src = None

        srcSet = {}

        msg = " ------> Generating photo sizes: "
        for i, size in enumerate(sizes):
            new_size = calculate_new_size(original_size, size)
            new_sub_photo = os.path.join(
                output_path, "%sx%s_%s%s" % (new_size[0], new_size[1], os.path.basename(slug), extract_extension(photo))
            )
            largest_src = new_sub_photo
            if smallest_src is None:
                smallest_src = new_sub_photo

            # Only generate if overwrite explicitly asked for or if doesn't exist
            msg += f"[cyan]{new_size[0]}x{new_size[1]}[/cyan] "
            if Config.instance().overwrite or not os.path.exists(new_sub_photo):
                with Image.open(new_original_photo) as im:
                    im.thumbnail(new_size)
                    if Config.instance().exif_transpose:
                        im = ImageOps.exif_transpose(im)
                    im.save(new_sub_photo)
            srcSet[str(size) + "w"] = ["%s/%s" % (quote(external_path), quote(os.path.basename(new_sub_photo)))]

        print(msg)

        if Config.instance().watermark_enabled and (Config.instance().overwrite or not os.path.exists(largest_src)):
            with Image.open(Config.instance().watermark_path) as watermark_im:
                print(" ------> Adding watermark")
                apply_watermark(largest_src, watermark_im, Config.instance().watermark_ratio)

        # Construct original photo path for downloads
        original_filename = "original_%s%s" % (os.path.basename(slug), extract_extension(photo))
        original_src = "%s/%s" % (quote(external_path), quote(original_filename))

        photo_obj = Photo(
            filename,
            width,
            height,
            "%s/%s" % (quote(external_path), quote(os.path.basename(largest_src))),
            "%s/%s" % (quote(external_path), quote(os.path.basename(smallest_src))),
            slug,
            srcSet,
            original_src,
            date_str,
        )
        photo_obj.exif = exif_data

        # Faces
        if Config.instance().people_enabled:
            # Use original photo file for face detection to preserve all metadata
            people_q.put(
                (
                    photo_obj,
                    photo,  # Use original photo instead of new_original_photo
                    largest_src,
                    output_path,
                    external_path,
                )
            )

        return photo_obj


def _process_photo(t):
    (external_path, photo_file, filename, unique_slug, album_folder) = t
    print(f" --> Processing [magenta]{photo_file}[/magenta]...")
    try:
        return (
            photo_file,
            Photo.process_photo(
                external_path, photo_file, filename, unique_slug, album_folder, _process_photo.people_q
            ),
        )
    except PhotoProcessingFailure as e:
        print(
            f"[yellow]Skipping processing of image file[/yellow] [magenta]{photo_file}[/magenta] Reason: [red]{str(e)}[/red]"
        )
        return (photo_file, None)


def _proces_photo_init(people_q, yaml_config):
    _process_photo.people_q = people_q
    # Re-initialize Config in worker process
    Config.init(yaml_config)


class Albums:
    _instance = None

    def __init__(self):
        raise RuntimeError("Call instance() instead")

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

        entries = list(map(lambda e: os.path.join(root_path, e), os.listdir(root_path)))
        paths = list(filter(lambda e: is_supported_album(e), entries))

        for album_path in paths:
            album_name = os.path.basename(album_path)
            if not album_name.startswith("."):  # skip dotfiles
                self.process_album_path(album_path, album_name, output_albums_photos_path, external_root, yaml_config)

    def process_album_path(self, album_dir, album_name, output_albums_photos_path, external_root, yaml_config):

        unique_album_slug = find_unique_slug(self.slugs, self.slugs_lock, album_name)
        print(
            f"Importing [magenta]{album_dir}[/magenta] as [green]{album_name}[/green] ([yellow]{unique_album_slug}[/yellow])"
        )

        album_obj = Album(album_name, unique_album_slug)

        album_name_folder = os.path.basename(unique_album_slug)
        album_folder = os.path.join(output_albums_photos_path, album_name_folder)
        # TODO externalize this?
        external_path = os.path.join(external_root, album_name_folder)
        os.makedirs(album_folder, exist_ok=True)

        entries = list(map(lambda e: os.path.join(album_dir, e), sorted(os.listdir(album_dir))))
        dirs = list(filter(lambda e: is_supported_album(e), entries))
        files = list(filter(lambda e: is_supported_photo(e), entries))

        unique_slugs_lock = RLock()
        unique_slugs = set()

        jobs = []

        for album_file in files:
            if os.path.basename(album_file).startswith("."):  # skip dotfiles
                continue
            photo_file = album_file  # album_file is already the full path from entries
            filename = os.path.basename(photo_file)

            # Get a unique slug
            unique_slug = find_unique_slug(unique_slugs, unique_slugs_lock, filename)

            jobs.append((external_path, photo_file, filename, unique_slug, album_folder))

        print(f"Found [cyan]{len(jobs)}[/cyan] photos to process")
        results = []
        people_q = Queue()
        if len(jobs) > 0:
            with Pool(
                processes=Config.instance().parallel_tasks,
                initializer=_proces_photo_init,
                initargs=[people_q, yaml_config],
            ) as P:
                results = P.map(_process_photo, jobs)
        else:
            print("[yellow]No photos found in this album[/yellow]")

        people = People.instance()
        print("Detecting Faces...")
        # Create a mapping from photo slug to photo object for face detection
        photo_by_slug = {}
        for photo_file, result in results:
            if result is not None:
                photo_by_slug[result.slug] = result

        # Process face detection and update the photo objects in results
        while not people_q.empty():
            (photo_obj, new_original_photo, largest_src, output_path, external_path) = people_q.get()
            # Find the corresponding photo object in results by matching slug
            # The photo_obj from queue might be a different instance due to multiprocessing
            if photo_obj.slug in photo_by_slug:
                actual_photo = photo_by_slug[photo_obj.slug]
                people.detect_faces(actual_photo, new_original_photo, largest_src, output_path, external_path)

        for photo_file, result in results:
            if result is not None:
                album_obj.add_photo(result)

        if len(album_obj.photos) > 0:
            album_obj.src = pick_album_thumbnail(album_obj.photos)  # TODO internalize
            self.add_album(album_obj)

        # Recursively process sub-dirs
        if Config.instance().recursive_albums:
            for sub_album_dir in dirs:
                if os.path.basename(sub_album_dir).startswith("."):  # skip dotfiles
                    continue
                sub_album_name = "%s" % Config.instance().recursive_albums_name_pattern
                sub_album_name = sub_album_name.replace("{parent_album}", album_name)
                sub_album_name = sub_album_name.replace("{album}", os.path.basename(sub_album_dir))
                self.process_album_path(
                    sub_album_dir, sub_album_name, output_albums_photos_path, external_root, yaml_config
                )


class Album:
    def __init__(self, name, slug):
        self.name = name
        self.slug = slug
        self.photos: list = []
        self.src: str = None

    def add_photo(self, photo):
        self.photos.append(photo)


class Photos:
    _instance = None

    def __init__(self):
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.__init()
        return cls._instance

    def __init(self):
        self.photos: list = []

    def collect_all_photos(self):
        """Collect all photos from all albums and add albumSlug to each photo."""
        self.photos = []
        albums = Albums.instance()
        for album_slug, album in albums.albums.items():
            for photo in album.photos:
                # Add albumSlug to photo for reference
                photo.albumSlug = album_slug
                self.photos.append(photo)

    def sort_photos(self):
        """Sort photos based on configuration."""
        sort_by = Config.instance().photos_sort_by
        sort_order = Config.instance().photos_sort_order

        def sort_key(photo):
            if sort_by == "date":
                if photo.date:
                    try:
                        # Handle various date formats
                        date_str = photo.date
                        if "T" not in date_str and " " in date_str:
                            date_str = date_str.replace(" ", "T")
                        if date_str.endswith("Z"):
                            date_str = date_str.replace("Z", "+00:00")
                        return datetime.fromisoformat(date_str).timestamp()
                    except Exception:
                        return 0
                return 0  # Put photos without dates at the beginning for asc, end for desc
            else:  # filename
                return photo.name.lower()

        self.photos.sort(key=sort_key, reverse=(sort_order == "desc"))

        # For date sorting, put None dates at the end regardless of order
        if sort_by == "date":
            photos_with_date = [p for p in self.photos if p.date]
            photos_without_date = [p for p in self.photos if not p.date]
            if sort_order == "desc":
                self.photos = photos_with_date + photos_without_date
            else:
                self.photos = photos_without_date + photos_with_date

    def json_dump_obj(self):
        return self.photos


class SiteGenerator:
    def __init__(self, yaml_config):

        Config.init(yaml_config)

        self.yaml_config = yaml_config
        self.unique_person_slugs = {}

    def generate(self):

        print(f"[bold]Generating site from [magenta]{Config.instance().input_photos_dir}[magenta][/bold]")
        output_photos_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "web", "public", "static", "_gallery")
        )
        output_data_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "web", "src", "_gallery")
        )
        external_root = os.path.normpath(os.path.join(Config.instance().http_root, "static", "_gallery", "albums"))
        generated_site_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "web", "build")
        )

        # Paths
        output_albums_data_file = os.path.join(output_data_path, "albums_data.js")
        output_people_data_file = os.path.join(output_data_path, "people_data.js")
        output_site_data_file = os.path.join(output_data_path, "site_data.js")
        output_albums_photos_path = os.path.join(output_photos_path, "albums")

        # Cleanup and prep of deploy space
        if Config.instance().overwrite:
            shutil.rmtree(output_photos_path, ignore_errors=True)
            shutil.rmtree(generated_site_path, ignore_errors=True)

        os.makedirs(output_photos_path, exist_ok=True)
        shutil.rmtree(output_data_path, ignore_errors=True)
        os.makedirs(output_data_path, exist_ok=True)

        Albums.instance().process_path(
            Config.instance().input_photos_dir, output_albums_photos_path, external_root, self.yaml_config
        )

        with open(output_albums_data_file, "w") as outfile:
            output_str = "export const albums_data = "
            output_str += json.dumps(Albums.instance(), sort_keys=True, indent=3, cls=SimpleEncoder)
            output_str += ";"
            outfile.write(output_str)

        with open(output_people_data_file, "w") as outfile:
            output_str = "export const people_data = "
            output_str += json.dumps(People.instance(), sort_keys=True, indent=3, cls=SimpleEncoder)
            output_str += ";"
            outfile.write(output_str)

        # Generate photos data (always write the file so it can be statically imported)
        output_photos_data_file = os.path.join(output_data_path, "photos_data.js")
        if Config.instance().photos_enabled:
            photos = Photos.instance()
            photos.collect_all_photos()
            photos.sort_photos()
            with open(output_photos_data_file, "w") as outfile:
                output_str = "export const photos_data = "
                output_str += json.dumps(photos, sort_keys=True, indent=3, cls=SimpleEncoder)
                output_str += ";"
                outfile.write(output_str)
        else:
            with open(output_photos_data_file, "w") as outfile:
                outfile.write("export const photos_data = [];\n")

        with open(output_site_data_file, "w") as outfile:
            output_str = "export const site_data = "
            output_str += json.dumps(Site.instance(), sort_keys=True, indent=3, cls=SimpleEncoder)
            output_str += ";"
            outfile.write(output_str)


class PhotoProcessingFailure(Exception):
    def __init__(self, message="Failed to process photo"):
        self.message = message
        super().__init__(self.message)
