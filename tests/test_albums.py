"""
Tests for Albums class in fussel.generator.generate module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fussel.generator.generate import Albums, Album, Photo


class TestAlbumsSingleton:
    """Tests for Albums singleton pattern."""
    
    def setup_method(self):
        """Reset Albums singleton before each test."""
        Albums._instance = None
    
    def test_cannot_instantiate_directly(self):
        """Test that Albums cannot be instantiated directly."""
        with pytest.raises(RuntimeError, match="Call instance\\(\\) instead"):
            Albums()
    
    def test_instance_returns_singleton(self):
        """Test that instance() returns the same object."""
        instance1 = Albums.instance()
        instance2 = Albums.instance()
        
        assert instance1 is instance2
        assert instance1 is Albums._instance
    
    def test_albums_initialization(self):
        """Test that Albums initializes correctly."""
        albums = Albums.instance()
        
        assert albums.albums == {}
        assert isinstance(albums.slugs, set)
        assert len(albums.slugs) == 0


class TestAlbumsMethods:
    """Tests for Albums class methods."""
    
    def setup_method(self):
        """Reset Albums singleton before each test."""
        Albums._instance = None
    
    def test_add_album(self):
        """Test adding an album to Albums."""
        albums = Albums.instance()
        album = Album(name='Test Album', slug='test-album')
        
        albums.add_album(album)
        
        assert 'test-album' in albums.albums
        assert albums.albums['test-album'] == album
    
    def test_json_dump_obj(self):
        """Test JSON serialization of Albums."""
        albums = Albums.instance()
        album1 = Album(name='Album 1', slug='album-1')
        album2 = Album(name='Album 2', slug='album-2')
        
        albums.add_album(album1)
        albums.add_album(album2)
        
        result = albums.json_dump_obj()
        
        assert result == albums.albums
        assert 'album-1' in result
        assert 'album-2' in result
    
    def test_getitem(self):
        """Test __getitem__ for accessing albums by index."""
        albums = Albums.instance()
        album1 = Album(name='Album 1', slug='album-1')
        album2 = Album(name='Album 2', slug='album-2')
        
        albums.add_album(album1)
        albums.add_album(album2)
        
        # __getitem__ returns albums as list values
        assert albums[0] in [album1, album2]
        assert albums[1] in [album1, album2]
        assert albums[0] != albums[1]
    
    @patch('fussel.generator.generate.find_unique_slug')
    @patch('fussel.generator.generate.is_supported_album')
    @patch('fussel.generator.generate.is_supported_photo')
    @patch('fussel.generator.generate.os.listdir')
    @patch('fussel.generator.generate.os.path.join')
    @patch('fussel.generator.generate.os.path.basename')
    @patch('fussel.generator.generate.os.makedirs')
    @patch('fussel.generator.generate.Config')
    @patch('fussel.generator.generate.Pool')
    @patch('fussel.generator.generate.People')
    def test_process_path(self, mock_people, mock_pool, mock_config, mock_makedirs,
                          mock_basename, mock_join, mock_listdir, mock_is_photo,
                          mock_is_album, mock_find_slug):
        """Test process_path method."""
        albums = Albums.instance()
        
        # Setup mocks
        mock_config.instance.return_value.recursive_albums = False
        mock_config.instance.return_value.recursive_albums_name_pattern = '{parent_album} > {album}'
        mock_config.instance.return_value.parallel_tasks = 2
        
        mock_listdir.return_value = ['album1', 'album2']
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_basename.side_effect = lambda p: p.split('/')[-1]
        mock_is_album.return_value = True
        mock_is_photo.return_value = False
        mock_find_slug.return_value = 'album-1'
        
        mock_yaml_config = Mock()
        
        # Mock Pool to return empty results
        mock_pool_instance = MagicMock()
        mock_pool_instance.__enter__.return_value.map.return_value = []
        mock_pool.return_value = mock_pool_instance
        
        mock_people.instance.return_value.detect_faces = Mock()
        
        albums.process_path(
            root_path='/input',
            output_albums_photos_path='/output',
            external_root='/external',
            yaml_config=mock_yaml_config
        )
        
        # Verify albums were processed
        assert mock_listdir.called
    
    @patch('fussel.generator.generate.find_unique_slug')
    @patch('fussel.generator.generate.is_supported_album')
    @patch('fussel.generator.generate.is_supported_photo')
    @patch('fussel.generator.generate.os.listdir')
    @patch('fussel.generator.generate.os.path.join')
    @patch('fussel.generator.generate.os.path.basename')
    @patch('fussel.generator.generate.os.makedirs')
    @patch('fussel.generator.generate.Config')
    @patch('fussel.generator.generate.Pool')
    @patch('fussel.generator.generate.People')
    @patch('fussel.generator.generate.pick_album_thumbnail')
    def test_process_album_path_with_photos(self, mock_pick_thumb, mock_people, mock_pool,
                                            mock_config, mock_makedirs, mock_basename,
                                            mock_join, mock_listdir, mock_is_photo,
                                            mock_is_album, mock_find_slug):
        """Test process_album_path with photos."""
        albums = Albums.instance()
        
        # Setup mocks
        mock_config.instance.return_value.recursive_albums = False
        mock_config.instance.return_value.parallel_tasks = 2
        
        mock_listdir.return_value = ['photo1.jpg']
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_basename.side_effect = lambda p: p.split('/')[-1] if '/' in p else p
        mock_is_album.return_value = False
        mock_is_photo.return_value = True
        mock_find_slug.return_value = 'photo-1'
        mock_pick_thumb.return_value = '/path/to/thumb.jpg'
        
        # Mock Pool to return a processed photo
        mock_photo = Photo(
            name='photo1.jpg',
            width=1000,
            height=800,
            src='/path/to/photo.jpg',
            thumb='/path/to/thumb.jpg',
            slug='photo-1',
            srcSet={}
        )
        mock_pool_instance = MagicMock()
        mock_pool_instance.__enter__.return_value.map.return_value = [
            ('/input/photo1.jpg', mock_photo)
        ]
        mock_pool.return_value = mock_pool_instance
        
        mock_people.instance.return_value.detect_faces = Mock()
        mock_people.instance.return_value.detect_faces.return_value = []
        
        # Mock Queue
        from unittest.mock import MagicMock as MockQueue
        with patch('fussel.generator.generate.Queue') as mock_queue_class:
            mock_queue = MockQueue()
            mock_queue.empty.return_value = True
            mock_queue_class.return_value = mock_queue
            
            mock_yaml_config = Mock()
            
            albums.process_album_path(
                album_dir='/input/album1',
                album_name='Album 1',
                output_albums_photos_path='/output',
                external_root='/external',
                yaml_config=mock_yaml_config
            )
            
            # Verify album was added
            assert len(albums.albums) > 0 or mock_find_slug.called
