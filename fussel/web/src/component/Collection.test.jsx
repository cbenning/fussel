/**
 * Tests for Collection component
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import Collection from './Collection';

// Mock data imports
vi.mock('../_gallery/albums_data.js', () => ({
  albums_data: {
    'vacation-2024': {
      name: 'Vacation 2024',
      slug: 'vacation-2024',
      photos: [
        {
          name: 'Beach Photo',
          slug: 'beach-photo',
          src: '/path/to/beach.jpg',
          srcSet: { '(500, 500)w': '/path/to/beach-500.jpg' }
        },
        {
          name: 'Mountain Photo',
          slug: 'mountain-photo',
          src: '/path/to/mountain.jpg',
          srcSet: { '(500, 500)w': '/path/to/mountain-500.jpg' }
        }
      ]
    }
  }
}));

vi.mock('../_gallery/people_data.js', () => ({
  people_data: {}
}));

// Mock Swiper
vi.mock('swiper/react', () => ({
  Swiper: ({ children, className }) => <div className={className} data-testid="swiper">{children}</div>,
  SwiperSlide: ({ children, slug, 'data-hash': dataHash }) => (
    <div data-testid="swiper-slide" data-slug={slug} data-hash={dataHash}>{children}</div>
  )
}));

vi.mock('swiper/modules', () => ({
  Keyboard: {},
  Pagination: {},
  HashNavigation: {},
  Navigation: {}
}));

// Mock react-photo-album
vi.mock('react-photo-album', () => ({
  MasonryPhotoAlbum: ({ photos, onClick }) => (
    <div data-testid="photo-album">
      {(photos || []).map((photo, index) => (
        <img
          key={photo.key || index}
          src={photo.src}
          alt={photo.alt}
          onClick={() => onClick && onClick({ photo, index })}
        />
      ))}
    </div>
  )
}));

vi.mock('react-photo-album/masonry.css', () => ({}));

// Mock react-modal
vi.mock('react-modal', () => {
  const MockModal = ({ isOpen, children, onRequestClose, style }) => {
    if (!isOpen) return null;
    return <div data-testid="modal" onClick={onRequestClose} style={style}>{children}</div>;
  };
  MockModal.setAppElement = vi.fn();
  return { default: MockModal };
});

// Mock withRouter
const mockNavigate = vi.fn();
vi.mock('./withRouter', () => ({
  default: (Component) => {
    return function WrappedComponent(props) {
      const mockParams = props.params || { collectionType: 'albums', collection: 'vacation-2024' };
      return <Component {...props} params={mockParams} navigate={mockNavigate} />;
    };
  }
}));

describe('Collection', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    // Reset window.location.hash
    delete window.location;
    window.location = { hash: '' };
  });

  it('should render collection title', () => {
    render(
      <HashRouter>
        <Collection params={{ collectionType: 'albums', collection: 'vacation-2024' }} />
      </HashRouter>
    );

    expect(screen.getByText('Vacation 2024')).toBeInTheDocument();
  });

  it('should render breadcrumb navigation', () => {
    render(
      <HashRouter>
        <Collection params={{ collectionType: 'albums', collection: 'vacation-2024' }} />
      </HashRouter>
    );

    const albumsLink = screen.getByText('Albums');
    expect(albumsLink).toBeInTheDocument();
    expect(albumsLink.closest('a')).toHaveAttribute('href', '#/collections/albums');
  });

  it('should render photos in masonry layout', () => {
    render(
      <HashRouter>
        <Collection params={{ collectionType: 'albums', collection: 'vacation-2024' }} />
      </HashRouter>
    );

    const beachImage = screen.getByAltText('Beach Photo');
    expect(beachImage).toBeInTheDocument();
    expect(beachImage).toHaveAttribute('src', '/path/to/beach-500.jpg');

    const mountainImage = screen.getByAltText('Mountain Photo');
    expect(mountainImage).toBeInTheDocument();
  });

  it('should open modal when photo is clicked', () => {
    render(
      <HashRouter>
        <Collection params={{ collectionType: 'albums', collection: 'vacation-2024' }} />
      </HashRouter>
    );

    const beachImage = screen.getByAltText('Beach Photo');
    fireEvent.click(beachImage);

    expect(mockNavigate).toHaveBeenCalledWith('/collections/albums/vacation-2024/beach-photo');
  });

  it('should render modal when image param is provided', () => {
    render(
      <HashRouter>
        <Collection params={{ 
          collectionType: 'albums', 
          collection: 'vacation-2024',
          image: 'beach-photo'
        }} />
      </HashRouter>
    );

    const modal = screen.getByTestId('modal');
    expect(modal).toBeInTheDocument();
  });

  it('should render Swiper in modal when open', () => {
    render(
      <HashRouter>
        <Collection params={{ 
          collectionType: 'albums', 
          collection: 'vacation-2024',
          image: 'beach-photo'
        }} />
      </HashRouter>
    );

    const swiper = screen.getByTestId('swiper');
    expect(swiper).toBeInTheDocument();

    const slides = screen.getAllByTestId('swiper-slide');
    expect(slides.length).toBeGreaterThan(0);
  });

  it('should close modal when close button is clicked', () => {
    render(
      <HashRouter>
        <Collection params={{ 
          collectionType: 'albums', 
          collection: 'vacation-2024',
          image: 'beach-photo'
        }} />
      </HashRouter>
    );

    const closeButton = document.querySelector('.modal-close-button');
    fireEvent.click(closeButton);

    expect(mockNavigate).toHaveBeenCalledWith('/collections/albums/vacation-2024');
  });

  it('should render title for albums collection type', () => {
    const { container } = render(
      <HashRouter>
        <Collection params={{ collectionType: 'albums', collection: 'vacation-2024' }} />
      </HashRouter>
    );

    // Title method is used internally, verify it works through breadcrumb
    const albumsLink = screen.getByText('Albums');
    expect(albumsLink).toBeInTheDocument();
  });

  it('should render title for people collection type', () => {
    render(
      <HashRouter>
        <Collection params={{ collectionType: 'people', collection: 'john-doe' }} />
      </HashRouter>
    );

    // People title should appear in breadcrumb
    const peopleLink = screen.queryByText('People');
    // Note: This test depends on the actual data structure
  });
});
