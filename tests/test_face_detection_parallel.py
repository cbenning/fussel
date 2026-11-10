"""
Regression test for face data being lost in large albums (#198).

Face jobs used to travel from the worker processes through a multiprocessing.Queue that was
only read after the pool was terminated. The pipe behind it holds about 64 KB (roughly 110
items), so everything beyond that was silently dropped.
"""

import os
from unittest.mock import Mock

import pytest
from PIL import Image

from fussel.generator.config import Config
from fussel.generator.generate import Albums, People

PHOTO_COUNT = 200  # well beyond what fits in the queue's pipe buffer

XMP = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF>'
    '<rdf:Description mwg-rs:type="Face" mwg-rs:name="Person{i}">'
    '<mwg-rs:Area stArea:x="0.5" stArea:y="0.5" stArea:w="0.2" stArea:h="0.3"/>'
    "</rdf:Description></rdf:RDF></x:xmpmeta>"
)


@pytest.fixture(autouse=True)
def reset_singletons():
    for cls in (People, Albums):
        cls._instance = None
    yield
    for cls in (People, Albums):
        cls._instance = None
    Config._instance = None


def test_faces_in_a_large_album_are_not_lost(tmp_path):
    root = tmp_path / "in"
    album = root / "album"
    album.mkdir(parents=True)
    for i in range(PHOTO_COUNT):
        Image.new("RGB", (60, 48), "red").save(album / f"p{i:04d}.jpg", xmp=XMP.format(i=i).encode())

    values = {
        "gallery.input_path": str(root),
        "gallery.photo_sizes": [[40, 40]],
        "gallery.watermark.enable": False,
        "gallery.people.enable": True,
        "gallery.overwrite": True,
        "gallery.parallel_tasks": 4,
    }
    yaml_config = Mock()
    yaml_config.getKey = Mock(side_effect=lambda key, default=None: values.get(key, default))
    Config.init(yaml_config)
    out = tmp_path / "out"
    out.mkdir()

    Albums.instance().process_path(str(root), str(out), "/ext", yaml_config)

    people = People.instance().people
    assert len(people) == PHOTO_COUNT
    assert len(os.listdir(out / "album")) > PHOTO_COUNT
