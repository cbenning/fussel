"""
Per-format tests backing the support matrix in README.md ("Feature support by format").
"""

import os
from datetime import datetime
from unittest.mock import Mock

import pytest
from PIL import Image, features
from PIL.PngImagePlugin import PngInfo

from fussel.generator import generate
from fussel.generator.config import Config
from fussel.generator.generate import People, Photo

HAS_AVIF = features.check("avif")
HAS_WEBP = features.check("webp")
WEBP = pytest.param(".webp", marks=pytest.mark.skipif(not HAS_WEBP, reason="Pillow built without WebP"))

ALL_FORMATS = [
    ".jpg",
    ".png",
    ".gif",
    pytest.param(".avif", marks=pytest.mark.skipif(not HAS_AVIF, reason="Pillow built without AVIF")),
    WEBP,
]
EXIF_FORMATS = [
    ".jpg",
    ".png",
    pytest.param(".avif", marks=pytest.mark.skipif(not HAS_AVIF, reason="Pillow built without AVIF")),
    WEBP,
]
XMP_FORMATS = EXIF_FORMATS  # formats that can embed XMP

SIZE = (100, 80)
EXIF_DATE = "2020:01:02 03:04:05"
EXIF_DATE_ISO = "2020-01-02T03:04:05"


def init_config(**overrides):
    values = {
        "gallery.input_path": "/unused",
        "gallery.photo_sizes": [[50, 50]],
        "gallery.watermark.enable": False,
        "gallery.people.enable": True,
        "gallery.exif_transpose": False,
        "gallery.overwrite": False,
    }
    values.update(overrides)
    yaml_config = Mock()
    yaml_config.getKey = Mock(side_effect=lambda key, default=None: values.get(key, default))
    Config.init(yaml_config)


def make_exif(orientation=None):
    exif = Image.Exif()
    exif[271] = "TestMake"
    exif[306] = EXIF_DATE
    if orientation is not None:
        exif[274] = orientation
    return exif


def save_image(path, exif=None):
    kwargs = {"exif": exif} if exif is not None else {}
    Image.new("RGB", SIZE, "red").save(path, **kwargs)
    return str(path)


def process(tmp_path, photo_path):
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    photo = Photo.process_photo("/ext", photo_path, os.path.basename(photo_path), "img", str(out), Mock())
    return photo, out


def resized_files(out):
    return [f for f in os.listdir(out) if not f.startswith("original_")]


@pytest.fixture(autouse=True)
def reset_singletons():
    People._instance = None
    yield
    People._instance = None
    Config._instance = None


class TestResizeAndDownload:
    @pytest.mark.parametrize("ext", ALL_FORMATS)
    def test_processes_and_keeps_original(self, tmp_path, ext):
        init_config()
        photo, out = process(tmp_path, save_image(tmp_path / f"img{ext}"))

        assert (photo.width, photo.height) == SIZE
        assert (out / f"original_img{ext}").exists()
        assert len(resized_files(out)) == 1
        assert photo.originalSrc.endswith(f"original_img{ext}")

    def test_gif_resized_copy_is_first_frame_only(self, tmp_path):
        init_config()
        frames = [Image.new("RGB", SIZE, c) for c in ("red", "blue")]
        path = tmp_path / "anim.gif"
        frames[0].save(path, save_all=True, append_images=frames[1:])

        _, out = process(tmp_path, str(path))

        with Image.open(out / "original_img.gif") as original:
            assert original.n_frames == 2
        with Image.open(out / resized_files(out)[0]) as resized:
            assert getattr(resized, "n_frames", 1) == 1

    @pytest.mark.skipif(not HAS_WEBP, reason="Pillow built without WebP")
    def test_animated_webp_resized_copy_is_first_frame_only(self, tmp_path):
        init_config()
        frames = [Image.new("RGB", SIZE, c) for c in ("red", "blue")]
        path = tmp_path / "anim.webp"
        frames[0].save(path, save_all=True, append_images=frames[1:])

        _, out = process(tmp_path, str(path))

        with Image.open(out / "original_img.webp") as original:
            assert original.n_frames == 2
        with Image.open(out / resized_files(out)[0]) as resized:
            assert getattr(resized, "n_frames", 1) == 1

    def test_extension_format_mismatch_is_skipped(self, tmp_path):
        init_config()
        path = tmp_path / "fake.jpg"
        Image.new("RGB", SIZE, "red").save(path, format="PNG")

        with pytest.raises(Exception, match="rename it to match"):
            process(tmp_path, str(path))


def save_with_xmp(path, xmp):
    """Save a small image with raw XMP embedded in the format's native slot."""
    im = Image.new("RGB", SIZE, "red")
    if str(path).endswith(".png"):
        info = PngInfo()
        info.add_itxt("XML:com.adobe.xmp", xmp.decode("utf-8"))
        im.save(path, pnginfo=info)
    else:
        im.save(path, xmp=xmp)
    return str(path)


FACE_XMP = (
    b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF>'
    b'<rdf:Description mwg-rs:type="Face" mwg-rs:name="Jane">'
    b'<mwg-rs:Area stArea:x="0.5" stArea:y="0.5" stArea:w="0.2" stArea:h="0.3"/>'
    b"</rdf:Description></rdf:RDF></x:xmpmeta>"
)
# Element-style MWG regions, as written by exiftool (rdf:parseType="Resource")
FACE_XMP_ELEMENTS = (
    b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF><rdf:Description>'
    b'<mwg-rs:Regions rdf:parseType="Resource"><mwg-rs:RegionList><rdf:Bag>'
    b'<rdf:li rdf:parseType="Resource">'
    b"<mwg-rs:Name>Jane</mwg-rs:Name><mwg-rs:Type>Face</mwg-rs:Type>"
    b'<mwg-rs:Area stArea:x="0.5" stArea:y="0.5" stArea:w="0.2" stArea:h="0.3" stArea:unit="normalized"/>'
    b'</rdf:li><rdf:li rdf:parseType="Resource">'
    b"<mwg-rs:Name>Bob</mwg-rs:Name><mwg-rs:Type>Face</mwg-rs:Type>"
    b'<mwg-rs:Area stArea:x="0.1" stArea:y="0.2" stArea:w="0.1" stArea:h="0.1" stArea:unit="normalized"/>'
    b"</rdf:li></rdf:Bag></mwg-rs:RegionList></mwg-rs:Regions></rdf:Description></rdf:RDF></x:xmpmeta>"
)
DATE_XMP = (
    b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF>'
    b'<rdf:Description xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmp:CreateDate="2020-01-02T03:04:05"/>'
    b"</rdf:RDF></x:xmpmeta>"
)


class TestFaceTags:
    @pytest.mark.parametrize("ext", XMP_FORMATS)
    def test_face_tags_are_read_from_xmp(self, tmp_path, ext):
        path = save_with_xmp(tmp_path / f"face{ext}", FACE_XMP)

        faces = People.instance().extract_faces(path)

        assert [f.name for f in faces] == ["Jane"]

    @pytest.mark.parametrize("ext", XMP_FORMATS)
    def test_element_style_mwg_regions_are_read(self, tmp_path, ext):
        path = save_with_xmp(tmp_path / f"face{ext}", FACE_XMP_ELEMENTS)

        faces = People.instance().extract_faces(path)

        assert [(f.name, f.geometry.x) for f in faces] == [("Jane", "0.5"), ("Bob", "0.1")]

    def test_non_face_element_region_is_ignored(self, tmp_path):
        xmp = FACE_XMP_ELEMENTS.replace(b"<mwg-rs:Type>Face</mwg-rs:Type>", b"<mwg-rs:Type>Pet</mwg-rs:Type>")
        path = save_with_xmp(tmp_path / "pet.jpg", xmp)

        assert People.instance().extract_faces(path) == []

    def test_gif_has_no_faces_and_no_error(self, tmp_path):
        init_config()
        photo, out = process(tmp_path, save_image(tmp_path / "img.gif"))
        people = People.instance()

        faces = people.detect_faces(photo, str(tmp_path / "img.gif"), str(out), str(out), "/ext")

        assert faces == []
        assert photo.faces == []
        assert people.people == {}


class TestExifAndDate:
    @pytest.mark.parametrize("ext", EXIF_FORMATS)
    def test_embedded_exif_is_read(self, tmp_path, ext):
        path = save_image(tmp_path / f"img{ext}", exif=make_exif())

        assert Photo._extract_date(path) == EXIF_DATE_ISO
        assert Photo._extract_exif(path)["camera"]["make"] == "TestMake"

    @pytest.mark.parametrize("ext", XMP_FORMATS)
    def test_xmp_date_is_used_without_exif(self, tmp_path, ext):
        path = save_with_xmp(tmp_path / f"img{ext}", DATE_XMP)

        assert Photo._extract_date(path) == EXIF_DATE_ISO

    @pytest.mark.parametrize("ext", ALL_FORMATS)
    def test_without_exif_falls_back_to_mtime(self, tmp_path, ext):
        path = save_image(tmp_path / f"img{ext}")

        assert Photo._extract_date(path) == datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
        assert Photo._extract_exif(path) == {}


class TestExifTranspose:
    @pytest.mark.parametrize("ext", EXIF_FORMATS)
    def test_orientation_swaps_dimensions(self, tmp_path, ext):
        init_config(**{"gallery.exif_transpose": True})
        photo, _ = process(tmp_path, save_image(tmp_path / f"img{ext}", exif=make_exif(orientation=6)))

        assert (photo.width, photo.height) == (SIZE[1], SIZE[0])

    def test_gif_keeps_dimensions(self, tmp_path):
        init_config(**{"gallery.exif_transpose": True})
        photo, _ = process(tmp_path, save_image(tmp_path / "img.gif"))

        assert (photo.width, photo.height) == SIZE


class TestWatermark:
    @pytest.mark.parametrize("ext", ALL_FORMATS)
    def test_watermark_is_applied_to_largest_size(self, tmp_path, ext):
        watermark = tmp_path / "wm.png"
        Image.new("RGBA", (20, 20), (0, 255, 0, 255)).save(watermark)
        init_config(
            **{
                "gallery.watermark.enable": True,
                "gallery.watermark.path": str(watermark),
                "gallery.watermark.size_ratio": 0.5,
                "gallery.overwrite": True,
            }
        )

        _, out = process(tmp_path, save_image(tmp_path / f"img{ext}"))

        with Image.open(out / resized_files(out)[0]) as marked:
            r, g, _ = marked.convert("RGB").getpixel((marked.width - 1, marked.height - 1))
        assert g > r

    def test_watermark_is_applied_without_overwrite(self, tmp_path):
        watermark = tmp_path / "wm.png"
        Image.new("RGBA", (20, 20), (0, 255, 0, 255)).save(watermark)
        init_config(
            **{
                "gallery.watermark.enable": True,
                "gallery.watermark.path": str(watermark),
                "gallery.watermark.size_ratio": 0.5,
                "gallery.overwrite": False,
            }
        )

        _, out = process(tmp_path, save_image(tmp_path / "img.jpg"))

        with Image.open(out / resized_files(out)[0]) as marked:
            r, g, _ = marked.convert("RGB").getpixel((marked.width - 1, marked.height - 1))
        assert g > r

    def test_rerun_without_overwrite_does_not_watermark_again(self, tmp_path, mocker):
        watermark = tmp_path / "wm.png"
        Image.new("RGBA", (20, 20), (0, 255, 0, 255)).save(watermark)
        init_config(
            **{
                "gallery.watermark.enable": True,
                "gallery.watermark.path": str(watermark),
                "gallery.overwrite": False,
            }
        )
        photo = save_image(tmp_path / "img.jpg")
        spy = mocker.spy(generate, "apply_watermark")

        process(tmp_path, photo)
        process(tmp_path, photo)

        assert spy.call_count == 1

    def test_rerun_with_overwrite_watermarks_again(self, tmp_path, mocker):
        watermark = tmp_path / "wm.png"
        Image.new("RGBA", (20, 20), (0, 255, 0, 255)).save(watermark)
        init_config(
            **{
                "gallery.watermark.enable": True,
                "gallery.watermark.path": str(watermark),
                "gallery.overwrite": True,
            }
        )
        photo = save_image(tmp_path / "img.jpg")
        spy = mocker.spy(generate, "apply_watermark")

        process(tmp_path, photo)
        process(tmp_path, photo)

        assert spy.call_count == 2
