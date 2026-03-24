/**
 * Tests for withRouter Higher-Order Component
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { useParams, useNavigate } from 'react-router';
import withRouter from './withRouter';

// Mock react-router hooks
vi.mock('react-router', () => ({
  useParams: vi.fn(),
  useNavigate: vi.fn(),
}));

describe('withRouter', () => {
  const mockParams = { collectionType: 'albums', collection: 'vacation' };
  const mockNavigate = vi.fn();

  beforeEach(() => {
    useParams.mockReturnValue(mockParams);
    useNavigate.mockReturnValue(mockNavigate);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should inject params and navigate props to wrapped component', () => {
    // Create a test component
    const TestComponent = ({ params, navigate }) => {
      return (
        <div>
          <div data-testid="collection-type">{params.collectionType}</div>
          <button onClick={() => navigate('/test')}>Navigate</button>
        </div>
      );
    };

    // Wrap component with withRouter
    const WrappedComponent = withRouter(TestComponent);

    // Render wrapped component
    render(<WrappedComponent />);

    // Verify params are passed
    expect(screen.getByTestId('collection-type')).toHaveTextContent('albums');

    // Verify navigate function is available
    const button = screen.getByText('Navigate');
    button.click();
    expect(mockNavigate).toHaveBeenCalledWith('/test');
  });

  it('should pass through other props to wrapped component', () => {
    const TestComponent = ({ params, navigate, customProp }) => {
      return (
        <div>
          <div data-testid="custom">{customProp}</div>
          <div data-testid="collection">{params.collection}</div>
        </div>
      );
    };

    const WrappedComponent = withRouter(TestComponent);

    render(<WrappedComponent customProp="test-value" />);

    expect(screen.getByTestId('custom')).toHaveTextContent('test-value');
    expect(screen.getByTestId('collection')).toHaveTextContent('vacation');
  });

  it('should use current route params from useParams hook', () => {
    const differentParams = { collectionType: 'people', collection: 'john-doe' };
    useParams.mockReturnValue(differentParams);

    const TestComponent = ({ params }) => {
      return <div data-testid="type">{params.collectionType}</div>;
    };

    const WrappedComponent = withRouter(TestComponent);
    render(<WrappedComponent />);

    expect(screen.getByTestId('type')).toHaveTextContent('people');
  });
});
