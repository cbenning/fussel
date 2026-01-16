/**
 * Tests for App component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import App from './App';

// Mock site_data
jest.mock('../_gallery/site_data.js', () => ({
  site_data: {
    site_name: 'Test Gallery',
    people_enabled: true
  }
}));

// Mock child components to simplify testing
jest.mock('./Navbar', () => {
  const React = require('react');
  return function Navbar({ hasPeople, children }) {
    return (
      <div data-testid="navbar" data-has-people={hasPeople}>
        {children}
      </div>
    );
  };
});

jest.mock('./Collections', () => {
  const React = require('react');
  return function Collections() {
    return <div data-testid="collections">Collections</div>;
  };
});

jest.mock('./Collection', () => {
  const React = require('react');
  return function Collection() {
    return <div data-testid="collection">Collection</div>;
  };
});

jest.mock('./NotFound', () => {
  const React = require('react');
  return function NotFound() {
    return <div data-testid="not-found">Not Found</div>;
  };
});

// Mock Helmet
jest.mock('react-helmet', () => {
  const React = require('react');
  return {
    Helmet: ({ children }) => <div data-testid="helmet">{children}</div>
  };
});

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
