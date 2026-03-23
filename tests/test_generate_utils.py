"""
Tests for utility classes in fussel.generator.generate module.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from fussel.generator.generate import Albums, Person, Photo, PhotoProcessingFailure, Photos, SimpleEncoder, Site


class TestSimpleEncoder:
    """Tests for SimpleEncoder JSON encoder."""

    def test_encode_object_with_json_dump_obj(self):
        """Test encoding an object with json_dump_obj method."""

        class TestObject:
            def json_dump_obj(self):
                return {"custom": "data"}

        encoder = SimpleEncoder()
        result = encoder.default(TestObject())
        assert result == {"custom": "data"}

    def test_encode_object_without_json_dump_obj(self):
        """Test encoding an object without json_dump_obj method."""

        class TestObject:
            def __init__(self):
                self.attr1 = "value1"
                self.attr2 = "value2"

        encoder = SimpleEncoder()
        result = encoder.default(TestObject())
        assert result == {"attr1": "value1", "attr2": "value2"}

    # Note: Testing standard type encoding is frivolous - it's just framework behavior.
    # The encoder is only meant for custom objects, which we test above.


class TestSite:
    """Tests for Site singleton class."""

    def setup_method(self):
        """Reset Site singleton before each test."""
        Site._instance = None

    def test_cannot_instantiate_directly(self):
        """Test that Site cannot be instantiated directly."""
        with pytest.raises(RuntimeError):
            Site()

    def test_instance_returns_singleton(self):
        """Test that instance() returns the same object."""
        with patch("fussel.generator.generate.Config") as mock_config:
            mock_config.instance.return_value.site_name = "Test Site"
            mock_config.instance.return_value.people_enabled = True

            instance1 = Site.instance()
            instance2 = Site.instance()

            assert instance1 is instance2
            assert instance1 is Site._instance

    def test_site_initialization(self):
        """Test that Site initializes with config values."""
        with patch("fussel.generator.generate.Config") as mock_config:
            mock_config.instance.return_value.site_name = "My Gallery"
            mock_config.instance.return_value.people_enabled = False

            site = Site.instance()

            assert site.site_name == "My Gallery"
            assert site.people_enabled is False


# Note: FaceGeometry and Face are simple dataclasses with no business logic.
# Testing them would be frivolous - they're just data containers.
# We test them indirectly through People.extract_faces() which uses them.


class TestPerson:
    """Tests for Person class."""

    # Note: Person initialization is just attribute assignment - tested indirectly.
    # Photo management is just list operations - not business logic.

    def test_has_thumbnail_false(self):
        """Test has_thumbnail returns False when src is None."""
        person = Person(name="John Doe", slug="john-doe")
        assert person.has_thumbnail() is False

    def test_has_thumbnail_true(self):
        """Test has_thumbnail returns True when src is set."""
        person = Person(name="John Doe", slug="john-doe")
        person.src = "/path/to/thumbnail.jpg"
        assert person.has_thumbnail() is True


class TestAlbum:
    """Tests for Album class."""

    # Note: Album initialization and add_photo are trivial (attribute assignment and list.append).
    # These are tested indirectly through Albums.process_album_path() which uses them.


class TestPhoto:
    """Tests for Photo class."""

    # Note: Photo initialization is just attribute assignment - tested indirectly.
    # Photo.faces is just a list - not business logic worth testing separately.

    @patch("fussel.generator.generate.Config")
    @patch("fussel.generator.generate.Image")
    @patch("fussel.generator.generate.shutil")
    @patch("fussel.generator.generate.os.path.exists")
    @patch("fussel.generator.generate.calculate_new_size")
    @patch("fussel.generator.generate.extract_extension")
    @patch("fussel.generator.generate.apply_watermark")
    def test_process_photo_success(
        self, mock_watermark, mock_extract, mock_calc_size, mock_exists, mock_shutil, mock_image, mock_config
    ):
        """Test successful photo processing."""
        # Setup mocks
        mock_config.instance.return_value.overwrite = False
        mock_config.instance.return_value.watermark_enabled = False
        mock_config.instance.return_value.people_enabled = False
        mock_config.instance.return_value.exif_transpose = False
        mock_config.instance.return_value.photo_sizes = [(500, 500), (800, 800), (1024, 1024), (1600, 1600)]

        mock_exists.return_value = False
        mock_extract.return_value = ".jpg"
        mock_calc_size.return_value = (500, 375)

        # Mock Image operations
        mock_img = MagicMock()
        mock_img.size = (2000, 1500)
        mock_img.verify.return_value = None
        mock_img.transpose.return_value = mock_img
        mock_img.thumbnail.return_value = None
        mock_img.save.return_value = None

        mock_image.open.return_value.__enter__.return_value = mock_img
        mock_image.open.return_value.__exit__.return_value = None

        # Mock shutil
        mock_shutil.copyfile.return_value = None

        # Test
        from multiprocessing import Queue

        people_q = Queue()

        result = Photo.process_photo(
            external_path="/external",
            photo="/path/to/photo.jpg",
            filename="photo.jpg",
            slug="photo",
            output_path="/output",
            people_q=people_q,
        )

        assert result is not None
        assert result.name == "photo.jpg"
        assert result.width == 2000
        assert result.height == 1500
        assert result.slug == "photo"

    @patch("fussel.generator.generate.Config")
    @patch("fussel.generator.generate.Image")
    def test_process_photo_verification_failure(self, mock_image, mock_config):
        """Test photo processing with verification failure."""
        mock_config.instance.return_value.overwrite = False

        # Mock Image to raise exception on verify
        mock_img = MagicMock()
        mock_img.verify.side_effect = Exception("Invalid image")

        mock_image.open.return_value.__enter__.return_value = mock_img
        mock_image.open.return_value.__exit__.return_value = None

        from multiprocessing import Queue

        from fussel.generator.generate import PhotoProcessingFailure

        people_q = Queue()

        with pytest.raises(PhotoProcessingFailure, match="Image Verification"):
            Photo.process_photo(
                external_path="/external",
                photo="/path/to/bad_photo.jpg",
                filename="bad_photo.jpg",
                slug="bad-photo",
                output_path="/output",
                people_q=people_q,
            )

    @patch("fussel.generator.generate.Config")
    @patch("fussel.generator.generate.Image")
    @patch("fussel.generator.generate.shutil")
    @patch("fussel.generator.generate.os.path.exists")
    @patch("fussel.generator.generate.calculate_new_size")
    @patch("fussel.generator.generate.extract_extension")
    @patch("fussel.generator.generate.apply_watermark")
    @patch("fussel.generator.generate.ImageOps")
    def test_process_photo_with_watermark_and_exif(
        self,
        mock_imageops,
        mock_watermark,
        mock_extract,
        mock_calc_size,
        mock_exists,
        mock_shutil,
        mock_image,
        mock_config,
    ):
        """Test photo processing with watermark enabled and exif_transpose."""
        mock_config.instance.return_value.overwrite = False
        mock_config.instance.return_value.watermark_enabled = True
        mock_config.instance.return_value.watermark_path = "/path/watermark.png"
        mock_config.instance.return_value.people_enabled = False
        mock_config.instance.return_value.exif_transpose = True
        mock_config.instance.return_value.photo_sizes = [(500, 500), (800, 800), (1024, 1024), (1600, 1600)]

        mock_exists.return_value = False
        mock_extract.return_value = ".jpg"
        mock_calc_size.return_value = (500, 375)

        mock_img = MagicMock()
        mock_img.size = (2000, 1500)
        mock_img.verify.return_value = None
        mock_img.transpose.return_value = mock_img
        mock_img.thumbnail.return_value = None
        mock_img.save.return_value = None
        mock_imageops.exif_transpose.return_value = mock_img

        mock_watermark_img = MagicMock()
        mock_watermark_img.size = (100, 50)

        # Image.open is called for:
        # EXIF date extraction (3x original photo): method1 getexif, method2 _getexif, method3 XMP
        # EXIF metadata extraction (1x original photo): _extract_exif
        # Verification (2x original photo): verify, transpose
        # Processing (1x new_original_photo): get size
        # Thumbnails (4x new_original_photo): 500x500, 800x800, 1024x1024, 1600x1600
        # Watermark (1x watermark_path)
        # Total: 12 calls
        def cm(img):
            return MagicMock(__enter__=Mock(return_value=img), __exit__=Mock())

        mock_image.open.side_effect = [
            cm(mock_img),  # method 1: getexif()
            cm(mock_img),  # method 2: _getexif()
            cm(mock_img),  # method 3: XMP applist
            cm(mock_img),  # _extract_exif
            cm(mock_img),  # verify
            cm(mock_img),  # transpose
            cm(mock_img),  # get size
            cm(mock_img),  # thumbnail 500x500
            cm(mock_img),  # thumbnail 800x800
            cm(mock_img),  # thumbnail 1024x1024
            cm(mock_img),  # thumbnail 1600x1600
            cm(mock_watermark_img),  # watermark
        ]

        mock_shutil.copyfile.return_value = None

        from multiprocessing import Queue

        people_q = Queue()

        result = Photo.process_photo(
            external_path="/external",
            photo="/path/to/photo.jpg",
            filename="photo.jpg",
            slug="photo",
            output_path="/output",
            people_q=people_q,
        )

        assert result is not None
        # Verify watermark was applied
        mock_watermark.assert_called_once()
        # Verify exif_transpose was called
        mock_imageops.exif_transpose.assert_called()

    @patch("fussel.generator.generate.Config")
    @patch("fussel.generator.generate.Image")
    @patch("fussel.generator.generate.shutil")
    @patch("fussel.generator.generate.os.path.exists")
    @patch("fussel.generator.generate.calculate_new_size")
    @patch("fussel.generator.generate.extract_extension")
    @patch("fussel.generator.generate.apply_watermark")
    def test_watermark_applied_to_new_photo_when_overwrite_false(
        self, mock_watermark, mock_extract, mock_calc_size, mock_exists, mock_shutil, mock_image, mock_config
    ):
        """Watermark must be applied to new photos even when overwrite=False.

        Regression test: the watermark condition was checking new_original_photo
        (which is always present after the copy step) instead of largest_src
        (the thumbnail the watermark is stamped onto).  With overwrite=False and
        a brand-new photo the watermark was silently skipped.
        """
        mock_config.instance.return_value.overwrite = False
        mock_config.instance.return_value.watermark_enabled = True
        mock_config.instance.return_value.watermark_path = "/path/watermark.png"
        mock_config.instance.return_value.people_enabled = False
        mock_config.instance.return_value.exif_transpose = False
        mock_config.instance.return_value.photo_sizes = [(500, 500)]

        mock_extract.return_value = ".jpg"
        mock_calc_size.return_value = (500, 375)

        # Simulate real-world: new_original_photo exists after copy, thumbnails do not.
        # new_original_photo path ends with "original_photo.jpg"
        # thumbnail path ends with "500x375_photo.jpg"
        import os as _os

        def exists_side_effect(path):
            return "original_" in _os.path.basename(path)

        mock_exists.side_effect = exists_side_effect

        mock_img = MagicMock()
        mock_img.size = (2000, 1500)
        mock_img.verify.return_value = None
        mock_img.transpose.return_value = mock_img
        mock_img.thumbnail.return_value = None
        mock_img.save.return_value = None

        mock_watermark_img = MagicMock()
        mock_watermark_img.size = (100, 50)

        def cm(img):
            return MagicMock(__enter__=Mock(return_value=img), __exit__=Mock())

        mock_image.open.side_effect = [
            cm(mock_img),  # method 1: getexif
            cm(mock_img),  # method 2: _getexif
            cm(mock_img),  # method 3: XMP
            cm(mock_img),  # _extract_exif
            cm(mock_img),  # verify
            cm(mock_img),  # transpose
            cm(mock_img),  # get size from new_original_photo
            cm(mock_img),  # thumbnail 500x500
            cm(mock_watermark_img),  # watermark
        ]
        mock_shutil.copyfile.return_value = None

        from multiprocessing import Queue

        people_q = Queue()

        result = Photo.process_photo(
            external_path="/external",
            photo="/path/to/photo.jpg",
            filename="photo.jpg",
            slug="photo",
            output_path="/output",
            people_q=people_q,
        )

        assert result is not None
        mock_watermark.assert_called_once(), "Watermark must be applied to new photos even when overwrite=False"

    @patch("fussel.generator.generate.Config")
    @patch("fussel.generator.generate.Image")
    @patch("fussel.generator.generate.shutil")
    @patch("fussel.generator.generate.os.path.exists")
    @patch("fussel.generator.generate.calculate_new_size")
    @patch("fussel.generator.generate.extract_extension")
    def test_process_photo_overwrite_mode(
        self, mock_extract, mock_calc_size, mock_exists, mock_shutil, mock_image, mock_config
    ):
        """Test photo processing in overwrite mode."""
        mock_config.instance.return_value.overwrite = True
        mock_config.instance.return_value.watermark_enabled = False
        mock_config.instance.return_value.people_enabled = False
        mock_config.instance.return_value.exif_transpose = False
        mock_config.instance.return_value.photo_sizes = [(500, 500), (800, 800), (1024, 1024), (1600, 1600)]

        mock_exists.return_value = True  # File exists but overwrite=True
        mock_extract.return_value = ".jpg"
        mock_calc_size.return_value = (500, 375)

        mock_img = MagicMock()
        mock_img.size = (2000, 1500)
        mock_img.verify.return_value = None
        mock_img.transpose.return_value = mock_img
        mock_img.thumbnail.return_value = None
        mock_img.save.return_value = None

        mock_image.open.return_value.__enter__.return_value = mock_img
        mock_image.open.return_value.__exit__.return_value = None

        mock_shutil.copyfile.return_value = None

        from multiprocessing import Queue

        people_q = Queue()

        result = Photo.process_photo(
            external_path="/external",
            photo="/path/to/photo.jpg",
            filename="photo.jpg",
            slug="photo",
            output_path="/output",
            people_q=people_q,
        )

        assert result is not None
        # Verify copyfile was called even though file exists (overwrite=True)
        assert mock_shutil.copyfile.called


class TestPhotoProcessingFailure:
    """Tests for PhotoProcessingFailure exception."""

    def test_exception_with_message(self):
        """Test PhotoProcessingFailure with custom message."""
        exception = PhotoProcessingFailure(message="Custom error message")
        assert str(exception) == "Custom error message"
        assert exception.message == "Custom error message"

    def test_exception_with_default_message(self):
        """Test PhotoProcessingFailure with default message."""
        exception = PhotoProcessingFailure()
        assert "Failed to process photo" in str(exception)
        assert exception.message == "Failed to process photo"


class TestPhotoUnidentifiedImageError:
    """Tests for the UnidentifiedImageError cleanup path in process_photo."""

    @patch("fussel.generator.generate.Config")
    @patch("fussel.generator.generate.Image")
    @patch("fussel.generator.generate.shutil")
    @patch("fussel.generator.generate.os.path.exists")
    @patch("fussel.generator.generate.os.remove")
    @patch("fussel.generator.generate.extract_extension")
    def test_unidentified_image_removes_file_when_exists(
        self, mock_extract, mock_remove, mock_exists, mock_shutil, mock_image, mock_config
    ):
        """When Image.open raises UnidentifiedImageError on the copy,
        the copied file is removed and PhotoProcessingFailure is raised."""
        from PIL.Image import UnidentifiedImageError

        mock_config.instance.return_value.overwrite = False
        mock_extract.return_value = ".jpg"

        mock_img = MagicMock()
        mock_img.verify.return_value = None
        mock_img.transpose.return_value = mock_img

        bad_cm = MagicMock()
        bad_cm.__enter__ = Mock(side_effect=UnidentifiedImageError("bad image"))
        bad_cm.__exit__ = Mock(return_value=False)

        good_cm = MagicMock(__enter__=Mock(return_value=mock_img), __exit__=Mock())

        # First 3 calls are EXIF date methods, then _extract_exif, then verify, then
        # transpose, then the copy open raises UnidentifiedImageError.
        mock_image.open.side_effect = [
            good_cm,  # method 1 getexif
            good_cm,  # method 2 _getexif
            good_cm,  # method 3 XMP
            good_cm,  # _extract_exif
            good_cm,  # verify
            good_cm,  # transpose
            bad_cm,  # open new_original_photo -> UnidentifiedImageError
        ]
        mock_exists.return_value = True  # file exists at cleanup time

        from multiprocessing import Queue

        people_q = Queue()

        with pytest.raises(PhotoProcessingFailure):
            Photo.process_photo(
                external_path="/external",
                photo="/path/to/photo.jpg",
                filename="photo.jpg",
                slug="photo",
                output_path="/output",
                people_q=people_q,
            )

        mock_remove.assert_called_once()

    @patch("fussel.generator.generate.Config")
    @patch("fussel.generator.generate.Image")
    @patch("fussel.generator.generate.shutil")
    @patch("fussel.generator.generate.os.path.exists")
    @patch("fussel.generator.generate.os.remove")
    @patch("fussel.generator.generate.extract_extension")
    def test_unidentified_image_skips_remove_when_not_exists(
        self, mock_extract, mock_remove, mock_exists, mock_shutil, mock_image, mock_config
    ):
        """When Image.open raises UnidentifiedImageError but the file was
        never written, os.remove is NOT called."""
        from PIL.Image import UnidentifiedImageError

        mock_config.instance.return_value.overwrite = False
        mock_extract.return_value = ".jpg"

        mock_img = MagicMock()
        mock_img.verify.return_value = None
        mock_img.transpose.return_value = mock_img

        bad_cm = MagicMock()
        bad_cm.__enter__ = Mock(side_effect=UnidentifiedImageError("bad image"))
        bad_cm.__exit__ = Mock(return_value=False)

        good_cm = MagicMock(__enter__=Mock(return_value=mock_img), __exit__=Mock())

        mock_image.open.side_effect = [
            good_cm,
            good_cm,
            good_cm,  # EXIF date methods
            good_cm,  # _extract_exif
            good_cm,
            good_cm,  # verify + transpose
            bad_cm,  # open copy -> UnidentifiedImageError
        ]
        mock_exists.return_value = False  # file was never written

        from multiprocessing import Queue

        people_q = Queue()

        with pytest.raises(PhotoProcessingFailure):
            Photo.process_photo(
                external_path="/external",
                photo="/path/to/photo.jpg",
                filename="photo.jpg",
                slug="photo",
                output_path="/output",
                people_q=people_q,
            )

        mock_remove.assert_not_called()


class TestPhotos:
    """Tests for Photos singleton: collect_all_photos and sort_photos."""

    def setup_method(self):
        Photos._instance = None
        Albums._instance = None

    @patch("fussel.generator.generate.Albums")
    def test_collect_all_photos_empty(self, mock_albums_class):
        """collect_all_photos with no albums produces empty list."""
        mock_albums = Mock()
        mock_albums.albums = {}
        mock_albums_class.instance.return_value = mock_albums

        photos = Photos.instance()
        photos.collect_all_photos()

        assert photos.photos == []

    @patch("fussel.generator.generate.Albums")
    def test_collect_all_photos_sets_album_slug(self, mock_albums_class):
        """collect_all_photos sets albumSlug on each photo and collects them."""
        photo1, photo2, photo3 = Mock(), Mock(), Mock()

        album_a = Mock()
        album_a.photos = [photo1, photo2]
        album_b = Mock()
        album_b.photos = [photo3]

        mock_albums = Mock()
        mock_albums.albums = {"album-a": album_a, "album-b": album_b}
        mock_albums_class.instance.return_value = mock_albums

        photos = Photos.instance()
        photos.collect_all_photos()

        assert len(photos.photos) == 3
        assert photo1.albumSlug == "album-a"
        assert photo2.albumSlug == "album-a"
        assert photo3.albumSlug == "album-b"

    @patch("fussel.generator.generate.Config")
    def test_sort_photos_by_filename_asc(self, mock_config):
        """sort_photos by filename ascending orders alphabetically."""
        mock_config.instance.return_value.photos_sort_by = "filename"
        mock_config.instance.return_value.photos_sort_order = "asc"

        p1 = Mock(name="p1", date=None)
        p1.name = "zebra.jpg"
        p2 = Mock(name="p2", date=None)
        p2.name = "apple.jpg"
        p3 = Mock(name="p3", date=None)
        p3.name = "mango.jpg"

        photos = Photos.instance()
        photos.photos = [p1, p2, p3]
        photos.sort_photos()

        assert [p.name for p in photos.photos] == ["apple.jpg", "mango.jpg", "zebra.jpg"]

    @patch("fussel.generator.generate.Config")
    def test_sort_photos_by_date_desc_puts_none_last(self, mock_config):
        """sort_photos by date descending: photos without dates go to the end."""
        mock_config.instance.return_value.photos_sort_by = "date"
        mock_config.instance.return_value.photos_sort_order = "desc"

        p_old = Mock(date="2020-01-01T00:00:00")
        p_new = Mock(date="2023-06-15T12:00:00")
        p_no_date = Mock(date=None)

        photos = Photos.instance()
        photos.photos = [p_old, p_no_date, p_new]
        photos.sort_photos()

        # Newest first, no-date at end
        assert photos.photos[0] is p_new
        assert photos.photos[1] is p_old
        assert photos.photos[2] is p_no_date

    @patch("fussel.generator.generate.Config")
    def test_sort_photos_by_date_with_invalid_date(self, mock_config):
        """sort_photos treats photos with unparseable dates as timestamp 0."""
        mock_config.instance.return_value.photos_sort_by = "date"
        mock_config.instance.return_value.photos_sort_order = "asc"

        p_valid = Mock(date="2022-03-10T08:00:00")
        p_bad = Mock(date="not-a-date")

        photos = Photos.instance()
        photos.photos = [p_valid, p_bad]
        photos.sort_photos()

        # Both have dates so neither goes to photos_without_date bucket;
        # p_bad gets timestamp 0 so sorts before p_valid in asc order.
        assert photos.photos[0] is p_bad
        assert photos.photos[1] is p_valid
