"""
Tests for _process_photo and _proces_photo_init functions.
"""

from unittest.mock import Mock, patch

import pytest

from fussel.generator.generate import Photo, PhotoProcessingFailure, _init_worker, _process_photo


class TestProcessPhoto:
    """Tests for _process_photo wrapper function."""

    @patch("fussel.generator.generate.Photo.process_photo")
    def test_process_photo_success(self, mock_process_photo):
        """Test _process_photo with successful processing."""
        mock_photo = Mock(spec=Photo)
        mock_process_photo.return_value = mock_photo

        result = _process_photo(("/external", "/path/to/photo.jpg", "photo.jpg", "photo", "/output"))

        assert result == ("/path/to/photo.jpg", mock_photo, [])
        mock_process_photo.assert_called_once()

    @patch("fussel.generator.generate.Photo.process_photo")
    def test_process_photo_returns_face_jobs(self, mock_process_photo):
        """Face jobs queued by process_photo are returned with the result."""

        def fake_process(external_path, photo, filename, slug, output_path, face_jobs):
            face_jobs.append((photo, "/output/largest.jpg", output_path, external_path))
            return Mock(spec=Photo)

        mock_process_photo.side_effect = fake_process

        _, _, face_jobs = _process_photo(("/external", "/path/to/photo.jpg", "photo.jpg", "photo", "/output"))

        assert face_jobs == [("/path/to/photo.jpg", "/output/largest.jpg", "/output", "/external")]

    @patch("fussel.generator.generate.Photo.process_photo")
    def test_process_photo_failure(self, mock_process_photo):
        """Test _process_photo with PhotoProcessingFailure."""
        mock_process_photo.side_effect = PhotoProcessingFailure(message="Test error")

        result = _process_photo(("/external", "/path/to/bad_photo.jpg", "bad_photo.jpg", "bad-photo", "/output"))

        assert result == ("/path/to/bad_photo.jpg", None, [])

    @patch("fussel.generator.generate.Photo.process_photo")
    def test_process_photo_unexpected_exception(self, mock_process_photo):
        """Test _process_photo with unexpected exception (should propagate)."""
        mock_process_photo.side_effect = ValueError("Unexpected error")

        with pytest.raises(ValueError):
            _process_photo(("/external", "/path/to/photo.jpg", "photo.jpg", "photo", "/output"))


class TestInitWorker:
    """Tests for _init_worker function."""

    def test_init_worker_initializes_config(self):
        mock_yaml_config = Mock()

        with patch("fussel.generator.generate.Config") as mock_config_class:
            _init_worker(mock_yaml_config)

            mock_config_class.init.assert_called_once_with(mock_yaml_config)
