"""The people.json manifest.

The gallery keeps its people data inside the bundled web app, where it has no stable address.
This module writes the same information as a plain JSON file at the gallery root, so another
site can fetch it, show a few thumbnails for a person and link to the full gallery.
"""

import json
import os

from .config import DEFAULT_PEOPLE_MANIFEST_PHOTOS

MANIFEST_NAME = "people.json"
MANIFEST_VERSION = 1
# Every generated image lives under this folder of the gallery, whatever site.http_root is.
ASSET_MARKER = "static/_gallery/"


def _relative(path):
    """Make a generated image path relative to the gallery root, so it works under any http_root."""
    if path is None:
        return None
    start = path.find(ASSET_MARKER)
    return path[start:] if start >= 0 else path


def _unique_photos(photos):
    seen = set()
    unique = []
    for photo in photos:
        if photo.src not in seen:
            seen.add(photo.src)
            unique.append(photo)
    return unique


def _newest_first(photos):
    # Two stable passes: name order breaks ties, then date (ISO strings) newest first, undated last.
    by_name = sorted(photos, key=lambda photo: photo.slug)
    return sorted(by_name, key=lambda photo: photo.date or "", reverse=True)


def build_people_manifest(people, max_photos=DEFAULT_PEOPLE_MANIFEST_PHOTOS):
    """Describe each person as plain data. `people` maps name to Person, as People.people does."""
    entries = []
    for person in sorted(people.values(), key=lambda p: p.slug):
        photos = _newest_first(_unique_photos(person.photos))
        entries.append(
            {
                "name": person.name,
                "slug": person.slug,
                "url": "#/collections/people/%s" % person.slug,
                "count": len(photos),
                "thumb": _relative(person.src),
                "photos": [
                    {
                        "name": photo.name,
                        "thumb": _relative(photo.thumb),
                        "src": _relative(photo.src),
                        "url": "#/collections/people/%s/%s" % (person.slug, photo.slug),
                    }
                    for photo in photos[: max(max_photos, 0)]
                ],
            }
        )
    return {"version": MANIFEST_VERSION, "people": entries}


def write_people_manifest(public_dir, people, enabled, max_photos=DEFAULT_PEOPLE_MANIFEST_PHOTOS):
    """Write people.json into the web app's public folder, or remove a stale one when people are off."""
    path = os.path.join(public_dir, MANIFEST_NAME)
    if not enabled:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        return
    with open(path, "w", encoding="utf-8") as outfile:
        json.dump(build_people_manifest(people, max_photos), outfile, indent=2, ensure_ascii=False)
        outfile.write("\n")
