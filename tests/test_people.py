"""
Tests for People class in fussel.generator.generate module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from bs4 import BeautifulSoup
from PIL import Image
from fussel.generator.generate import People, Person, Face, FaceGeometry


class TestPeopleSingleton:
    """Tests for People singleton pattern."""
    
    def setup_method(self):
        """Reset People singleton before each test."""
        People._instance = None
    
    def test_cannot_instantiate_directly(self):
        """Test that People cannot be instantiated directly."""
        with pytest.raises(RuntimeError, match="Call instance\\(\\) instead"):
            People()
    
    def test_instance_returns_singleton(self):
        """Test that instance() returns the same object."""
        instance1 = People.instance()
        instance2 = People.instance()
        
        assert instance1 is instance2
        assert instance1 is People._instance
    
    def test_people_initialization(self):
        """Test that People initializes correctly."""
        people = People.instance()
        
        assert people.people == {}
        assert isinstance(people.slugs, set)
        assert len(people.slugs) == 0


class TestPeopleDetectFaces:
    """Tests for People.detect_faces method."""
    
    def setup_method(self):
        """Reset People singleton before each test."""
        People._instance = None
    
    @patch('fussel.generator.generate.People.extract_faces')
    @patch('fussel.generator.generate.Image')
    @patch('fussel.generator.generate.find_unique_slug')
    def test_detect_faces_new_person(self, mock_find_slug, mock_image, mock_extract):
        """Test detecting faces for a new person."""
        people = People.instance()
        mock_find_slug.return_value = 'john-doe'
        
        # Mock face extraction
        face = Face(
            name='John Doe',
            geometry=FaceGeometry(w='0.2', h='0.3', x='0.5', y='0.5')
        )
        mock_extract.return_value = [face]
        
        # Mock photo
        mock_photo = Mock()
        mock_photo.slug = 'photo1'
        
        # Mock image operations
        mock_img = MagicMock()
        mock_img.size = (1000, 1000)
        mock_img.crop.return_value = mock_img
        mock_img.save.return_value = None
        mock_image.open.return_value.__enter__.return_value = mock_img
        mock_image.open.return_value.__exit__.return_value = None
        
        result = people.detect_faces(
            photo=mock_photo,
            original_src='/path/original.jpg',
            largest_src='/path/largest.jpg',
            output_path='/output',
            external_path='/external'
        )
        
        assert len(result) == 1
        assert 'John Doe' in people.people
        assert people.people['John Doe'].name == 'John Doe'
        assert people.people['John Doe'].slug == 'john-doe'
    
    @patch('fussel.generator.generate.People.extract_faces')
    @patch('fussel.generator.generate.Image')
    def test_detect_faces_existing_person(self, mock_image, mock_extract):
        """Test detecting faces for an existing person."""
        people = People.instance()
        
        # Add existing person
        existing_person = Person(name='John Doe', slug='john-doe')
        people.people['John Doe'] = existing_person
        
        # Mock face extraction
        face = Face(
            name='John Doe',
            geometry=FaceGeometry(w='0.2', h='0.3', x='0.5', y='0.5')
        )
        mock_extract.return_value = [face]
        
        mock_photo = Mock()
        mock_photo.slug = 'photo2'
        
        # Mock image operations for thumbnail creation
        mock_img = MagicMock()
        mock_img.size = (1000, 1000)
        mock_img.crop.return_value = mock_img
        mock_img.save.return_value = None
        mock_image.open.return_value.__enter__.return_value = mock_img
        mock_image.open.return_value.__exit__.return_value = None
        
        result = people.detect_faces(
            photo=mock_photo,
            original_src='/path/original.jpg',
            largest_src='/path/largest.jpg',
            output_path='/output',
            external_path='/external'
        )
        
        assert len(result) == 1
        assert len(existing_person.photos) == 1
        assert existing_person.photos[0] == mock_photo
    
    @patch('fussel.generator.generate.People.extract_faces')
    @patch('fussel.generator.generate.find_unique_slug')
    def test_detect_faces_person_with_thumbnail(self, mock_find_slug, mock_extract):
        """Test detecting faces for person who already has thumbnail (should skip thumbnail creation)."""
        people = People.instance()
        
        # Add existing person with thumbnail
        existing_person = Person(name='John Doe', slug='john-doe')
        existing_person.src = '/path/to/thumbnail.jpg'  # Already has thumbnail
        people.people['John Doe'] = existing_person
        
        face = Face(
            name='John Doe',
            geometry=FaceGeometry(w='0.2', h='0.3', x='0.5', y='0.5')
        )
        mock_extract.return_value = [face]
        
        mock_photo = Mock()
        mock_photo.slug = 'photo2'
        
        # Should not call find_unique_slug since person exists
        result = people.detect_faces(
            photo=mock_photo,
            original_src='/path/original.jpg',
            largest_src='/path/largest.jpg',
            output_path='/output',
            external_path='/external'
        )
        
        assert len(result) == 1
        # Person should still get the photo added
        assert len(existing_person.photos) == 1
        # But thumbnail path should remain unchanged
        assert existing_person.src == '/path/to/thumbnail.jpg'
        # find_unique_slug should not be called for existing person
        mock_find_slug.assert_not_called()


class TestPeopleExtractFaces:
    """Tests for People.extract_faces method."""
    
    def setup_method(self):
        """Reset People singleton before each test."""
        People._instance = None
    
    def test_extract_faces_no_applist(self):
        """Test extract_faces when image has no applist."""
        people = People.instance()
        
        mock_img = MagicMock()
        del mock_img.applist  # Remove applist attribute
        
        with patch('fussel.generator.generate.Image') as mock_image:
            mock_image.open.return_value.__enter__.return_value = mock_img
            mock_image.open.return_value.__exit__.return_value = None
            
            result = people.extract_faces('/path/to/photo.jpg')
            assert result == []
    
    def test_extract_faces_with_xmp_data(self):
        """Test extract_faces with valid XMP data."""
        people = People.instance()
        
        # Create sample XMP data
        xmp_body = '''<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                 xmlns:mwg-rs="http://www.metadataworkinggroup.com/schemas/regions/">
            <rdf:Description mwg-rs:type="Face" mwg-rs:name="John Doe">
                <mwg-rs:Area starea:x="0.5" starea:y="0.5" starea:w="0.2" starea:h="0.3"/>
            </rdf:Description>
        </rdf:RDF>'''
        
        # Mock image with applist
        mock_img = MagicMock()
        xmp_bytes = bytes('\x00http://ns.adobe.com/xap/1.0/\x00' + xmp_body, 'utf-8')
        mock_img.applist = [('APP1', xmp_bytes)]
        
        with patch('fussel.generator.generate.Image') as mock_image:
            mock_image.open.return_value.__enter__.return_value = mock_img
            mock_image.open.return_value.__exit__.return_value = None
            
            result = people.extract_faces('/path/to/photo.jpg')
            
            assert len(result) == 1
            assert result[0].name == 'John Doe'
            assert result[0].geometry.x == '0.5'
            assert result[0].geometry.y == '0.5'
            assert result[0].geometry.w == '0.2'
            assert result[0].geometry.h == '0.3'
    
    def test_extract_faces_alternative_namespace(self):
        """Test extract_faces with alternative namespace format."""
        people = People.instance()
        
        # XMP with alternative namespace format
        xmp_body = '''<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <rdf:Description type="Face" name="Jane Doe">
                <Area x="0.3" y="0.4" w="0.15" h="0.25"/>
            </rdf:Description>
        </rdf:RDF>'''
        
        mock_img = MagicMock()
        xmp_bytes = bytes('\x00http://ns.adobe.com/xap/1.0/\x00' + xmp_body, 'utf-8')
        mock_img.applist = [('APP1', xmp_bytes)]
        
        with patch('fussel.generator.generate.Image') as mock_image:
            mock_image.open.return_value.__enter__.return_value = mock_img
            mock_image.open.return_value.__exit__.return_value = None
            
            result = people.extract_faces('/path/to/photo.jpg')
            
            assert len(result) == 1
            assert result[0].name == 'Jane Doe'
    
    def test_extract_faces_duplicate_detection(self):
        """Test that duplicate faces are not added."""
        people = People.instance()
        
        xmp_body = '''<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <rdf:Description type="Face" name="John Doe">
                <Area x="0.5" y="0.5" w="0.2" h="0.3"/>
                <Area x="0.5" y="0.5" w="0.2" h="0.3"/>
            </rdf:Description>
        </rdf:RDF>'''
        
        mock_img = MagicMock()
        xmp_bytes = bytes('\x00http://ns.adobe.com/xap/1.0/\x00' + xmp_body, 'utf-8')
        mock_img.applist = [('APP1', xmp_bytes)]
        
        with patch('fussel.generator.generate.Image') as mock_image:
            mock_image.open.return_value.__enter__.return_value = mock_img
            mock_image.open.return_value.__exit__.return_value = None
            
            result = people.extract_faces('/path/to/photo.jpg')
            
            # Should only have one face despite duplicate area
            assert len(result) == 1
    
    def test_extract_faces_invalid_segment(self):
        """Test extract_faces with invalid segment data."""
        people = People.instance()
        
        mock_img = MagicMock()
        # Invalid segment that will cause ValueError
        mock_img.applist = [('APP1', b'invalid data without null byte')]
        
        with patch('fussel.generator.generate.Image') as mock_image:
            mock_image.open.return_value.__enter__.return_value = mock_img
            mock_image.open.return_value.__exit__.return_value = None
            
            result = people.extract_faces('/path/to/photo.jpg')
            # Should handle error gracefully and return empty list
            assert result == []


class TestPeopleJsonDumpObj:
    """Tests for People.json_dump_obj method."""
    
    def setup_method(self):
        """Reset People singleton before each test."""
        People._instance = None
    
    def test_json_dump_obj(self):
        """Test JSON serialization of People."""
        people = People.instance()
        
        person1 = Person(name='John Doe', slug='john-doe')
        person2 = Person(name='Jane Doe', slug='jane-doe')
        
        people.people['John Doe'] = person1
        people.people['Jane Doe'] = person2
        
        result = people.json_dump_obj()
        
        assert 'john-doe' in result
        assert 'jane-doe' in result
        assert result['john-doe'] == person1
        assert result['jane-doe'] == person2
    
    def test_json_dump_obj_empty(self):
        """Test JSON serialization with no people."""
        people = People.instance()
        result = people.json_dump_obj()
        assert result == {}
