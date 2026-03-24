/**
 * Tests for App component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import App from './App';

// Mock site_data
vi.mock('../_gallery/site_data.js', () => ({
  site_data: {
    site_name: 'Test Gallery',
    people_enabled: true
  }
}));

// Mock child components to simplify testing
vi.mock('./Navbar', () => ({
  default: function Navbar({ hasPeople, children }) {
    return (
      <div data-testid="navbar" data-has-people={hasPeople}>
        {children}
      </div>
    );
  }
}));

vi.mock('./Collections', () => ({
  default: function Collections() {
    return <div data-testid="collections">Collections</div>;
  }
}));

vi.mock('./Collection', () => ({
  default: function Collection() {
    return <div data-testid="collection">Collection</div>;
  }
}));

vi.mock('./NotFound', () => ({
  default: function NotFound() {
    return <div data-testid="not-found">Not Found</div>;
  }
}));

// Mock Helmet
vi.mock('react-helmet-async', () => ({
  HelmetProvider: ({ children }) => <>{children}</>,
  Helmet: ({ children }) => <div data-testid="helmet">{children}</div>
}));

describe('App', () => {
  it('should render Helmet with site name', () => {
    render(
      <HashRouter>
        <App />
      </HashRouter>
    );

    const helmet = screen.getByTestId('helmet');
    expect(helmet).toBeInTheDocument();
  });

  it('should pass people_enabled to Navbar', () => {
    render(
      <HashRouter>
        <App />
      </HashRouter>
    );

    const navbar = screen.getByTestId('navbar');
    expect(navbar).toHaveAttribute('data-has-people', 'true');
  });

});
