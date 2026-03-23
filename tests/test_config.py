"""
Tests for fussel.generator.config module.
"""

from unittest.mock import Mock, patch

import pytest

from fussel.generator.config import DEFAULT_PHOTO_SIZES, DEFAULT_WATERMARK_PATH, DEFAULT_WATERMARK_SIZE_RATIO, Config


class TestConfigSingleton:
    """Tests for Config singleton pattern."""

    def test_cannot_instantiate_directly(self):
        """Test that Config cannot be instantiated directly."""
        with pytest.raises(RuntimeError, match="Call instance\\(\\) instead"):
            Config()

    def test_instance_returns_singleton(self):
        """Test that instance() returns the same object."""
        # Reset singleton for clean test
        Config._instance = None

        instance1 = Config.instance()
        instance2 = Config.instance()

        assert instance1 is instance2
        assert instance1 is Config._instance

    def test_init_creates_instance(self):
        """Test that init() creates and populates an instance."""
        # Reset singleton
        Config._instance = None

        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
            }.get(key, default)
        )

        Config.init(mock_yaml_config)

        instance = Config.instance()
        assert instance is not None
        assert instance.input_photos_dir == "/test/input"


class TestConfigInitialization:
    """Tests for Config initialization and value extraction."""

    def setup_method(self):
        """Reset Config singleton before each test."""
        Config._instance = None

    def test_init_with_full_config(self):
        """Test initialization with all config values provided."""
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
                "gallery.people.enable": True,
                "gallery.watermark.enable": True,
                "gallery.watermark.path": "/custom/watermark.png",
                "gallery.watermark.size_ratio": 0.5,
                "gallery.albums.recursive": False,
                "gallery.albums.recursive_name_pattern": "{parent} - {album}",
                "gallery.overwrite": True,
                "gallery.parallel_tasks": 4,
                "gallery.exif_transpose": True,
                "site.http_root": "/gallery/",
                "site.title": "My Gallery",
            }.get(key, default)
        )

        Config.init(mock_yaml_config)
        instance = Config.instance()

        assert instance.input_photos_dir == "/test/input"
        assert instance.output_photos_path == "/test/output"
        assert instance.people_enabled is True
        assert instance.watermark_enabled is True
        assert instance.watermark_path == "/custom/watermark.png"
        assert instance.watermark_ratio == 0.5
        assert instance.recursive_albums is False
        assert instance.recursive_albums_name_pattern == "{parent} - {album}"
        assert instance.overwrite is True
        assert instance.parallel_tasks == 4
        assert instance.exif_transpose is True
        assert instance.http_root == "/gallery/"
        assert instance.site_name == "My Gallery"

    def test_init_with_defaults(self):
        """Test initialization with missing values uses defaults."""
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
            }.get(key, default)
        )

        Config.init(mock_yaml_config)
        instance = Config.instance()

        assert instance.people_enabled is True  # Default
        assert instance.watermark_enabled is True  # Default
        assert instance.watermark_path == DEFAULT_WATERMARK_PATH  # Default
        assert instance.watermark_ratio == DEFAULT_WATERMARK_SIZE_RATIO  # Default
        assert instance.recursive_albums is True  # Default
        assert instance.overwrite is False  # Default
        assert instance.exif_transpose is False  # Default
        assert instance.http_root == "/"  # Default

    def test_type_conversions(self):
        """Test that config values are properly type-converted."""
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
                "gallery.people.enable": "true",  # String that should become bool
                "gallery.watermark.size_ratio": "0.4",  # String that should become float
                "gallery.parallel_tasks": "8",  # String that should become int
            }.get(key, default)
        )

        Config.init(mock_yaml_config)
        instance = Config.instance()

        # Note: bool('true') is True, bool('false') is also True (non-empty string)
        # So the conversion depends on the actual value
        assert isinstance(instance.watermark_ratio, float)
        assert isinstance(instance.parallel_tasks, int)

    @patch("fussel.generator.config.os.cpu_count")
    def test_parallel_tasks_default_calculation(self, mock_cpu_count):
        """Test that parallel_tasks defaults to cpu_count/2."""
        mock_cpu_count.return_value = 8

        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
            }.get(key, default)
        )

        Config.init(mock_yaml_config)
        instance = Config.instance()

        assert instance.parallel_tasks == 4  # 8 / 2

    @patch("fussel.generator.config.os.cpu_count")
    def test_parallel_tasks_minimum_one(self, mock_cpu_count):
        """Test that parallel_tasks is at least 1."""
        mock_cpu_count.return_value = 1  # cpu_count/2 would be 0.5

        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
            }.get(key, default)
        )

        Config.init(mock_yaml_config)
        instance = Config.instance()

        assert instance.parallel_tasks >= 1

    def test_supported_extensions(self):
        """Test that supported_extensions is set correctly."""
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
            }.get(key, default)
        )

        Config.init(mock_yaml_config)
        instance = Config.instance()

        assert instance.supported_extensions == (".jpg", ".jpeg", ".gif", ".png")

    def test_photo_sizes_default(self):
        """Test that photo_sizes defaults to DEFAULT_PHOTO_SIZES."""
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
            }.get(key, default)
        )

        Config.init(mock_yaml_config)
        instance = Config.instance()

        assert instance.photo_sizes == DEFAULT_PHOTO_SIZES

    def test_photo_sizes_custom(self):
        """Test that photo_sizes can be overridden via config."""
        custom_sizes = [[320, 320], [640, 640]]
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
                "gallery.photo_sizes": custom_sizes,
            }.get(key, default)
        )

        Config.init(mock_yaml_config)
        instance = Config.instance()

        assert instance.photo_sizes == [(320, 320), (640, 640)]
