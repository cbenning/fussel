"""
Tests for SiteGenerator class in fussel.generator.generate module.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from fussel.generator.generate import SiteGenerator, Config, Albums, People, Site


class TestSiteGenerator:
    """Tests for SiteGenerator class."""
    
    def setup_method(self):
        """Reset singletons before each test."""
        Config._instance = None
        Albums._instance = None
        People._instance = None
        Site._instance = None
    
    def test_site_generator_initialization(self, sample_config_dict):
        """Test SiteGenerator initialization."""
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(side_effect=lambda key, default=None: {
            'gallery.input_path': '/test/input',
            'gallery.output_path': '/test/output',
        }.get(key, default))
        
        generator = SiteGenerator(mock_yaml_config)
        
        assert generator.yaml_config == mock_yaml_config
        assert generator.unique_person_slugs == {}
        assert Config.instance() is not None
    
    @patch('fussel.generator.generate.os.path.dirname')
    @patch('fussel.generator.generate.os.path.realpath')
    @patch('fussel.generator.generate.os.makedirs')
    @patch('fussel.generator.generate.shutil.rmtree')
    @patch('fussel.generator.generate.Albums')
    @patch('fussel.generator.generate.People')
    @patch('fussel.generator.generate.Site')
    @patch('fussel.generator.generate.Config')
    @patch('fussel.generator.generate.json.dumps')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_full_workflow(self, mock_file, mock_json_dumps, mock_config_class,
                                     mock_site_class, mock_people_class, mock_albums_class,
                                     mock_rmtree, mock_makedirs, mock_realpath, mock_dirname):
        """Test full generate workflow with all mocks."""
        # Setup path mocks
        mock_dirname.return_value = '/fussel/fussel/generator'
        mock_realpath.return_value = '/fussel/fussel/generator/generate.py'
        
        # Setup Config mocks
        mock_config = Mock()
        mock_config.input_photos_dir = '/test/input'
        mock_config.http_root = '/'
        mock_config.overwrite = False
        mock_config_class.instance.return_value = mock_config
        
        # Setup singleton mocks
        mock_albums = Mock()
        mock_albums.json_dump_obj.return_value = {'album1': {}}
        mock_albums_class.instance.return_value = mock_albums
        mock_albums.process_path = Mock()
        
        mock_people = Mock()
        mock_people.json_dump_obj.return_value = {'person1': {}}
        mock_people_class.instance.return_value = mock_people
        
        mock_site = Mock()
        mock_site.json_dump_obj.return_value = {'site_name': 'Test'}
        mock_site_class.instance.return_value = mock_site
        
        # Setup JSON dumps
        mock_json_dumps.return_value = '{}'
        
        # Create generator
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(side_effect=lambda key, default=None: {
            'gallery.input_path': '/test/input',
            'gallery.output_path': '/test/output',
        }.get(key, default))
        
        generator = SiteGenerator(mock_yaml_config)
        generator.generate()
        
        # Verify directories were created
        assert mock_makedirs.called
        
        # Verify Albums.process_path was called
        mock_albums.process_path.assert_called_once()
        
        # Verify files were written
        assert mock_file.called
        assert mock_json_dumps.called
    
    @patch('fussel.generator.generate.os.path.dirname')
    @patch('fussel.generator.generate.os.path.realpath')
    @patch('fussel.generator.generate.os.makedirs')
    @patch('fussel.generator.generate.shutil.rmtree')
    @patch('fussel.generator.generate.Albums')
    @patch('fussel.generator.generate.Config')
    def test_generate_with_overwrite(self, mock_config_class, mock_albums_class,
                                     mock_rmtree, mock_makedirs, mock_realpath, mock_dirname):
        """Test generate with overwrite enabled."""
        mock_dirname.return_value = '/fussel/fussel/generator'
        mock_realpath.return_value = '/fussel/fussel/generator/generate.py'
        
        mock_config = Mock()
        mock_config.input_photos_dir = '/test/input'
        mock_config.http_root = '/'
        mock_config.overwrite = True
        mock_config_class.instance.return_value = mock_config
        
        mock_albums = Mock()
        mock_albums.process_path = Mock()
        mock_albums_class.instance.return_value = mock_albums
        
        mock_yaml_config = Mock()
        mock_yaml_config.getKey = Mock(side_effect=lambda key, default=None: {
            'gallery.input_path': '/test/input',
            'gallery.output_path': '/test/output',
        }.get(key, default))
        
        generator = SiteGenerator(mock_yaml_config)
        
        with patch('builtins.open', mock_open()), \
             patch('fussel.generator.generate.json.dumps', return_value='{}'), \
             patch('fussel.generator.generate.People'), \
             patch('fussel.generator.generate.Site'):
            generator.generate()
        
        # Verify rmtree was called for overwrite
        assert mock_rmtree.called
