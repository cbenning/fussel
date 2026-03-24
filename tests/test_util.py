"""
Tests for fussel.generator.util module.
"""

import os
import threading
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from fussel.generator.util import (
    apply_watermark,
    calculate_face_crop_dimensions,
    calculate_new_size,
    extract_extension,
    find_unique_slug,
    increase_h,
    increase_size,
    increase_w,
    is_supported_album,
    is_supported_photo,
    pick_album_thumbnail,
)


class TestIsSupportedAlbum:
    """Tests for is_supported_album function."""

    def test_valid_directory(self, temp_dir):
        """Test that a valid directory is supported."""
        test_dir = os.path.join(temp_dir, "valid_album")
        os.makedirs(test_dir)
        assert is_supported_album(test_dir) is True

    def test_hidden_directory(self, temp_dir):
        """Test that hidden directories (starting with .) are not supported."""
        test_dir = os.path.join(temp_dir, ".hidden")
        os.makedirs(test_dir)
        assert is_supported_album(test_dir) is False

    def test_file_not_directory(self, temp_dir):
        """Test that files are not supported."""
        test_file = os.path.join(temp_dir, "not_a_dir.txt")
        with open(test_file, "w") as f:
            f.write("test")
        assert is_supported_album(test_file) is False

    def test_nonexistent_path(self):
        """Test that nonexistent paths are not supported."""
        assert is_supported_album("/nonexistent/path") is False


class TestExtractExtension:
    """Tests for extract_extension function."""

    @pytest.mark.parametrize(
        "path,expected",
        [
            ("photo.jpg", ".jpg"),
            ("photo.JPG", ".jpg"),
            ("photo.PNG", ".png"),
            ("photo.jpeg", ".jpeg"),
            ("photo.gif", ".gif"),
            ("path/to/photo.jpg", ".jpg"),
            ("photo", ""),
            ("photo.", "."),
        ],
    )
    def test_extract_extension(self, path, expected):
        """Test extension extraction for various paths."""
        assert extract_extension(path) == expected


class TestIsSupportedPhoto:
    """Tests for is_supported_photo function."""

    @patch("fussel.generator.util.Config")
    def test_supported_extensions(self, mock_config_class):
        """Test that supported extensions return True."""
        mock_config = Mock()
        mock_config.supported_extensions = (".jpg", ".jpeg", ".gif", ".png")
        mock_config_class.instance.return_value = mock_config

        assert is_supported_photo("photo.jpg") is True
        assert is_supported_photo("photo.jpeg") is True
        assert is_supported_photo("photo.png") is True
        assert is_supported_photo("photo.gif") is True

    @patch("fussel.generator.util.Config")
    def test_unsupported_extensions(self, mock_config_class):
        """Test that unsupported extensions return False."""
        mock_config = Mock()
        mock_config.supported_extensions = (".jpg", ".jpeg", ".gif", ".png")
        mock_config_class.instance.return_value = mock_config

        assert is_supported_photo("photo.txt") is False
        assert is_supported_photo("photo.pdf") is False
        assert is_supported_photo("photo") is False


class TestFindUniqueSlug:
    """Tests for find_unique_slug function."""

    def test_unique_slug_no_collision(self):
        """Test finding a unique slug when no collision exists."""
        slugs = set()
        lock = threading.Lock()
        name = "Test Album"

        result = find_unique_slug(slugs, lock, name)
        assert result == "test-album"
        # Regression test: slug should be added to set and lock should be released
        assert "test-album" in slugs
        # Verify lock is released (can acquire it again without blocking)
        acquired = lock.acquire(blocking=False)
        assert acquired is True, "Lock should be released after function returns"
        lock.release()

    def test_unique_slug_with_collision(self):
        """Test finding a unique slug when collision exists."""
        slugs = {"test-album"}
        lock = threading.Lock()
        name = "Test Album"

        result = find_unique_slug(slugs, lock, name)
        assert result == "test-album-1"
        assert "test-album-1" in slugs

    def test_unique_slug_multiple_collisions(self):
        """Test finding a unique slug with multiple collisions."""
        slugs = {"test-album", "test-album-1", "test-album-2"}
        lock = threading.Lock()
        name = "Test Album"

        result = find_unique_slug(slugs, lock, name)
        assert result == "test-album-3"
        assert "test-album-3" in slugs

    def test_slug_with_special_characters(self):
        """Test slug generation with special characters."""
        slugs = set()
        lock = threading.Lock()
        name = "My Album & Photos!"

        result = find_unique_slug(slugs, lock, name)
        assert result == "my-album-photos"
        assert "my-album-photos" in slugs


class TestCalculateNewSize:
    """Tests for calculate_new_size function."""

    def test_no_scaling_needed(self):
        """Test that size is returned unchanged when input is smaller."""
        input_size = (400, 300)
        desired_size = (500, 500)
        result = calculate_new_size(input_size, desired_size)
        assert result == input_size

    def test_scaling_down(self):
        """Test scaling down a larger image."""
        input_size = (2000, 1500)
        desired_size = (1000, 1000)
        result = calculate_new_size(input_size, desired_size)
        assert result[0] == 1000
        assert result[1] == 750  # Maintains aspect ratio

    def test_exact_match(self):
        """Test when input size matches desired size."""
        input_size = (500, 500)
        desired_size = (500, 500)
        result = calculate_new_size(input_size, desired_size)
        assert result == input_size

    def test_wide_image(self):
        """Test scaling a wide image."""
        input_size = (3000, 1000)
        desired_size = (1500, 1500)
        result = calculate_new_size(input_size, desired_size)
        assert result[0] == 1500
        assert result[1] == 500

    def test_calculate_new_size_zero_width(self):
        """Test calculate_new_size with zero width (edge case)."""
        input_size = (0, 1000)
        desired_size = (500, 500)
        # Should handle gracefully - will return input_size since 0 <= 500
        result = calculate_new_size(input_size, desired_size)
        assert result == input_size

    def test_calculate_new_size_tall_image(self):
        """Test scaling a tall image."""
        input_size = (1000, 3000)
        desired_size = (500, 500)
        result = calculate_new_size(input_size, desired_size)
        assert result[0] == 500
        assert result[1] == 1500  # Maintains aspect ratio


class TestIncreaseW:
    """Tests for increase_w function."""

    def test_increase_width_basic(self):
        """Test basic width increase."""
        left, top, right, bottom = 10, 10, 20, 30
        w, h = 100, 100
        target_ratio = 1.0

        result = increase_w(left, top, right, bottom, w, h, target_ratio)
        assert result[0] < left  # Left should decrease
        assert result[2] > right  # Right should increase
        assert result[1] == top  # Top unchanged
        assert result[3] == bottom  # Bottom unchanged

    def test_no_increase_when_ratio_met(self):
        """Test no increase when target ratio is already met."""
        left, top, right, bottom = 10, 10, 30, 20
        w, h = 100, 100
        target_ratio = 0.5  # Current ratio is already higher

        result = increase_w(left, top, right, bottom, w, h, target_ratio)
        assert result == (left, top, right, bottom)


class TestIncreaseH:
    """Tests for increase_h function."""

    def test_increase_height_basic(self):
        """Test basic height increase."""
        left, top, right, bottom = 10, 10, 20, 20
        w, h = 100, 100
        target_ratio = 0.5  # Need to decrease ratio (increase height)

        result = increase_h(left, top, right, bottom, w, h, target_ratio)
        assert result[1] < top  # Top should decrease
        assert result[3] > bottom  # Bottom should increase
        assert result[0] == left  # Left unchanged
        assert result[2] == right  # Right unchanged

    def test_increase_h_calculates_height_correctly(self):
        """Regression test: increase_h should recalculate f_h (not overwrite f_w) in loop.

        Bug: Original code had 'f_w = f_b - f_t' which overwrote width with height,
        causing ratio to increase instead of decrease, making loop exit condition never
        trigger properly. This caused excessive height expansion.
        """
        left, top, right, bottom = 10, 10, 20, 30  # width=10, height=20, ratio=0.5
        w, h = 100, 100
        target_ratio = 0.3  # Need to decrease ratio (increase height)

        result = increase_h(left, top, right, bottom, w, h, target_ratio)
        # Height should increase (top decreases, bottom increases)
        assert result[1] < top  # Top decreased
        assert result[3] > bottom  # Bottom increased
        # Width should remain unchanged
        assert result[0] == left
        assert result[2] == right

        # Verify the ratio actually decreased (not increased like the bug would cause)
        final_width = result[2] - result[0]
        final_height = result[3] - result[1]
        final_ratio = (final_width + 1) / (final_height + 1)
        assert final_ratio < 0.55, "Ratio should decrease, not increase"


class TestIncreaseSize:
    """Tests for increase_size function."""

    def test_increase_size_basic(self):
        """Test basic size increase in all directions."""
        left, top, right, bottom = 40, 40, 60, 60
        w, h = 100, 100
        target_ratio = 1.5

        result = increase_size(left, top, right, bottom, w, h, target_ratio)
        assert result[0] < left  # Left decreased
        assert result[1] < top  # Top decreased
        assert result[2] > right  # Right increased
        assert result[3] > bottom  # Bottom increased


class TestCalculateFaceCropDimensions:
    """Tests for calculate_face_crop_dimensions function."""

    def test_basic_face_crop(self):
        """Test basic face crop calculation."""
        input_size = (1000, 1000)
        face_size = (0.2, 0.2)  # 20% of image
        face_position = (0.5, 0.5)  # Center

        result = calculate_face_crop_dimensions(input_size, face_size, face_position)
        left, top, right, bottom = result

        assert left >= 0
        assert top >= 0
        assert right <= input_size[0]
        assert bottom <= input_size[1]
        assert right > left
        assert bottom > top

    def test_face_near_edge(self):
        """Test face crop when face is near image edge."""
        input_size = (1000, 1000)
        face_size = (0.1, 0.1)
        face_position = (0.1, 0.1)  # Near top-left corner

        result = calculate_face_crop_dimensions(input_size, face_size, face_position)
        left, top, right, bottom = result

        assert left >= 0
        assert top >= 0
        assert right <= input_size[0]
        assert bottom <= input_size[1]

    def test_face_crop_very_small_face(self):
        """Test face crop with very small face region."""
        input_size = (1000, 1000)
        face_size = (0.05, 0.05)  # Very small face
        face_position = (0.5, 0.5)

        result = calculate_face_crop_dimensions(input_size, face_size, face_position)
        left, top, right, bottom = result

        # Should still produce valid coordinates
        assert right > left
        assert bottom > top

    def test_face_crop_at_corner(self):
        """Test face crop when face is at image corner."""
        input_size = (1000, 1000)
        face_size = (0.1, 0.1)
        face_position = (0.0, 0.0)  # Top-left corner

        result = calculate_face_crop_dimensions(input_size, face_size, face_position)
        left, top, right, bottom = result

        # Should handle edge case gracefully
        assert left >= 0
        assert top >= 0

    def test_face_crop_ratio_calculation_correct(self):
        """Regression test: face crop should calculate ratio with correct operator precedence."""
        input_size = (1000, 1000)
        face_size = (0.2, 0.3)  # Taller than wide (height > width)
        face_position = (0.5, 0.5)  # Center

        result = calculate_face_crop_dimensions(input_size, face_size, face_position)
        left, top, right, bottom = result

        # Since face is taller than wide, ratio should be < 4/3, so should expand horizontally
        # Verify valid coordinates
        assert right > left
        assert bottom > top
        assert left >= 0
        assert top >= 0
        assert right <= input_size[0]
        assert bottom <= input_size[1]

        # Verify the ratio calculation works correctly
        calculated_ratio = (right - left + 1) / (bottom - top + 1)
        # Should be close to target ratio (4/3) after expansion
        assert 0.8 < calculated_ratio < 2.0  # Reasonable range after processing


class TestApplyWatermark:
    """Tests for apply_watermark function."""

    def test_apply_watermark(self, temp_dir, mock_image_file):
        """Test watermark application."""
        watermark = Image.new("RGBA", (100, 50), color=(255, 255, 255, 128))
        watermark_ratio = 0.2

        # Copy the mock image to a new path for watermarking
        watermarked_path = os.path.join(temp_dir, "watermarked.jpg")
        import shutil

        shutil.copy(mock_image_file, watermarked_path)

        apply_watermark(watermarked_path, watermark, watermark_ratio)

        # Verify file was modified
        assert os.path.exists(watermarked_path)
        with Image.open(watermarked_path) as img:
            assert img.size == (100, 100)  # Original size maintained


class TestPickAlbumThumbnail:
    """Tests for pick_album_thumbnail function."""

    def test_pick_thumbnail_with_photos(self):
        """Test picking thumbnail when photos exist."""
        mock_photo = Mock()
        mock_photo.thumb = "/path/to/thumb.jpg"
        album_photos = [mock_photo]

        result = pick_album_thumbnail(album_photos)
        assert result == "/path/to/thumb.jpg"

    def test_pick_thumbnail_empty_list(self):
        """Test picking thumbnail when no photos exist."""
        album_photos = []
        result = pick_album_thumbnail(album_photos)
        assert result == ""

    def test_pick_thumbnail_first_photo(self):
        """Test that first photo's thumbnail is selected."""
        mock_photo1 = Mock()
        mock_photo1.thumb = "/path/to/thumb1.jpg"
        mock_photo2 = Mock()
        mock_photo2.thumb = "/path/to/thumb2.jpg"
        album_photos = [mock_photo1, mock_photo2]

        result = pick_album_thumbnail(album_photos)
        assert result == "/path/to/thumb1.jpg"

    def test_pick_album_thumbnail_none_thumb(self):
        """Test picking thumbnail when first photo has no thumb."""
        mock_photo = Mock()
        mock_photo.thumb = None
        album_photos = [mock_photo]

        result = pick_album_thumbnail(album_photos)
        assert result is None
