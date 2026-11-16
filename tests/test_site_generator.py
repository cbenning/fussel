"""
Tests for SiteGenerator class in fussel.generator.generate module.
"""

import json
from unittest.mock import Mock, patch

import pytest
import yaml

from fussel.fussel import YamlConfig
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

    def _generate(self, tmp_path, overwrite=False):
        """Run a real generate() over one tiny album, returning the output dir."""
        from PIL import Image

        album = tmp_path / "photos" / "Trip"
        album.mkdir(parents=True)
        Image.new("RGB", (200, 100), "red").save(album / "one.jpg")
        output = tmp_path / "site"
        config_path = tmp_path / "config.yml"
        config_path.write_text(
            yaml.dump(
                {
                    "gallery": {
                        "input_path": str(tmp_path / "photos"),
                        "output_path": str(output),
                        "overwrite": overwrite,
                        "parallel_tasks": 1,
                        "people": {"enable": False},
                        "watermark": {"enable": False},
                    },
                    "site": {"title": "Test Gallery", "http_root": "/"},
                }
            )
        )
        SiteGenerator(YamlConfig(str(config_path))).generate()
        return output

    def test_generate_writes_json_data_into_output(self, tmp_path):
        """Gallery data lands as JSON under <output>/static/_gallery/data."""
        output = self._generate(tmp_path)

        data_dir = output / "static" / "_gallery" / "data"
        site = json.loads((data_dir / "site.json").read_text())
        albums = json.loads((data_dir / "albums.json").read_text())
        assert site["site_name"] == "Test Gallery"
        assert list(albums) == ["trip"]
        assert albums["trip"]["name"] == "Trip"
        assert len(json.loads((data_dir / "photos.json").read_text())) == 1
        assert json.loads((data_dir / "people.json").read_text()) == {}
        assert (output / "static" / "_gallery" / "albums" / "trip").is_dir()

    def test_generate_with_overwrite_only_clears_gallery_files(self, tmp_path):
        """Overwrite wipes stale generated files but leaves the rest of the output dir alone."""
        output = tmp_path / "site"
        stale = output / "static" / "_gallery" / "albums" / "stale.txt"
        stale.parent.mkdir(parents=True)
        stale.write_text("old")
        keep = output / "keep.txt"
        keep.write_text("mine")

        self._generate(tmp_path, overwrite=True)

        assert not stale.exists()
        assert keep.read_text() == "mine"


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
