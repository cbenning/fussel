"""
Tests for the people.json manifest that other sites can fetch.
"""

import json
import os

from fussel.generator.generate import Person, Photo
from fussel.generator.people_manifest import build_people_manifest, write_people_manifest


def make_photo(slug, date, root="/static/_gallery/albums/trip"):
    return Photo(
        slug + ".jpg",
        800,
        600,
        "%s/1600x1600_%s.jpg" % (root, slug),
        "%s/500x500_%s.jpg" % (root, slug),
        slug,
        [],
        "%s/original_%s.jpg" % (root, slug),
        date,
    )


def make_person(name, slug, photos, src=None):
    person = Person(name, slug)
    person.photos = photos
    person.src = src
    return person


class TestBuildPeopleManifest:
    def test_describes_a_person_with_paths_relative_to_the_gallery_root(self):
        photo = make_photo("beach", "2020-07-01T10:00:00")
        person = make_person(
            "Ada Lovelace", "ada-lovelace", [photo], src="/static/_gallery/albums/trip/ada-lovelace_beach.jpg"
        )

        manifest = build_people_manifest({"Ada Lovelace": person})

        assert manifest == {
            "version": 1,
            "people": [
                {
                    "name": "Ada Lovelace",
                    "slug": "ada-lovelace",
                    "url": "#/collections/people/ada-lovelace",
                    "count": 1,
                    "thumb": "static/_gallery/albums/trip/ada-lovelace_beach.jpg",
                    "photos": [
                        {
                            "name": "beach.jpg",
                            "thumb": "static/_gallery/albums/trip/500x500_beach.jpg",
                            "src": "static/_gallery/albums/trip/1600x1600_beach.jpg",
                            "url": "#/collections/people/ada-lovelace/beach",
                        }
                    ],
                }
            ],
        }

    def test_paths_do_not_depend_on_http_root(self):
        photo = make_photo("beach", "2020-07-01", root="/gallery/static/_gallery/albums/trip")
        person = make_person("Ada", "ada", [photo], src="/gallery/static/_gallery/albums/trip/ada_beach.jpg")

        entry = build_people_manifest({"Ada": person})["people"][0]

        assert entry["thumb"] == "static/_gallery/albums/trip/ada_beach.jpg"
        assert entry["photos"][0]["thumb"] == "static/_gallery/albums/trip/500x500_beach.jpg"
        assert entry["photos"][0]["src"] == "static/_gallery/albums/trip/1600x1600_beach.jpg"

    def test_lists_newest_photos_first_and_caps_them_but_counts_all(self):
        photos = [make_photo("p%d" % n, "2020-01-0%dT00:00:00" % n) for n in range(1, 6)]
        photos.append(make_photo("undated", None))
        person = make_person("Ada", "ada", photos)

        entry = build_people_manifest({"Ada": person}, max_photos=3)["people"][0]

        assert entry["count"] == 6
        assert [p["name"] for p in entry["photos"]] == ["p5.jpg", "p4.jpg", "p3.jpg"]

    def test_undated_photos_come_last(self):
        person = make_person("Ada", "ada", [make_photo("undated", None), make_photo("dated", "2020-01-01")])

        entry = build_people_manifest({"Ada": person})["people"][0]

        assert [p["name"] for p in entry["photos"]] == ["dated.jpg", "undated.jpg"]

    def test_a_photo_with_two_tags_of_one_person_counts_once(self):
        photo = make_photo("beach", "2020-07-01")
        person = make_person("Ada", "ada", [photo, photo])

        entry = build_people_manifest({"Ada": person})["people"][0]

        assert entry["count"] == 1
        assert len(entry["photos"]) == 1

    def test_people_are_sorted_by_slug(self):
        people = {
            "Zed": make_person("Zed", "zed", []),
            "Ada": make_person("Ada", "ada", []),
            "Max": make_person("Max", "max", []),
        }

        manifest = build_people_manifest(people)

        assert [p["slug"] for p in manifest["people"]] == ["ada", "max", "zed"]

    def test_a_person_without_a_face_crop_has_a_null_thumb(self):
        entry = build_people_manifest({"Ada": make_person("Ada", "ada", [])})["people"][0]

        assert entry["thumb"] is None

    def test_zero_photos_per_person_lists_none_but_still_counts(self):
        person = make_person("Ada", "ada", [make_photo("beach", "2020-07-01")])

        entry = build_people_manifest({"Ada": person}, max_photos=0)["people"][0]

        assert entry["photos"] == []
        assert entry["count"] == 1

    def test_no_people_gives_an_empty_list(self):
        assert build_people_manifest({}) == {"version": 1, "people": []}


class TestWritePeopleManifest:
    def test_writes_people_json_as_utf8(self, temp_dir):
        person = make_person("Zoë Müller", "zoe-muller", [])

        write_people_manifest(temp_dir, {"Zoë Müller": person}, enabled=True, max_photos=6)

        with open(os.path.join(temp_dir, "people.json"), encoding="utf-8") as f:
            text = f.read()
        assert "Zoë Müller" in text
        assert json.loads(text)["people"][0]["slug"] == "zoe-muller"

    def test_removes_a_stale_file_when_people_are_disabled(self, temp_dir):
        path = os.path.join(temp_dir, "people.json")
        with open(path, "w") as f:
            f.write("{}")

        write_people_manifest(temp_dir, {}, enabled=False, max_photos=6)

        assert not os.path.exists(path)

    def test_disabled_with_no_file_is_fine(self, temp_dir):
        write_people_manifest(temp_dir, {}, enabled=False, max_photos=6)

        assert not os.path.exists(os.path.join(temp_dir, "people.json"))
