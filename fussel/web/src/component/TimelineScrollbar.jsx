import React, { Component } from 'react';
import './Collection.css';

class TimelineScrollbar extends Component {
  constructor(props) {
    super(props);
    this.state = {
      scrollTop: 0,
      scrollHeight: 0,
      clientHeight: 0,
      navbarHeight: 0,
      datePositions: [],
      visibleLabels: []
    };
    this.timelineRef = React.createRef();
    this.scrollTimeout = null;
    this.rafId = null;
    this.cachedHeaderHeight = null; // Cache header height to prevent recalculation
  }

  componentDidMount() {
    // Cache header height immediately
    this.cachedHeaderHeight = this.props.headerHeight;
    // Initial scroll position update
    this.updateScrollPosition();
    // Calculate positions after a short delay to ensure DOM is ready
    setTimeout(() => {
      // Re-cache header height after DOM is ready
      this.cachedHeaderHeight = this.props.headerHeight;
      this.calculateDatePositions();
      this.updateScrollPosition();
    }, 500); // Increased delay to ensure images are loaded
    this.setupScrollListener();
    window.addEventListener('resize', this.handleResize);
  }

  componentDidUpdate(prevProps) {
    if (prevProps.photos !== this.props.photos || 
        prevProps.sortOrder !== this.props.sortOrder) {
      // Delay to ensure DOM is ready
      setTimeout(() => {
        this.calculateDatePositions();
        this.updateScrollPosition();
      }, 100);
    }
    // Update cached header height if it changed, but don't recalculate positions
    if (prevProps.headerHeight !== this.props.headerHeight) {
      this.cachedHeaderHeight = this.props.headerHeight;
    }
  }

  componentWillUnmount() {
    this.removeScrollListener();
    window.removeEventListener('resize', this.handleResize);
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
    }
    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout);
    }
  }

  handleResize = () => {
    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout);
    }
    this.scrollTimeout = setTimeout(() => {
      this.calculateDatePositions();
      this.updateScrollPosition();
    }, 100);
  }

  setupScrollListener = () => {
    // Always use window scroll for the gallery
    window.addEventListener('scroll', this.handleScroll, { passive: true });
  }

  removeScrollListener = () => {
    window.removeEventListener('scroll', this.handleScroll);
  }

  handleScroll = () => {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
    }
    this.rafId = requestAnimationFrame(() => {
      // Only update scroll position, don't recalculate date positions
      this.updateScrollPosition();
    });
  }

  updateScrollPosition = () => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = window.innerHeight;
    
    // Get navbar height
    const navbar = document.querySelector('.navbar');
    const navbarHeight = navbar ? navbar.getBoundingClientRect().height : 0;

    this.setState({
      scrollTop,
      scrollHeight,
      clientHeight,
      navbarHeight
    });
  }

  calculateDatePositions = () => {
    const { photos, sortOrder, headerHeight } = this.props;
    
    if (!photos || photos.length === 0) {
      this.setState({ datePositions: [], visibleLabels: [] });
      return;
    }

    // Group photos by year-month
    const dateGroups = new Map();
    const photosWithoutDate = [];
    
    photos.forEach((photo, index) => {
      if (!photo.date) {
        photosWithoutDate.push({ photo, index });
        return;
      }

      try {
        const date = new Date(photo.date);
        if (isNaN(date.getTime())) {
          photosWithoutDate.push({ photo, index });
          return;
        }

        const year = date.getFullYear();
        const month = date.getMonth();
        const key = `${year}-${month}`;
        const label = this.formatDate(date);

        if (!dateGroups.has(key)) {
          dateGroups.set(key, {
            key,
            label,
            year,
            month,
            photos: [],
            firstIndex: index
          });
        }
        dateGroups.get(key).photos.push({ photo, index });
      } catch (e) {
        console.warn('TimelineScrollbar: Error processing photo date', e, photo);
        photosWithoutDate.push({ photo, index });
      }
    });

    if (dateGroups.size === 0) {
      this.setState({ datePositions: [], visibleLabels: [] });
      return;
    }

    // Wait for images to be rendered, then calculate positions
    // Use multiple requestAnimationFrame calls to ensure layout is complete
    const tryCalculate = (attempt = 0) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          // Try multiple selectors to find gallery images
          let galleryImages = document.querySelectorAll('.gallery-image');
          
          // Try alternative selectors if main one doesn't work
          if (galleryImages.length === 0) {
            galleryImages = document.querySelectorAll('img[data-photo-index]');
          }
          
          if (galleryImages.length === 0) {
            // Try finding images within react-photo-album containers
            const albumContainer = document.querySelector('[class*="react-photo-album"]');
            if (albumContainer) {
              galleryImages = albumContainer.querySelectorAll('img');
            }
          }
          
          if (galleryImages.length === 0 && attempt < 15) {
            // Images not ready yet, try again after a short delay
            setTimeout(() => tryCalculate(attempt + 1), 200);
            return;
          }
          
          if (galleryImages.length === 0) {
            // Give up after attempts
            return;
          }

        const datePositions = [];
        const { headerHeight } = this.props;
        
        dateGroups.forEach((group) => {
          const firstPhotoIndex = group.firstIndex;
          
          // Try to find the image by data-photo-index first
          let firstPhotoImage = Array.from(galleryImages).find(img => {
            const photoIndex = parseInt(img.getAttribute('data-photo-index') || '-1', 10);
            return photoIndex === firstPhotoIndex;
          });
          
          // If not found, try by array index (images should be in order)
          if (!firstPhotoImage && galleryImages.length > firstPhotoIndex) {
            firstPhotoImage = galleryImages[firstPhotoIndex];
          }

          if (firstPhotoImage) {
            const imageRect = firstPhotoImage.getBoundingClientRect();
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            // Position relative to document top, accounting for header
            // Use cached header height for consistency
            const effectiveHeaderHeight = this.cachedHeaderHeight !== null ? this.cachedHeaderHeight : (headerHeight || 0);
            const position = imageRect.top + scrollTop - effectiveHeaderHeight;
            
            datePositions.push({
              ...group,
              position: Math.max(0, position),
              photoCount: group.photos.length
            });
          }
        });

        // Sort by position
        datePositions.sort((a, b) => a.position - b.position);

        // Select visible labels based on available space
        const visibleLabels = this.selectVisibleLabels(datePositions);

        this.setState({ datePositions, visibleLabels });
        });
      });
    };
    
    tryCalculate();

  }

  selectVisibleLabels = (datePositions) => {
    if (datePositions.length === 0) return [];
    if (datePositions.length <= 3) return datePositions;

    const timelineHeight = this.timelineRef.current?.clientHeight || window.innerHeight;
    const minLabelSpacing = 60; // Minimum pixels between labels
    const maxLabels = Math.floor(timelineHeight / minLabelSpacing);

    if (datePositions.length <= maxLabels) {
      return datePositions;
    }

    // Always include first and last
    const selected = [datePositions[0]];
    const last = datePositions[datePositions.length - 1];

    // Calculate interval
    const remaining = maxLabels - 2;
    if (remaining <= 0) {
      return [datePositions[0], last];
    }

    const interval = Math.floor((datePositions.length - 2) / remaining);
    
    // Select evenly spaced labels, prioritizing those with more photos
    const middlePositions = datePositions.slice(1, -1);
    
    // Sort by photo count (descending) to prioritize dates with more photos
    const sortedByCount = [...middlePositions].sort((a, b) => b.photoCount - a.photoCount);
    
    // Take top ones, then sort by position
    const topByCount = sortedByCount.slice(0, remaining).sort((a, b) => a.position - b.position);
    
    // If we still have room, fill gaps with evenly spaced positions
    if (topByCount.length < remaining) {
      for (let i = 1; i < datePositions.length - 1; i += interval) {
        if (topByCount.length >= remaining) break;
        const pos = datePositions[i];
        if (!topByCount.find(p => p.key === pos.key)) {
          topByCount.push(pos);
        }
      }
      topByCount.sort((a, b) => a.position - b.position);
    }

    selected.push(...topByCount);
    selected.push(last);

    return selected;
  }

  formatDate = (date) => {
    const year = date.getFullYear();
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = monthNames[date.getMonth()];
    return `${year} ${month}`;
  }

  handleLabelClick = (datePosition) => {
    // Simply scroll to the position where this date's photos are
    // The label is already positioned where the scroll indicator will be for this scroll position
    const scrollTo = Math.max(0, datePosition.position);
    window.scrollTo({
      top: scrollTo,
      behavior: 'smooth'
    });
  }

  render() {
    const { scrollTop, scrollHeight, clientHeight, navbarHeight, visibleLabels, datePositions } = this.state;
    const { photos } = this.props;
    
    // Use cached header height to ensure consistency
    const headerHeight = this.cachedHeaderHeight !== null ? this.cachedHeaderHeight : (this.props.headerHeight || 0);
    
    // Calculate available height (viewport minus navbar)
    const availableHeight = clientHeight - navbarHeight;
    const timelineTop = navbarHeight;

    // Always render if we have photos, even if scroll calculations aren't ready yet
    if (!photos || photos.length === 0) {
      return null;
    }

    // If scrollHeight isn't calculated yet, show a minimal timeline
    if (!scrollHeight || scrollHeight <= clientHeight) {
      const tempTimelineHeight = availableHeight - 40;
      const tempLabelPositions = visibleLabels && visibleLabels.length > 0 ? visibleLabels.map((label, index) => {
        // Distribute labels evenly for now
        const labelTop = (index / Math.max(1, visibleLabels.length - 1)) * tempTimelineHeight;
        return { ...label, labelTop: Math.max(0, Math.min(tempTimelineHeight, labelTop)) };
      }) : [];
      
      return (
        <div 
          ref={this.timelineRef}
          className="timeline-scrollbar"
          style={{ top: `${timelineTop}px`, bottom: '0' }}
        >
          <div className="timeline-track" style={{ height: `${tempTimelineHeight}px` }}>
            {tempLabelPositions.length > 0 ? tempLabelPositions.map((label) => (
              <button
                key={label.key}
                className="timeline-label"
                style={{
                  top: `${label.labelTop}px`
                }}
                onClick={() => this.handleLabelClick(label)}
                title={`${label.label} (${label.photoCount} photo${label.photoCount !== 1 ? 's' : ''})`}
              >
                {label.label}
              </button>
            )) : null}
          </div>
        </div>
      );
    }

    const timelineHeight = availableHeight - 40; // 40px for margins
    const scrollableHeight = scrollHeight - clientHeight;
    const scrollRatio = scrollableHeight > 0 ? scrollTop / scrollableHeight : 0;
    const thumbHeight = Math.max(20, (clientHeight / scrollHeight) * timelineHeight);
    const thumbTop = scrollRatio * (timelineHeight - thumbHeight);

    // Calculate label positions relative to timeline
    // Labels should be positioned where the scroll indicator (thumb) will be when scrolled to that date
    const labelPositions = visibleLabels && visibleLabels.length > 0 ? visibleLabels.map(label => {
      // Calculate what scrollTop would be needed to show this date's photos at the top of viewport
      // label.position is the document position where the photo is (accounting for header)
      // We need to calculate the scrollTop that would put the scroll indicator at the label position
      
      // The scroll indicator position is: scrollRatio * (timelineHeight - thumbHeight)
      // where scrollRatio = scrollTop / scrollableHeight
      
      // First, calculate the scrollTop needed to show this date
      // The photo position is relative to document top, but we need scrollTop
      const scrollTopForDate = Math.max(0, label.position);
      
      // Calculate the scroll ratio for this position
      const scrollRatioForDate = scrollableHeight > 0 ? scrollTopForDate / scrollableHeight : 0;
      
      // Calculate where the scroll indicator (thumb) would be for this scroll position
      // This is where the label should be positioned
      const labelTop = scrollRatioForDate * (timelineHeight - thumbHeight) + (thumbHeight / 2);
      
      // Ensure label is within bounds
      return { ...label, labelTop: Math.max(0, Math.min(timelineHeight, labelTop)) };
    }) : [];

    return (
      <div 
        ref={this.timelineRef}
        className="timeline-scrollbar"
        style={{ top: `${timelineTop}px`, bottom: '0' }}
      >
        <div className="timeline-track" style={{ height: `${timelineHeight}px`, marginTop: '20px', marginBottom: '20px' }}>
          <div 
            className="timeline-thumb"
            style={{
              top: `${Math.max(0, Math.min(timelineHeight - thumbHeight, thumbTop))}px`,
              height: `${thumbHeight}px`
            }}
          />
          {labelPositions.length > 0 && labelPositions.map((label) => (
            <button
              key={label.key}
              className="timeline-label"
              style={{
                top: `${label.labelTop}px`
              }}
              onClick={() => this.handleLabelClick(label)}
              title={`${label.label} (${label.photoCount} photo${label.photoCount !== 1 ? 's' : ''})`}
            >
              {label.label}
            </button>
          ))}
        </div>
      </div>
    );
  }
}

export default TimelineScrollbar;
