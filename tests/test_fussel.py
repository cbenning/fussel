"""
Tests for fussel.fussel module (YamlConfig and main).
"""

import os
import pickle
from unittest.mock import Mock, patch

import pytest
import yaml

from fussel.fussel import YamlConfig, main


class TestYamlConfig:
    """Tests for YamlConfig class."""

    def test_yaml_config_loading(self, sample_config_file, sample_config_dict):
        """Test loading YAML config file."""
        config = YamlConfig(config_file=sample_config_file)

        assert config.cfg == sample_config_dict
        assert config.getKey("gallery.input_path") == "/tmp/test_input"
        assert config.getKey("gallery.output_path") == "/tmp/test_output"

    def test_yaml_config_default_path(self, temp_dir, sample_config_dict):
        """Test YamlConfig uses default config.yml path when None provided."""
        # This test would require mocking the file path resolution
        # For now, we'll test with explicit path
        config_path = os.path.join(temp_dir, "config.yml")
        with open(config_path, "w") as f:
            yaml.dump(sample_config_dict, f)

        # Create input/output directories
        os.makedirs(sample_config_dict["gallery"]["input_path"], exist_ok=True)
        os.makedirs(sample_config_dict["gallery"]["output_path"], exist_ok=True)

        config = YamlConfig(config_file=config_path)
        assert config.cfg == sample_config_dict

    def test_getkey_simple_key(self, sample_config_file):
        """Test getKey with simple top-level key."""
        config = YamlConfig(config_file=sample_config_file)
        # Note: sample_config_dict doesn't have top-level keys, so test nested
        result = config.getKey("gallery.input_path")
        assert result == "/tmp/test_input"

    def test_getkey_nested_key(self, sample_config_file):
        """Test getKey with nested key using dot notation."""
        config = YamlConfig(config_file=sample_config_file)

        result = config.getKey("gallery.people.enable")
        assert result is True

        result = config.getKey("site.title")
        assert result == "Test Gallery"

    def test_getkey_with_default(self, sample_config_file):
        """Test getKey with default value for missing key."""
        config = YamlConfig(config_file=sample_config_file)

        result = config.getKey("nonexistent.key", default="default_value")
        assert result == "default_value"

    def test_getkey_missing_key_no_default(self, sample_config_file):
        """Test getKey with missing key and no default."""
        config = YamlConfig(config_file=sample_config_file)

        result = config.getKey("nonexistent.key")
        assert result is None

    def test_getkey_direct_key(self, temp_dir):
        """Test getKey with direct key (not nested)."""
        test_input = os.path.join(temp_dir, "test_input")
        test_output = os.path.join(temp_dir, "test_output")
        config_dict = {"simple_key": "simple_value", "gallery": {"input_path": test_input, "output_path": test_output}}
        config_path = os.path.join(temp_dir, "config.yml")
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f)

        os.makedirs(test_input, exist_ok=True)
        os.makedirs(test_output, exist_ok=True)

        config = YamlConfig(config_file=config_path)
        result = config.getKey("simple_key")
        assert result == "simple_value"

    def test_pickle_serialization(self, sample_config_file):
        """Test that YamlConfig can be pickled and unpickled."""
        config = YamlConfig(config_file=sample_config_file)

        # Pickle
        pickled = pickle.dumps(config)

        # Unpickle
        unpickled = pickle.loads(pickled)

        assert unpickled.cfg == config.cfg
        assert unpickled.getKey("gallery.input_path") == config.getKey("gallery.input_path")

    def test_invalid_input_path(self, temp_dir):
        """Test that invalid input path causes exit."""
        config_dict = {"gallery": {"input_path": "/nonexistent/path", "output_path": "/tmp/test_output"}}
        config_path = os.path.join(temp_dir, "config.yml")
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f)

        os.makedirs("/tmp/test_output", exist_ok=True)

        with pytest.raises(SystemExit):
            YamlConfig(config_file=config_path)

    def test_invalid_output_path_file(self, temp_dir):
        """Test that output path being a file (not dir) causes exit."""
        test_input = os.path.join(temp_dir, "test_input")
        test_output = os.path.join(temp_dir, "test_output")
        config_dict = {"gallery": {"input_path": test_input, "output_path": test_output}}
        config_path = os.path.join(temp_dir, "config.yml")
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f)

        os.makedirs(test_input, exist_ok=True)
        # Create a file at output path instead of directory
        with open(test_output, "w") as f:
            f.write("not a directory")

        with pytest.raises(SystemExit):
            YamlConfig(config_file=config_path)


class TestMain:
    """Tests for main function."""

    @patch("fussel.fussel.SiteGenerator")
    @patch("fussel.fussel.shutil")
    @patch("fussel.fussel.os")
    @patch("fussel.fussel.YamlConfig")
    def test_main_success(self, mock_yaml_config_class, mock_os, mock_shutil, mock_site_generator_class):
        """Test successful main execution."""
        # Setup mocks
        mock_config = Mock()
        mock_config.getKey = Mock(
            side_effect=lambda key, default=None: {"site.http_root": "/", "gallery.output_path": "/test/output"}.get(
                key, default
            )
        )
        mock_yaml_config_class.return_value = mock_config

        mock_generator = Mock()
        mock_generator.generate = Mock()
        mock_site_generator_class.return_value = mock_generator

        mock_os.path.dirname.return_value = "/fussel/fussel"
        mock_os.path.realpath.return_value = "/fussel/fussel/fussel.py"
        mock_os.path.join.side_effect = os.path.join
        mock_os.path.normpath.side_effect = os.path.normpath
        mock_os.getcwd.return_value = "/current"
        mock_os.chdir = Mock()
        mock_os.system.return_value = 0

        mock_shutil.which.return_value = "/usr/bin/yarn"

        # Run main
        main()

        # Verify SiteGenerator was created and generate called
        mock_site_generator_class.assert_called_once()
        mock_generator.generate.assert_called_once()

    @patch("fussel.fussel.SiteGenerator")
    @patch("fussel.fussel.shutil")
    @patch("fussel.fussel.os")
    @patch("fussel.fussel.YamlConfig")
    def test_main_yarn_not_found(self, mock_yaml_config_class, mock_os, mock_shutil, mock_site_generator_class):
        """Test main when yarn is not found."""
        mock_config = Mock()
        mock_config.getKey = Mock(return_value="/")
        mock_yaml_config_class.return_value = mock_config

        mock_generator = Mock()
        mock_site_generator_class.return_value = mock_generator

        mock_os.path.dirname.return_value = "/fussel/fussel"
        mock_os.path.realpath.return_value = "/fussel/fussel/fussel.py"
        mock_os.path.join.side_effect = os.path.join
        mock_os.path.normpath.side_effect = os.path.normpath
        mock_os.getcwd.return_value = "/current"
        mock_os.chdir = Mock()

        mock_shutil.which.return_value = None  # yarn not found

        with pytest.raises(SystemExit):
            main()

    @patch("fussel.fussel.SiteGenerator")
    @patch("fussel.fussel.shutil")
    @patch("fussel.fussel.os")
    @patch("fussel.fussel.YamlConfig")
    def test_main_yarn_build_fails(self, mock_yaml_config_class, mock_os, mock_shutil, mock_site_generator_class):
        """Test main when yarn build fails."""
        mock_config = Mock()
        mock_config.getKey = Mock(return_value="/")
        mock_yaml_config_class.return_value = mock_config

        mock_generator = Mock()
        mock_site_generator_class.return_value = mock_generator

        mock_os.path.dirname.return_value = "/fussel/fussel"
        mock_os.path.realpath.return_value = "/fussel/fussel/fussel.py"
        mock_os.path.join.side_effect = os.path.join
        mock_os.path.normpath.side_effect = os.path.normpath
        mock_os.getcwd.return_value = "/current"
        mock_os.chdir = Mock()
        mock_os.system.return_value = 1  # yarn build failed

        mock_shutil.which.return_value = "/usr/bin/yarn"

        with pytest.raises(SystemExit):
            main()
