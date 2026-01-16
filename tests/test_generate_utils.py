"""
Tests for utility classes in fussel.generator.generate module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fussel.generator.generate import (
    SimpleEncoder,
    Site,
    Person,
    Album,
    Photo,
    PhotoProcessingFailure
)


class TestSimpleEncoder:
    """Tests for SimpleEncoder JSON encoder."""
    
    def test_encode_object_with_json_dump_obj(self):
        """Test encoding an object with json_dump_obj method."""
        class TestObject:
            def json_dump_obj(self):
                return {'custom': 'data'}
        
        encoder = SimpleEncoder()
        result = encoder.default(TestObject())
        assert result == {'custom': 'data'}
    
    def test_encode_object_without_json_dump_obj(self):
        """Test encoding an object without json_dump_obj method."""
        class TestObject:
            def __init__(self):
                self.attr1 = 'value1'
                self.attr2 = 'value2'
        
        encoder = SimpleEncoder()
        result = encoder.default(TestObject())
        assert result == {'attr1': 'value1', 'attr2': 'value2'}
    
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
        with patch('fussel.generator.generate.Config') as mock_config:
            mock_config.instance.return_value.site_name = 'Test Site'
            mock_config.instance.return_value.people_enabled = True
            
            instance1 = Site.instance()
            instance2 = Site.instance()
            
            assert instance1 is instance2
            assert instance1 is Site._instance
    
    def test_site_initialization(self):
        """Test that Site initializes with config values."""
        with patch('fussel.generator.generate.Config') as mock_config:
            mock_config.instance.return_value.site_name = 'My Gallery'
            mock_config.instance.return_value.people_enabled = False
            
            site = Site.instance()
            
            assert site.site_name == 'My Gallery'
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
        person = Person(name='John Doe', slug='john-doe')
        assert person.has_thumbnail() is False
    
    def test_has_thumbnail_true(self):
        """Test has_thumbnail returns True when src is set."""
        person = Person(name='John Doe', slug='john-doe')
        person.src = '/path/to/thumbnail.jpg'
        assert person.has_thumbnail() is True


class TestAlbum:
    """Tests for Album class."""
    
    # Note: Album initialization and add_photo are trivial (attribute assignment and list.append).
    # These are tested indirectly through Albums.process_album_path() which uses them.


class TestPhoto:
    """Tests for Photo class."""
    
    # Note: Photo initialization is just attribute assignment - tested indirectly.
    # Photo.faces is just a list - not business logic worth testing separately.
    
    @patch('fussel.generator.generate.Config')
    @patch('fussel.generator.generate.Image')
    @patch('fussel.generator.generate.shutil')
    @patch('fussel.generator.generate.os.path.exists')
    @patch('fussel.generator.generate.calculate_new_size')
    @patch('fussel.generator.generate.extract_extension')
    @patch('fussel.generator.generate.apply_watermark')
    def test_process_photo_success(self, mock_watermark, mock_extract, mock_calc_size,
                                   mock_exists, mock_shutil, mock_image, mock_config):
        """Test successful photo processing."""
        # Setup mocks
        mock_config.instance.return_value.overwrite = False
        mock_config.instance.return_value.watermark_enabled = False
        mock_config.instance.return_value.people_enabled = False
        mock_config.instance.return_value.exif_transpose = False
        
        mock_exists.return_value = False
        mock_extract.return_value = '.jpg'
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
            external_path='/external',
            photo='/path/to/photo.jpg',
            filename='photo.jpg',
            slug='photo',
            output_path='/output',
            people_q=people_q
        )
        
        assert result is not None
        assert result.name == 'photo.jpg'
        assert result.width == 2000
        assert result.height == 1500
        assert result.slug == 'photo'
    
    @patch('fussel.generator.generate.Config')
    @patch('fussel.generator.generate.Image')
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
                external_path='/external',
                photo='/path/to/bad_photo.jpg',
                filename='bad_photo.jpg',
                slug='bad-photo',
                output_path='/output',
                people_q=people_q
            )
    
    @patch('fussel.generator.generate.Config')
    @patch('fussel.generator.generate.Image')
    @patch('fussel.generator.generate.shutil')
    @patch('fussel.generator.generate.os.path.exists')
    @patch('fussel.generator.generate.calculate_new_size')
    @patch('fussel.generator.generate.extract_extension')
    @patch('fussel.generator.generate.apply_watermark')
    @patch('fussel.generator.generate.ImageOps')
    def test_process_photo_with_watermark_and_exif(self, mock_imageops, mock_watermark, mock_extract,
                                                    mock_calc_size, mock_exists, mock_shutil,
                                                    mock_image, mock_config):
        """Test photo processing with watermark enabled and exif_transpose."""
        mock_config.instance.return_value.overwrite = False
        mock_config.instance.return_value.watermark_enabled = True
        mock_config.instance.return_value.watermark_path = '/path/watermark.png'
        mock_config.instance.return_value.people_enabled = False
        mock_config.instance.return_value.exif_transpose = True
        
        mock_exists.return_value = False
        mock_extract.return_value = '.jpg'
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
        
        # Image.open is called: verify (photo), transpose (photo), size (new_original_photo),
        # thumbnail generation for each size (new_original_photo), watermark (watermark_path)
        # Sizes: (500, 500), (800, 800), (1024, 1024), (1600, 1600) = 4 thumbnail calls
        mock_image.open.side_effect = [
            MagicMock(__enter__=Mock(return_value=mock_img), __exit__=Mock()),  # verify
            MagicMock(__enter__=Mock(return_value=mock_img), __exit__=Mock()),  # transpose
            MagicMock(__enter__=Mock(return_value=mock_img), __exit__=Mock()),  # get size
            MagicMock(__enter__=Mock(return_value=mock_img), __exit__=Mock()),  # thumbnail 500x500
            MagicMock(__enter__=Mock(return_value=mock_img), __exit__=Mock()),  # thumbnail 800x800
            MagicMock(__enter__=Mock(return_value=mock_img), __exit__=Mock()),  # thumbnail 1024x1024
            MagicMock(__enter__=Mock(return_value=mock_img), __exit__=Mock()),  # thumbnail 1600x1600
            MagicMock(__enter__=Mock(return_value=mock_watermark_img), __exit__=Mock()),  # watermark
        ]
        
        mock_shutil.copyfile.return_value = None
        
        from multiprocessing import Queue
        people_q = Queue()
        
        result = Photo.process_photo(
            external_path='/external',
            photo='/path/to/photo.jpg',
            filename='photo.jpg',
            slug='photo',
            output_path='/output',
            people_q=people_q
        )
        
        assert result is not None
        # Verify watermark was applied
        mock_watermark.assert_called_once()
        # Verify exif_transpose was called
        mock_imageops.exif_transpose.assert_called()
    
    @patch('fussel.generator.generate.Config')
    @patch('fussel.generator.generate.Image')
    @patch('fussel.generator.generate.shutil')
    @patch('fussel.generator.generate.os.path.exists')
    @patch('fussel.generator.generate.calculate_new_size')
    @patch('fussel.generator.generate.extract_extension')
    def test_process_photo_overwrite_mode(self, mock_extract, mock_calc_size, mock_exists,
                                          mock_shutil, mock_image, mock_config):
        """Test photo processing in overwrite mode."""
        mock_config.instance.return_value.overwrite = True
        mock_config.instance.return_value.watermark_enabled = False
        mock_config.instance.return_value.people_enabled = False
        mock_config.instance.return_value.exif_transpose = False
        
        mock_exists.return_value = True  # File exists but overwrite=True
        mock_extract.return_value = '.jpg'
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
            external_path='/external',
            photo='/path/to/photo.jpg',
            filename='photo.jpg',
            slug='photo',
            output_path='/output',
            people_q=people_q
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
