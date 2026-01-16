"""
Tests for _process_photo and _proces_photo_init functions.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fussel.generator.generate import _process_photo, _proces_photo_init, PhotoProcessingFailure, Photo, Config


class TestProcessPhoto:
    """Tests for _process_photo wrapper function."""
    
    @patch('fussel.generator.generate.Photo.process_photo')
    def test_process_photo_success(self, mock_process_photo):
        """Test _process_photo with successful processing."""
        mock_photo = Mock(spec=Photo)
        mock_process_photo.return_value = mock_photo
        
        # Set up the people_q attribute
        mock_queue = Mock()
        _process_photo.people_q = mock_queue
        
        result = _process_photo((
            '/external',
            '/path/to/photo.jpg',
            'photo.jpg',
            'photo',
            '/output'
        ))
        
        assert result == ('/path/to/photo.jpg', mock_photo)
        mock_process_photo.assert_called_once()
    
    @patch('fussel.generator.generate.Photo.process_photo')
    def test_process_photo_failure(self, mock_process_photo):
        """Test _process_photo with PhotoProcessingFailure."""
        mock_process_photo.side_effect = PhotoProcessingFailure(message="Test error")
        
        mock_queue = Mock()
        _process_photo.people_q = mock_queue
        
        result = _process_photo((
            '/external',
            '/path/to/bad_photo.jpg',
            'bad_photo.jpg',
            'bad-photo',
            '/output'
        ))
        
        assert result == ('/path/to/bad_photo.jpg', None)
    
    @patch('fussel.generator.generate.Photo.process_photo')
    def test_process_photo_unexpected_exception(self, mock_process_photo):
        """Test _process_photo with unexpected exception (should propagate)."""
        mock_process_photo.side_effect = ValueError("Unexpected error")
        
        mock_queue = Mock()
        _process_photo.people_q = mock_queue
        
        with pytest.raises(ValueError):
            _process_photo((
                '/external',
                '/path/to/photo.jpg',
                'photo.jpg',
                'photo',
                '/output'
            ))


class TestProcessPhotoInit:
    """Tests for _proces_photo_init function."""
    
    def test_proces_photo_init(self):
        """Test _proces_photo_init sets up worker process."""
        mock_queue = Mock()
        mock_yaml_config = Mock()
        
        with patch('fussel.generator.generate.Config') as mock_config_class:
            _proces_photo_init(mock_queue, mock_yaml_config)
            
            # Verify people_q is set
            assert _process_photo.people_q == mock_queue
            
            # Verify Config.init was called
            mock_config_class.init.assert_called_once_with(mock_yaml_config)
