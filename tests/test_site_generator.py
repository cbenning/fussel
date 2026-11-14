"""
Tests for SiteGenerator class in fussel.generator.generate module.
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from fussel.generator.generate import Albums, Config, People, Photos, Site, SiteGenerator


class TestSiteGenerator:
    """Tests for SiteGenerator class."""

    def setup_method(self):
        """Reset singletons before each test."""
        Config._instance = None
        Albums._instance = None
        People._instance = None
        Site._instance = None
        Photos._instance = None

    def test_site_generator_initialization(self, sample_config_dict):
        """Test SiteGenerator initialization."""
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
            }.get(key, default)
        )

        generator = SiteGenerator(mock_yaml_config)

        assert generator.yaml_config == mock_yaml_config
        assert generator.unique_person_slugs == {}
        assert Config.instance() is not None

    @patch("fussel.generator.generate.os.path.dirname")
    @patch("fussel.generator.generate.os.path.realpath")
    @patch("fussel.generator.generate.os.makedirs")
    @patch("fussel.generator.generate.shutil.rmtree")
    @patch("fussel.generator.generate.Albums")
    @patch("fussel.generator.generate.People")
    @patch("fussel.generator.generate.Site")
    @patch("fussel.generator.generate.Config")
    @patch("fussel.generator.generate.json.dumps")
    @patch("builtins.open", new_callable=mock_open)
    @patch("fussel.generator.generate.write_people_manifest")
    def test_generate_full_workflow(
        self,
        mock_write_manifest,
        mock_file,
        mock_json_dumps,
        mock_config_class,
        mock_site_class,
        mock_people_class,
        mock_albums_class,
        mock_rmtree,
        mock_makedirs,
        mock_realpath,
        mock_dirname,
    ):
        """Test full generate workflow with all mocks."""
        # Setup path mocks
        mock_dirname.return_value = "/fussel/fussel/generator"
        mock_realpath.return_value = "/fussel/fussel/generator/generate.py"

        # Setup Config mocks
        mock_config = Mock()
        mock_config.input_photos_dir = "/test/input"
        mock_config.http_root = "/"
        mock_config.overwrite = False
        mock_config.watermark_enabled = False
        mock_config_class.instance.return_value = mock_config

        # Setup singleton mocks
        mock_albums = Mock()
        mock_albums.json_dump_obj.return_value = {"album1": {}}
        mock_albums.albums = {}
        mock_albums_class.instance.return_value = mock_albums
        mock_albums.process_path = Mock()

        mock_people = Mock()
        mock_people.json_dump_obj.return_value = {"person1": {}}
        mock_people_class.instance.return_value = mock_people

        mock_site = Mock()
        mock_site.json_dump_obj.return_value = {"site_name": "Test"}
        mock_site_class.instance.return_value = mock_site

        # Setup JSON dumps
        mock_json_dumps.return_value = "{}"

        # Create generator
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
            }.get(key, default)
        )

        generator = SiteGenerator(mock_yaml_config)
        generator.generate()

        # Verify directories were created
        assert mock_makedirs.called

        # Verify Albums.process_path was called
        mock_albums.process_path.assert_called_once()

        # Verify files were written
        assert mock_file.called
        assert mock_json_dumps.called

    @patch("fussel.generator.generate.write_people_manifest")
    @patch("fussel.generator.generate.os.path.realpath")
    @patch("fussel.generator.generate.os.makedirs")
    @patch("fussel.generator.generate.shutil.rmtree")
    @patch("fussel.generator.generate.Albums")
    @patch("fussel.generator.generate.People")
    @patch("fussel.generator.generate.Site")
    @patch("fussel.generator.generate.Config")
    def test_generate_writes_the_people_manifest_into_the_web_apps_public_folder(
        self,
        mock_config_class,
        mock_site_class,
        mock_people_class,
        mock_albums_class,
        mock_rmtree,
        mock_makedirs,
        mock_realpath,
        mock_write_manifest,
    ):
        """people.json goes where Vite copies files verbatim to the site root, with the configured settings."""
        mock_realpath.return_value = "/fussel/fussel/generator/generate.py"

        mock_config = Mock()
        mock_config.input_photos_dir = "/test/input"
        mock_config.http_root = "/"
        mock_config.overwrite = False
        mock_config.watermark_enabled = False
        mock_config.people_enabled = True
        mock_config.people_manifest_photos = 9
        mock_config_class.instance.return_value = mock_config

        mock_albums = Mock()
        mock_albums.albums = {}
        mock_albums_class.instance.return_value = mock_albums

        people = {"Ada": Mock()}
        mock_people = Mock()
        mock_people.people = people
        mock_people_class.instance.return_value = mock_people

        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(side_effect=lambda key, default=None: default)

        with (
            patch("builtins.open", mock_open()),
            patch("fussel.generator.generate.json.dumps", return_value="{}"),
        ):
            SiteGenerator(mock_yaml_config).generate()

        mock_write_manifest.assert_called_once_with("/fussel/fussel/web/public", people, True, 9)

    @patch("fussel.generator.generate.os.path.dirname")
    @patch("fussel.generator.generate.os.path.realpath")
    @patch("fussel.generator.generate.os.makedirs")
    @patch("fussel.generator.generate.shutil.rmtree")
    @patch("fussel.generator.generate.Albums")
    @patch("fussel.generator.generate.Config")
    def test_generate_with_overwrite(
        self, mock_config_class, mock_albums_class, mock_rmtree, mock_makedirs, mock_realpath, mock_dirname
    ):
        """Test generate with overwrite enabled."""
        mock_dirname.return_value = "/fussel/fussel/generator"
        mock_realpath.return_value = "/fussel/fussel/generator/generate.py"

        mock_config = Mock()
        mock_config.input_photos_dir = "/test/input"
        mock_config.http_root = "/"
        mock_config.overwrite = True
        mock_config.watermark_enabled = False
        mock_config_class.instance.return_value = mock_config

        mock_albums = Mock()
        mock_albums.albums = {}
        mock_albums.process_path = Mock()
        mock_albums_class.instance.return_value = mock_albums

        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(
            side_effect=lambda key, default=None: {
                "gallery.input_path": "/test/input",
                "gallery.output_path": "/test/output",
            }.get(key, default)
        )

        generator = SiteGenerator(mock_yaml_config)

        with (
            patch("builtins.open", mock_open()),
            patch("fussel.generator.generate.json.dumps", return_value="{}"),
            patch("fussel.generator.generate.People"),
            patch("fussel.generator.generate.Site"),
            patch("fussel.generator.generate.write_people_manifest"),
        ):
            generator.generate()

        # Verify rmtree was called for overwrite
        assert mock_rmtree.called


class TestWatermarkValidation:
    @patch("fussel.generator.generate.Albums")
    @patch("fussel.generator.generate.Config")
    def test_generate_exits_early_when_watermark_image_is_missing(self, mock_config_class, mock_albums_class, capsys):
        mock_config = Mock()
        mock_config.watermark_enabled = True
        mock_config.watermark_path = "/nope/missing.png"
        mock_config_class.instance.return_value = mock_config
        generator = SiteGenerator.__new__(SiteGenerator)
        generator.yaml_config = Mock()

        with pytest.raises(SystemExit) as exc:
            generator.generate()

        assert exc.value.code == 1
        assert "Watermark image not found" in capsys.readouterr().out
        mock_albums_class.instance.assert_not_called()
