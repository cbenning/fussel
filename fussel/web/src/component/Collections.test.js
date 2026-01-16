/**
 * Tests for Collections component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import Collections from './Collections';

// Mock data imports
jest.mock('../_gallery/albums_data.js', () => ({
  albums_data: {
    'vacation-2024': {
      name: 'Vacation 2024',
      slug: 'vacation-2024',
      photos: [{ slug: 'photo1' }, { slug: 'photo2' }],
      src: '/path/to/vacation.jpg'
    },
    'family-reunion': {
      name: 'Family Reunion',
      slug: 'family-reunion',
      photos: [{ slug: 'photo3' }],
      src: '/path/to/family.jpg'
    }
  }
}));

jest.mock('../_gallery/people_data.js', () => ({
  people_data: {
    'john-doe': {
      name: 'John Doe',
      slug: 'john-doe',
      photos: [{ slug: 'photo4' }, { slug: 'photo5' }, { slug: 'photo6' }],
      src: '/path/to/john.jpg'
    }
  }
}));

// Mock withRouter
jest.mock('./withRouter', () => (Component) => {
  return function WrappedComponent(props) {
    const mockParams = props.params || { collectionType: 'albums' };
    const mockNavigate = jest.fn();
    return <Component {...props} params={mockParams} navigate={mockNavigate} />;
  };
});

describe('Collections', () => {
  it('should render title for albums collection type', () => {
    render(
      <HashRouter>
        <Collections params={{ collectionType: 'albums' }} />
      </HashRouter>
    );

    expect(screen.getByText('Albums')).toBeInTheDocument();
  });

  it('should render title for people collection type', () => {
    render(
      <HashRouter>
        <Collections params={{ collectionType: 'people' }} />
      </HashRouter>
    );

    expect(screen.getByText('People')).toBeInTheDocument();
  });

  it('should render cards for albums', () => {
    render(
      <HashRouter>
        <Collections params={{ collectionType: 'albums' }} />
      </HashRouter>
    );

    expect(screen.getByText('Vacation 2024')).toBeInTheDocument();
    expect(screen.getByText('2 Photos')).toBeInTheDocument();
    expect(screen.getByText('Family Reunion')).toBeInTheDocument();
    expect(screen.getByText('1 Photo')).toBeInTheDocument();
  });

  it('should render cards for people', () => {
    render(
      <HashRouter>
        <Collections params={{ collectionType: 'people' }} />
      </HashRouter>
    );

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('3 Photos')).toBeInTheDocument();
  });

  it('should use collectionType from props when params missing', () => {
    render(
      <HashRouter>
        <Collections collectionType="albums" params={{}} />
      </HashRouter>
    );

    expect(screen.getByText('Albums')).toBeInTheDocument();
  });

  // Note: Photo count singular/plural logic is tested above in "should render cards" tests

  it('should create links to collection pages', () => {
    render(
      <HashRouter>
        <Collections params={{ collectionType: 'albums' }} />
      </HashRouter>
    );

    const vacationLink = screen.getByText('Vacation 2024').closest('a');
    expect(vacationLink).toHaveAttribute('href', '#/collections/albums/vacation-2024');
  });
});
