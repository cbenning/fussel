"""
Shared pytest fixtures for all tests.
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_config_dict():
    """Sample configuration dictionary for testing."""
    return {
        'gallery': {
            'input_path': '/tmp/test_input',
            'output_path': '/tmp/test_output',
            'people': {
                'enable': True
            },
            'watermark': {
                'enable': True,
                'path': 'web/src/images/fussel-watermark.png',
                'size_ratio': 0.3
            },
            'albums': {
                'recursive': True,
                'recursive_name_pattern': '{parent_album} > {album}'
            },
            'overwrite': False,
            'exif_transpose': False,
            'parallel_tasks': 2
        },
        'site': {
            'title': 'Test Gallery',
            'http_root': '/'
        }
    }


@pytest.fixture
def sample_config_file(temp_dir, sample_config_dict):
    """Create a temporary config.yml file."""
    config_path = os.path.join(temp_dir, 'config.yml')
    os.makedirs(sample_config_dict['gallery']['input_path'], exist_ok=True)
    os.makedirs(sample_config_dict['gallery']['output_path'], exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(sample_config_dict, f)
    
    return config_path


@pytest.fixture
def mock_image_file(temp_dir):
    """Create a mock image file for testing."""
    # Create a simple 100x100 PNG file
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img_path = os.path.join(temp_dir, 'test_image.jpg')
    img.save(img_path)
    return img_path
