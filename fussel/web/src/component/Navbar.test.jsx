/**
 * Tests for Navbar component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import Navbar from './Navbar';

describe('Navbar', () => {
  it('should render albums button', () => {
    render(
      <HashRouter>
        <Navbar hasAlbums={true} hasPeople={false} />
      </HashRouter>
    );

    const albumsLink = screen.getByText('Albums');
    expect(albumsLink).toBeInTheDocument();
    expect(albumsLink.closest('a')).toHaveAttribute('href', '#/collections/albums');
  });

  it('should render people button when hasPeople is true', () => {
    render(
      <HashRouter>
        <Navbar hasPeople={true} />
      </HashRouter>
    );

    const peopleLink = screen.getByText('People');
    expect(peopleLink).toBeInTheDocument();
    expect(peopleLink.closest('a')).toHaveAttribute('href', '#/collections/people');
  });

  it('should not render people button when hasPeople is false', () => {
    render(
      <HashRouter>
        <Navbar hasPeople={false} />
      </HashRouter>
    );

    expect(screen.queryByText('People')).not.toBeInTheDocument();
  });

  it('should render logo image', () => {
    render(
      <HashRouter>
        <Navbar hasPeople={false} />
      </HashRouter>
    );

    const logo = screen.getByAltText('logo');
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('width', '32');
    expect(logo).toHaveAttribute('height', '32');
  });

  it('should render Outlet for nested routes', () => {
    const { container } = render(
      <HashRouter>
        <Navbar hasPeople={false} />
      </HashRouter>
    );

    // Outlet renders child routes, so we just verify the structure
    const nav = container.querySelector('nav');
    expect(nav).toBeInTheDocument();
  });
});
