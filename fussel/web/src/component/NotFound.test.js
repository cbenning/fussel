/**
 * Tests for NotFound component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import NotFound from './NotFound';

// Mock withRouter
jest.mock('./withRouter', () => (Component) => Component);

describe('NotFound', () => {
  it('should render "Not Found" message', () => {
    render(
      <HashRouter>
        <NotFound />
      </HashRouter>
    );

    expect(screen.getByText('Not Found')).toBeInTheDocument();
  });

  it('should have correct CSS class', () => {
    const { container } = render(
      <HashRouter>
        <NotFound />
      </HashRouter>
    );

    const messageDiv = container.querySelector('.message');
    expect(messageDiv).toBeInTheDocument();
    expect(messageDiv).toHaveTextContent('Not Found');
  });
});
