import React, { Component } from "react";
import { MasonryPhotoAlbum } from "react-photo-album";
import "react-photo-album/masonry.css";
import withRouter from './withRouter';
import { albums_data } from "../_gallery/albums_data.js"
import { people_data } from "../_gallery/people_data.js"
// photos_data might not exist if photos is disabled
let photos_data = [];
try {
  // Use dynamic import to handle missing file gracefully
  const photosModule = require("../_gallery/photos_data.js");
  photos_data = photosModule.photos_data || [];
} catch (e) {
  // photos_data.js doesn't exist - photos is disabled or not generated yet
  photos_data = [];
}
import { site_data } from "../_gallery/site_data.js"
import { Keyboard, Pagination, HashNavigation, Navigation } from "swiper/modules";
import { Swiper, SwiperSlide } from 'swiper/react';
import 'swiper/css';
import 'swiper/css/navigation'
import 'swiper/css/pagination'
import Modal from 'react-modal';

import { Link } from "react-router-dom";
import "./Collection.css";
import TimelineScrollbar from "./TimelineScrollbar";

Modal.setAppElement('#app');

// FaceTagOverlay component for displaying face rectangles
class FaceTagOverlay extends Component {
  constructor(props) {
    super(props);
    this.state = {
      offsetX: 0,
      offsetY: 0,
      scale: 1
    };
  }

  componentDidMount() {
    // Wait for next frame to ensure DOM is ready
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        this.calculateDimensions();
      });
    });
    
    this.resizeHandler = () => {
      this.calculateDimensions();
    };
    window.addEventListener('resize', this.resizeHandler);
  }

  componentDidUpdate(prevProps) {
    // Recalculate when image, container refs, or original dimensions change
    if (prevProps.imageRef !== this.props.imageRef || 
        prevProps.containerRef !== this.props.containerRef ||
        prevProps.originalWidth !== this.props.originalWidth ||
        prevProps.originalHeight !== this.props.originalHeight) {
      // Use double requestAnimationFrame to ensure layout is complete
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          this.calculateDimensions();
        });
      });
    }
  }

  componentWillUnmount() {
    if (this.resizeHandler) {
      window.removeEventListener('resize', this.resizeHandler);
    }
  }

  calculateDimensions = () => {
    const { imageRef, containerRef, originalWidth, originalHeight } = this.props;
    
    // Validate all required props and refs
    if (!imageRef || !containerRef || !originalWidth || originalWidth === 0 || !originalHeight || originalHeight === 0) {
      return;
    }

    // Ensure image is fully loaded before calculating (naturalWidth/Height are 0 until loaded)
    if (!imageRef.complete || imageRef.naturalWidth === 0 || imageRef.naturalHeight === 0) {
      return;
    }

    // Use getBoundingClientRect to get displayed dimensions and positions (browser-scaled)
    // This accounts for CSS transforms (max-width/max-height) and translate(-50%, -50%)
    const imgRect = imageRef.getBoundingClientRect();
    const containerRect = containerRef.getBoundingClientRect();
    
    // Ensure we have valid dimensions (image must be rendered)
    if (imgRect.width === 0 || imgRect.height === 0 || 
        containerRect.width === 0 || containerRect.height === 0) {
      return;
    }
    
    const displayedWidth = imgRect.width;
    const displayedHeight = imgRect.height;
    
    // Validate that displayed dimensions are reasonable (prevent division by zero or invalid scales)
    if (!isFinite(displayedWidth) || !isFinite(displayedHeight) || displayedWidth <= 0 || displayedHeight <= 0) {
      return;
    }
    
    // Calculate scale: face coords are normalized (0-1) relative to ORIGINAL dimensions
    // Two scales apply:
    // 1. Original -> Generated size (e.g., 4000 -> 1600): This is the file size on disk
    // 2. Generated -> Browser display (e.g., 1600 -> 800): This is CSS scaling
    // Face geometry is relative to ORIGINAL, so scale directly: displayed / original
    // The intermediate generated size doesn't matter because coords are normalized to original
    // Using displayedWidth/originalWidth as uniform scale assumes aspect ratio is preserved (which it is via max-width/max-height)
    const scale = displayedWidth / originalWidth;
    
    // Calculate position of image relative to container
    // Use getBoundingClientRect() directly - it already accounts for transforms, padding, borders, etc.
    // This gives us the actual rendered position of the image's bounding box
    // The image's top-left corner relative to the container is simply:
    const offsetX = imgRect.left - containerRect.left;
    const offsetY = imgRect.top - containerRect.top;
    
    // Validate scale is finite and reasonable
    if (!isFinite(scale) || scale <= 0) {
      return;
    }
    
    // Only update state if values have changed to avoid unnecessary re-renders
    this.setState(prevState => {
      if (prevState && 
          prevState.offsetX === offsetX && 
          prevState.offsetY === offsetY && 
          prevState.scale === scale) {
        return null; // No change needed
      }
      return { offsetX, offsetY, scale };
    });
  }

  render() {
    const { faces, imageRef, containerRef, originalWidth, originalHeight, navigate, onCloseModal } = this.props;
    if (!imageRef || !containerRef || !faces || faces.length === 0) return null;

    // Use cached dimensions from state to avoid expensive getBoundingClientRect in render
    const { offsetX = 0, offsetY = 0, scale = 1 } = this.state || {};

    return (
      <div className="face-tag-overlay">
        {faces.map((face, idx) => {
          // XMP coordinates are normalized (0-1) relative to original image dimensions
          // IMPORTANT: x and y represent the CENTER of the face, not the top-left corner
          // Convert to pixels and adjust to get top-left corner
          const faceCenterX = face.geometry.x * originalWidth * scale;
          const faceCenterY = face.geometry.y * originalHeight * scale;
          const faceW = face.geometry.w * originalWidth * scale;
          const faceH = face.geometry.h * originalHeight * scale;
          
          // Calculate top-left corner: center - (width/2, height/2)
          const faceX = faceCenterX - (faceW / 2);
          const faceY = faceCenterY - (faceH / 2);
          
          // Add the image's position within the container to get final position
          const x = faceX + offsetX;
          const y = faceY + offsetY;

          return (
            <div
              key={idx}
              className="face-tag-rectangle"
              style={{
                left: `${x}px`,
                top: `${y}px`,
                width: `${faceW}px`,
                height: `${faceH}px`,
              }}
            >
              <a 
                className="face-tag-label" 
                href={`#/collections/people/${face.slug}`}
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  // Close modal before navigating
                  if (this.props.onCloseModal) {
                    this.props.onCloseModal();
                  }
                  // Navigate to person's gallery
                  if (navigate) {
                    navigate(`/collections/people/${face.slug}`);
                  }
                }}
              >
                {face.name}
              </a>
            </div>
          );
        })}
      </div>
    );
  }
}

class Collection extends Component {

  constructor(props) {
    super(props);
    // Load toggle states from localStorage
    const savedShowFaceTags = localStorage.getItem('fussel_showFaceTags') === 'true';
    const savedShowPhotoInfo = localStorage.getItem('fussel_showPhotoInfo') === 'true';
    this.state = {
      viewerIsOpen: true ? this.props.params.image != undefined : false,
      currentPhotoIndex: 0,
      showPhotoInfo: savedShowPhotoInfo,
      showFaceTags: savedShowFaceTags,
      zoomLevel: 1.0,
      panX: 0,
      panY: 0,
      isDragging: false,
      // Photos-specific state
      sortOrder: localStorage.getItem('fussel_photos_sortOrder') || 'desc',
      selectedPeople: [],
      peopleFilterOpen: false,
      peopleFilterSearch: ''
    };
    this.swiperRef = null;
    this.dragStartX = 0;
    this.dragStartY = 0;
    this.dragStartPanX = 0;
    this.dragStartPanY = 0;
    this.currentImageRef = null;
    this._isDragging = false; // Synchronous flag for dragging state
    this.galleryContainerRef = React.createRef();
    this.headerRef = React.createRef();
  }

  modalStateTracker = (event) => {
    var newPath = event.newURL.split("#", 2)
    if (newPath.length < 2) {
      return
    }
    var oldPath = event.oldURL.split("#", 2)
    if (oldPath.length < 2) {
      return
    }

    const collectionType = this.props.params.collectionType || 'photos';
    const collection = this.props.params.collection;
    
    // For photos view, there's no collection name - URL is /collections/photos
    // For albums/people, URL is /collections/{type}/{collection}
    var closedModalUrl;
    if (collectionType === 'photos') {
      closedModalUrl = "/collections/photos";
    } else {
      closedModalUrl = `/collections/${collectionType}/${collection}`;
    }

    if (this.state.viewerIsOpen) {
      if (
        oldPath[1] != closedModalUrl &&
        newPath[1] == closedModalUrl
      ) {
        this.setState({
          viewerIsOpen: false
        })
        // Re-enable body scrolling when modal is closed
        const page = document.getElementsByTagName('body')[0];
        if (page) {
          page.classList.remove('noscroll');
        }
      }
    }

    if (!this.state.viewerIsOpen) {
      if (
        oldPath[1] == closedModalUrl &&
        newPath[1] != closedModalUrl
      ) {
        this.setState({
          viewerIsOpen: true
        })
        // Prevent body scrolling when modal is open
        const page = document.getElementsByTagName('body')[0];
        if (page) {
          page.classList.add('noscroll');
        }
      }
    }
  }

  openModal = (event) => {

    const collectionType = this.props.params.collectionType || 'photos';
    const collection = this.props.params.collection;
    const photoSlug = event.target.attributes.slug.value;
    const albumSlug = event.target.attributes['data-album-slug']?.value;
    
    console.log('openModal called:', {
      collectionType: collectionType,
      collection: collection,
      photoSlug: photoSlug,
      albumSlug: albumSlug
    });
    
    // For photos view, include albumSlug to avoid name collisions
    // URL format: /collections/photos/{albumSlug}/{slug}
    // For albums/people, URL is /collections/{type}/{collection}/{slug}
    let url;
    if (collectionType === 'photos') {
      if (albumSlug) {
        url = `/collections/photos/${albumSlug}/${photoSlug}`;
      } else {
        // Fallback for backward compatibility
        url = `/collections/photos/${photoSlug}`;
      }
    } else {
      url = `/collections/${collectionType}/${collection}/${photoSlug}`;
    }
    
    console.log('Navigating to:', url);
    this.props.navigate(url);
    this.setState({
      viewerIsOpen: true
    })
    // Add listener to detect if the back button was pressed and the modal should be closed
    window.addEventListener('hashchange', this.modalStateTracker, false);
    // Prevent body scrolling when modal is open
    const page = document.getElementsByTagName('body')[0];
    if (page) {
      page.classList.add('noscroll');
    }
  };

  closeModal = () => {

    const collectionType = this.props.params.collectionType || 'photos';
    const collection = this.props.params.collection;
    
    // For photos view, there's no collection name - URL is /collections/photos
    // For albums/people, URL is /collections/{type}/{collection}
    let url;
    if (collectionType === 'photos') {
      url = '/collections/photos';
    } else {
      url = `/collections/${collectionType}/${collection}`;
    }
    
    this.props.navigate(url);
    this.setState({
      viewerIsOpen: false
    })
    // Re-enable body scrolling when modal is closed
    const page = document.getElementsByTagName('body')[0];
    if (page) {
      page.classList.remove('noscroll');
    }
  };

  title = (collectionType) => {
    var titleStr = "Unknown"
    if (collectionType == "albums") {
      titleStr = "Albums"
    }
    else if (collectionType == "people") {
      titleStr = "People"
    }
    else if (collectionType == "photos") {
      titleStr = "Photos"
    }
    return titleStr
  }

  collection = (collectionType, collection) => {
    // Handle photos specially - it doesn't have a collection name
    if (collectionType == "photos") {
      return {
        name: "Photos",
        slug: "photos",
        photos: photos_data || []
      }
    }
    
    let data = {}
    if (collectionType == "albums") {
      data = albums_data
    }
    else if (collectionType == "people") {
      data = people_data
    }
    if (collection in data) {
      return data[collection]
    }
    return {}
  }

  // Helper function to find photo by slug, optionally using albumSlug for disambiguation
  findPhotoIndex = (photos, slug, albumSlug) => {
    if (!albumSlug) {
      // No albumSlug provided - find first match (backward compatibility)
      return photos.findIndex(p => p.slug === slug);
    }
    
    // Try to find exact match with albumSlug first
    const exactMatch = photos.findIndex(p => p.slug === slug && p.albumSlug === albumSlug);
    if (exactMatch !== -1) {
      return exactMatch;
    }
    
    // Fallback: if no exact match, find first with matching slug
    return photos.findIndex(p => p.slug === slug);
  }

  handleSlideChange = (swiper) => {
    const newIndex = swiper.activeIndex;
    // Reset zoom when slide changes
    this._isDragging = false;
    this.setState({
      currentPhotoIndex: newIndex,
      zoomLevel: 1.0,
      panX: 0,
      panY: 0,
      isDragging: false
    });
    
    // Update refs when slide changes - find the new active image
    // Use requestAnimationFrame to ensure slide transition is complete
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const activeSlide = swiper.slides[newIndex];
        if (activeSlide) {
          const img = activeSlide.querySelector('.swiper-image');
          const container = activeSlide.querySelector('.swiper-slide-content');
          if (img && container) {
            this.imageRef = img;
            this.currentImageRef = img;
            this.slideContentRef = container;
            // Trigger recalculation after refs are updated
            if (this.state.showFaceTags) {
              this.forceUpdate();
            }
          }
        }
      });
    });
  }

  togglePhotoInfo = () => {
    this.setState(prevState => {
      const newState = { showPhotoInfo: !prevState.showPhotoInfo };
      // Persist photo info toggle state to localStorage
      localStorage.setItem('fussel_showPhotoInfo', newState.showPhotoInfo.toString());
      return newState;
    });
  }

  handleDownload = (photo) => {
    if (!photo || !photo.originalSrc) return;
    
    // Create a temporary anchor element to trigger download
    const link = document.createElement('a');
    link.href = photo.originalSrc;
    link.download = photo.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  toggleFaceTags = () => {
    this.setState(prevState => {
      const newState = { showFaceTags: !prevState.showFaceTags };
      // Persist face tag toggle state to localStorage
      localStorage.setItem('fussel_showFaceTags', newState.showFaceTags.toString());
      return newState;
    });
  }

  handleImageLoad = (e, photo) => {
    // Store image reference for face tag calculations
    if (photo.slug === this.state.currentPhotoIndex) {
      this.imageRef = e.target;
    }
  }

  getPhotoPeople = (photoSlug) => {
    if (!people_data || !photoSlug) return [];
    const people = [];
    for (const personSlug in people_data) {
      const person = people_data[personSlug];
      if (person.photos && person.photos.some(p => p.slug === photoSlug)) {
        people.push({ name: person.name, slug: personSlug });
      }
    }
    return people;
  }

  // Photos filtering and sorting
  getFilteredPhotos = (photos) => {
    if (!photos) return [];
    if (this.state.selectedPeople.length === 0) {
      return photos;
    }
    return photos.filter(photo => {
      // Check if photo has ALL selected people (AND logic, not OR)
      // Strictly check for faces - must exist, be an array, and have length > 0
      
      // First check: photo must exist
      if (!photo) {
        console.warn('Filter: photo is null/undefined');
        return false;
      }
      
      // Second check: faces property must exist
      if (!photo.hasOwnProperty('faces')) {
        console.warn('Filter: photo missing faces property:', photo.name);
        return false;
      }
      
      // Third check: faces must not be null/undefined
      if (photo.faces === null || photo.faces === undefined) {
        console.warn('Filter: photo has null/undefined faces:', photo.name);
        return false;
      }
      
      // Fourth check: faces must be an array
      if (!Array.isArray(photo.faces)) {
        console.warn('Filter: photo faces is not an array:', photo.name, 'type:', typeof photo.faces, 'value:', photo.faces);
        return false;
      }
      
      // Fifth check: must have at least one face
      if (photo.faces.length === 0) {
        console.warn('Filter: photo has empty faces array:', photo.name, photo.slug);
        return false;
      }
      
      // Get all face slugs in this photo (filter out any undefined/null/invalid slugs)
      const photoFaceSlugs = photo.faces
        .map(face => {
          // Check if face is an object with a slug property
          if (!face || typeof face !== 'object') {
            console.warn('Filter: invalid face object in photo:', photo.name, 'face:', face);
            return null;
          }
          // Handle both face.slug and face being a string slug directly
          const slug = face.slug || (typeof face === 'string' ? face : null);
          return slug;
        })
        .filter(slug => slug !== null && slug !== undefined && slug !== '');
      
      // If no valid face slugs, exclude this photo
      if (photoFaceSlugs.length === 0) {
        console.warn('Filter: photo has faces but no valid slugs:', photo.name, photo.slug, 'faces:', photo.faces);
        return false;
      }
      
      // Check that every selected person is present in the photo
      const hasAllPeople = this.state.selectedPeople.every(slug => photoFaceSlugs.includes(slug));
      
      if (!hasAllPeople) {
        console.log('Filter: photo filtered out (missing people):', photo.name, photo.slug, 'has:', photoFaceSlugs, 'needs:', this.state.selectedPeople);
      }
      
      return hasAllPeople;
    });
  }

  getSortedAndFilteredPhotos = (photos) => {
    let filtered = this.getFilteredPhotos(photos);
    
    // Debug: Check for any photos with empty faces that made it through
    if (this.state.selectedPeople.length > 0) {
      const photosWithEmptyFaces = filtered.filter(p => 
        !p.faces || 
        !Array.isArray(p.faces) || 
        p.faces.length === 0 ||
        (Array.isArray(p.faces) && p.faces.length > 0 && p.faces.every(face => {
          const slug = (face && typeof face === 'object' ? face.slug : (typeof face === 'string' ? face : null));
          return !slug || slug === '';
        }))
      );
      
      if (photosWithEmptyFaces.length > 0) {
        console.error('BUG: Photos with empty/invalid faces passed filter:', 
          photosWithEmptyFaces.map(p => ({
            name: p.name,
            slug: p.slug,
            faces: p.faces,
            facesType: typeof p.faces,
            isArray: Array.isArray(p.faces),
            length: Array.isArray(p.faces) ? p.faces.length : 'N/A'
          }))
        );
      }
    }
    
    // Apply sorting by date only
    return filtered.sort((a, b) => {
      const aVal = a.date ? new Date(a.date).getTime() : 0;
      const bVal = b.date ? new Date(b.date).getTime() : 0;
      
      if (this.state.sortOrder === 'asc') {
        return aVal > bVal ? 1 : (aVal < bVal ? -1 : 0);
      } else { // desc
        return aVal < bVal ? 1 : (aVal > bVal ? -1 : 0);
      }
    });
  }

  handleSortOrderChange = (e) => {
    const newSortOrder = e.target.value;
    this.setState({ sortOrder: newSortOrder });
    localStorage.setItem('fussel_photos_sortOrder', newSortOrder);
  }

  handlePeopleFilterChange = (e) => {
    const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
    this.setState({ selectedPeople: selectedOptions });
  }

  togglePeopleFilter = () => {
    this.setState(prevState => ({ 
      peopleFilterOpen: !prevState.peopleFilterOpen,
      peopleFilterSearch: '' // Clear search when closing
    }));
  }

  handlePeopleFilterSearch = (e) => {
    this.setState({ peopleFilterSearch: e.target.value });
  }

  togglePersonSelection = (personSlug) => {
    this.setState(prevState => {
      const isSelected = prevState.selectedPeople.includes(personSlug);
      const newSelected = isSelected
        ? prevState.selectedPeople.filter(slug => slug !== personSlug)
        : [...prevState.selectedPeople, personSlug];
      return { selectedPeople: newSelected };
    });
  }

  handleClickOutside = (e) => {
    if (this.peopleFilterRef && !this.peopleFilterRef.contains(e.target)) {
      this.setState({ peopleFilterOpen: false, peopleFilterSearch: '' });
    }
  }

  // Zoom handlers
  handleZoomIn = () => {
    this.setState(prevState => ({
      zoomLevel: Math.min(4.0, prevState.zoomLevel + 0.25)
    }));
  }

  handleZoomOut = () => {
    this.setState(prevState => ({
      zoomLevel: Math.max(1.0, prevState.zoomLevel - 0.25)
    }));
  }

  handleResetZoom = () => {
    this._isDragging = false;
    this.setState({
      zoomLevel: 1.0,
      panX: 0,
      panY: 0,
      isDragging: false
    });
  }

  // Keyboard handlers
  handleKeyDown = (e) => {
    if (!this.state.viewerIsOpen) return;

    // Escape key behavior:
    // - If zoomed in: reset zoom
    // - If not zoomed: close modal
    if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      if (this.state.zoomLevel > 1.0) {
        this.handleResetZoom();
      } else {
        this.closeModal();
      }
      return;
    }

    // Arrow keys for panning when zoomed
    if (this.state.zoomLevel > 1.0 && this.currentImageRef) {
      const step = 50;
      let newPanX = this.state.panX;
      let newPanY = this.state.panY;

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        e.stopPropagation();
        const container = this.currentImageRef.parentElement;
        if (container) {
          const containerRect = container.getBoundingClientRect();
          const imgRect = this.currentImageRef.getBoundingClientRect();
          const maxPanX = Math.max(0, (imgRect.width - containerRect.width) / 2);
          // ArrowLeft should reveal left side, so move image right (increase panX)
          newPanX = Math.max(-maxPanX, Math.min(maxPanX, this.state.panX + step));
          this.setState({ panX: newPanX });
        }
        return;
      }
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        e.stopPropagation();
        const container = this.currentImageRef.parentElement;
        if (container) {
          const containerRect = container.getBoundingClientRect();
          const imgRect = this.currentImageRef.getBoundingClientRect();
          const maxPanX = Math.max(0, (imgRect.width - containerRect.width) / 2);
          // ArrowRight should reveal right side, so move image left (decrease panX)
          newPanX = Math.max(-maxPanX, Math.min(maxPanX, this.state.panX - step));
          this.setState({ panX: newPanX });
        }
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        e.stopPropagation();
        const container = this.currentImageRef.parentElement;
        if (container) {
          const containerRect = container.getBoundingClientRect();
          const imgRect = this.currentImageRef.getBoundingClientRect();
          const maxPanY = Math.max(0, (imgRect.height - containerRect.height) / 2);
          // ArrowUp should reveal top, so move image down (increase panY)
          newPanY = Math.max(-maxPanY, Math.min(maxPanY, this.state.panY + step));
          this.setState({ panY: newPanY });
        }
        return;
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        e.stopPropagation();
        const container = this.currentImageRef.parentElement;
        if (container) {
          const containerRect = container.getBoundingClientRect();
          const imgRect = this.currentImageRef.getBoundingClientRect();
          const maxPanY = Math.max(0, (imgRect.height - containerRect.height) / 2);
          // ArrowDown should reveal bottom, so move image up (decrease panY)
          newPanY = Math.max(-maxPanY, Math.min(maxPanY, this.state.panY - step));
          this.setState({ panY: newPanY });
        }
        return;
      }
    }
  }

  // Double-click to zoom
  handleDoubleClick = (e) => {
    // Only handle double-clicks on images
    if (e.target.tagName !== 'IMG') return;
    
    // Don't handle if double-clicking on a face tag label
    if (e.target.closest('.face-tag-label')) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    if (this.state.zoomLevel > 1.0) {
      // If zoomed, reset to normal (fit to screen)
      this.handleResetZoom();
    } else {
      // If not zoomed, zoom to 100% (2.0x)
      this.setState({
        zoomLevel: 2.0,
        panX: 0,
        panY: 0
      });
    }
  }

  // Mouse drag handlers - use pointer events for better compatibility
  handlePointerDown = (e) => {
    console.log('handlePointerDown ENTRY', { 
      zoomLevel: this.state.zoomLevel, 
      target: e.target.tagName, 
      targetClass: e.target.className,
      isZoomed: this.state.zoomLevel > 1.0,
      currentTarget: e.currentTarget.className
    });
    
    // Only handle when zoomed
    if (this.state.zoomLevel <= 1.0) {
      console.log('handlePointerDown: zoomLevel too low, returning');
      return;
    }
    
    // Find the image - could be target or within currentTarget
    let imgElement = e.target;
    if (e.target.tagName !== 'IMG') {
      // If clicking on container, find the image
      imgElement = e.currentTarget.querySelector('.swiper-image');
      if (!imgElement) {
        console.log('handlePointerDown: no image found, returning', e.target.tagName);
        return;
      }
    }
    
    // Don't handle if clicking on a face tag label (those should navigate)
    if (e.target.closest('.face-tag-label')) {
      console.log('handlePointerDown: clicked on face tag, returning');
      return;
    }

    console.log('handlePointerDown PROCEEDING', { zoomLevel: this.state.zoomLevel, imgElement: imgElement.tagName });
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    
    // Disable Swiper interactions when panning
    if (this.swiperRef) {
      this.swiperRef.allowTouchMove = false;
      this.swiperRef.simulateTouch = false;
      if (this.swiperRef.keyboard) {
        this.swiperRef.keyboard.disable();
      }
      // Disable Swiper's mouse event handling
      if (this.swiperRef.touchEventsData) {
        this.swiperRef.touchEventsData.touchesStart = {};
        this.swiperRef.touchEventsData.touchesCurrent = {};
      }
    }
    
    // Set synchronous flag immediately (before async setState)
    this._isDragging = true;
    this.dragStartX = e.clientX;
    this.dragStartY = e.clientY;
    this.dragStartPanX = this.state.panX;
    this.dragStartPanY = this.state.panY;
    this.currentImageRef = imgElement;
    
    // Update state (async)
    this.setState({ isDragging: true });

    // Use capture phase to catch events before Swiper
    document.addEventListener('pointermove', this.handlePointerMove, { capture: true, passive: false });
    document.addEventListener('pointerup', this.handlePointerUp, { capture: true });
    document.addEventListener('mousemove', this.handleMouseMove, { capture: true, passive: false });
    document.addEventListener('mouseup', this.handleMouseUp, { capture: true });
  }

  handlePointerMove = (e) => {
    // Use synchronous flag since setState is async
    if (!this._isDragging || this.state.zoomLevel <= 1.0) {
      return;
    }
    
    if (!this.currentImageRef) {
      const currentSlide = document.querySelector('.swiper-slide-active .swiper-image');
      if (currentSlide) {
        this.currentImageRef = currentSlide;
      } else {
        return;
      }
    }

    console.log('handlePointerMove called', { isDragging: this._isDragging, zoomLevel: this.state.zoomLevel });
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    
    const container = this.currentImageRef.parentElement;
    if (!container) return;

    const deltaX = e.clientX - this.dragStartX;
    const deltaY = e.clientY - this.dragStartY;
    
    const containerRect = container.getBoundingClientRect();
    const imgRect = this.currentImageRef.getBoundingClientRect();
    
    const zoomedWidth = imgRect.width;
    const zoomedHeight = imgRect.height;
    const maxPanX = Math.max(0, (zoomedWidth - containerRect.width) / 2);
    const maxPanY = Math.max(0, (zoomedHeight - containerRect.height) / 2);

    const newPanX = Math.max(-maxPanX, Math.min(maxPanX, this.dragStartPanX + deltaX));
    const newPanY = Math.max(-maxPanY, Math.min(maxPanY, this.dragStartPanY + deltaY));

    this.setState({ panX: newPanX, panY: newPanY });
  }

  handlePointerUp = () => {
    if (this._isDragging || this.state.isDragging) {
      this._isDragging = false;
      this.setState({ isDragging: false });
      
      if (this.swiperRef) {
        if (this.state.zoomLevel === 1.0) {
          this.swiperRef.allowTouchMove = true;
          this.swiperRef.simulateTouch = true;
          if (this.swiperRef.keyboard) {
            this.swiperRef.keyboard.enable();
          }
        }
      }
      
      document.removeEventListener('pointermove', this.handlePointerMove, { capture: true });
      document.removeEventListener('pointerup', this.handlePointerUp, { capture: true });
      document.removeEventListener('mousemove', this.handleMouseMove, { capture: true });
      document.removeEventListener('mouseup', this.handleMouseUp, { capture: true });
    }
  }

  handleMouseMove = (e) => {
    // Use synchronous flag since setState is async
    if (!this._isDragging || this.state.zoomLevel <= 1.0) {
      return;
    }
    
    if (!this.currentImageRef) {
      // Try to find the current image if ref is not set
      const currentSlide = document.querySelector('.swiper-slide-active .swiper-image');
      if (currentSlide) {
        this.currentImageRef = currentSlide;
      } else {
        return;
      }
    }

    console.log('handleMouseMove called', { isDragging: this._isDragging, zoomLevel: this.state.zoomLevel, deltaX: e.clientX - this.dragStartX, deltaY: e.clientY - this.dragStartY });
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    
    const container = this.currentImageRef.parentElement;
    if (!container) return;

    const deltaX = e.clientX - this.dragStartX;
    const deltaY = e.clientY - this.dragStartY;
    
    const containerRect = container.getBoundingClientRect();
    const imgRect = this.currentImageRef.getBoundingClientRect();
    
    // Calculate max pan based on zoomed image size vs container
    const zoomedWidth = imgRect.width;
    const zoomedHeight = imgRect.height;
    const maxPanX = Math.max(0, (zoomedWidth - containerRect.width) / 2);
    const maxPanY = Math.max(0, (zoomedHeight - containerRect.height) / 2);

    const newPanX = Math.max(-maxPanX, Math.min(maxPanX, this.dragStartPanX + deltaX));
    const newPanY = Math.max(-maxPanY, Math.min(maxPanY, this.dragStartPanY + deltaY));

    this.setState({ panX: newPanX, panY: newPanY });
  }

  handleMouseUp = () => {
    if (this._isDragging || this.state.isDragging) {
      this._isDragging = false;
      this.setState({ isDragging: false });
      
      // Re-enable Swiper interactions when not zoomed
      if (this.swiperRef) {
        if (this.state.zoomLevel === 1.0) {
          this.swiperRef.allowTouchMove = true;
          this.swiperRef.simulateTouch = true;
          if (this.swiperRef.keyboard) {
            this.swiperRef.keyboard.enable();
          }
        }
      }
      
      document.removeEventListener('mousemove', this.handleMouseMove, { capture: true });
      document.removeEventListener('mouseup', this.handleMouseUp, { capture: true });
    }
  }

  componentDidMount() {
    window.addEventListener('keydown', this.handleKeyDown, true);
    // Close people filter dropdown when clicking outside
    document.addEventListener('click', this.handleClickOutside);
  }
  
  componentDidUpdate(prevProps, prevState) {
    // Disable/enable Swiper keyboard and touch based on zoom level
    if (this.swiperRef) {
      if (this.swiperRef.keyboard) {
        if (this.state.zoomLevel > 1.0 && prevState.zoomLevel <= 1.0) {
          // Just zoomed in - disable Swiper keyboard
          this.swiperRef.keyboard.disable();
        } else if (this.state.zoomLevel <= 1.0 && prevState.zoomLevel > 1.0) {
          // Just zoomed out - enable Swiper keyboard
          this.swiperRef.keyboard.enable();
        }
      }
      // Update allowTouchMove dynamically
      if (this.state.zoomLevel > 1.0) {
        this.swiperRef.allowTouchMove = false;
      } else {
        this.swiperRef.allowTouchMove = true;
      }
    }
    
    // Update photo index if URL changed (e.g., clicking a photo in gallery)
    if (this.swiperRef && this.props.params.image && 
        (prevProps.params.image !== this.props.params.image || 
         prevState.selectedPeople !== this.state.selectedPeople ||
         prevState.sortOrder !== this.state.sortOrder)) {
      // Recalculate displayPhotos with current filters/sort
      const collectionType = this.props.params.collectionType || 'photos';
      const collection = this.props.params.collection || 'photos';
      let collection_data = this.collection(collectionType, collection);
      const isPhotos = collectionType === 'photos';
      let displayPhotos = collection_data["photos"] || [];
      if (isPhotos) {
        displayPhotos = this.getSortedAndFilteredPhotos(displayPhotos);
      }
      
      // Use albumSlug from URL params if available for disambiguation
      const albumSlug = this.props.params.albumSlug;
      const photoIndex = this.findPhotoIndex(displayPhotos, this.props.params.image, albumSlug);
      if (photoIndex !== -1 && photoIndex !== this.state.currentPhotoIndex) {
        this.setState({ currentPhotoIndex: photoIndex });
        this.swiperRef.slideTo(photoIndex);
      }
    }
    
    // Update scroll position when content changes (e.g., filters applied, photos loaded)
    const currentCollectionType = this.props.params.collectionType || 'photos';
  }

  componentWillUnmount() {
    window.removeEventListener('keydown', this.handleKeyDown, true);
    document.removeEventListener('click', this.handleClickOutside);
    // Clean up mouse event listeners
    document.removeEventListener('mousemove', this.handleMouseMove, { capture: true });
    document.removeEventListener('mouseup', this.handleMouseUp, { capture: true });
  }

  getHeaderHeight = () => {
    let height = 0;
    // Always query the DOM directly since refs might not be ready during render
    const header = document.querySelector('.hero.is-small');
    if (header) {
      const headerRect = header.getBoundingClientRect();
      height += headerRect.height;
    } else if (this.headerRef && this.headerRef.current) {
      const headerRect = this.headerRef.current.getBoundingClientRect();
      height += headerRect.height;
    }
    // Also account for photos-controls if it exists
    const photosControls = document.querySelector('.photos-controls');
    if (photosControls) {
      const controlsRect = photosControls.getBoundingClientRect();
      height += controlsRect.height + 20; // 20px is the margin-bottom
    }
    return height;
  }

  render() {
    const collectionType = this.props.params.collectionType || 'photos'; // Default to photos if not in params
    const collection = this.props.params.collection;
    let collection_data = this.collection(collectionType, collection)
    const isPhotos = collectionType === 'photos';
    
    // Store in instance for use in other methods
    this._collectionType = collectionType;
    this._collection = collection;
    
    // For photos, apply filtering and sorting
    let displayPhotos = collection_data["photos"] || [];
    if (isPhotos) {
      displayPhotos = this.getSortedAndFilteredPhotos(displayPhotos);
    }
    
    const totalPhotos = displayPhotos.length;
    const currentPhoto = displayPhotos[this.state.currentPhotoIndex] || null;
    const photoPeople = currentPhoto ? this.getPhotoPeople(currentPhoto.slug) : [];
    const allowDownload = site_data.allow_download;
    
    // Debug: Log displayPhotos when filtering is active
    if (isPhotos && this.state.selectedPeople.length > 0) {
      console.log('Gallery render - displayPhotos:', {
        length: displayPhotos.length,
        selectedPeople: this.state.selectedPeople,
        photos: displayPhotos.map(p => ({
          name: p.name,
          slug: p.slug,
          facesCount: Array.isArray(p.faces) ? p.faces.length : 'not-array',
          faces: p.faces
        }))
      });
    }
    
    return (
      <div className="container" >
        <section className="hero is-small" ref={this.headerRef}>
          <div className="hero-body">
            <nav className="breadcrumb" aria-label="breadcrumbs">
              <ul>
                {isPhotos ? (
                  // For Photos view, just show the title without subheading
                  <li className="is-active">
                    <i className="fas fa-images fa-lg"></i>
                    <span className="title is-5">&nbsp;&nbsp;{this.title(collectionType)}</span>
                  </li>
                ) : (
                  // For Albums/People, show the collection type and subheading
                  <>
                    <li>
                      <i className="fas fa-book fa-lg"></i>
                      <Link className="title is-5" to={"/collections/" + collectionType}>&nbsp;&nbsp;{this.title(collectionType)}</Link>
                    </li>
                    <li className="is-active">
                      <a className="title is-5">{collection_data["name"]}</a>
                    </li>
                  </>
                )}
              </ul>
            </nav>
          </div>
        </section>
        {isPhotos && (
          <div className="photos-controls field is-grouped is-grouped-multiline" style={{ marginBottom: '20px' }}>
            <div className="field">
              <label className="label" style={{ fontSize: '0.85rem', marginBottom: '0.25rem' }}>Date order</label>
              <div className="control">
                <div className="select is-small">
                  <select value={this.state.sortOrder} onChange={this.handleSortOrderChange}>
                    <option value="desc">Newest first</option>
                    <option value="asc">Oldest first</option>
                  </select>
                </div>
              </div>
            </div>
            {people_data && Object.keys(people_data).length > 0 && (
              <div className="field">
                <label className="label" style={{ fontSize: '0.85rem', marginBottom: '0.25rem' }}>Filter by people</label>
                <div className="control">
                  <div 
                    ref={el => this.peopleFilterRef = el}
                    className="people-filter-dropdown" 
                    style={{ position: 'relative', minWidth: '200px' }}
                  >
                    <button
                      type="button"
                      className="people-filter-trigger"
                      onClick={(e) => {
                        e.stopPropagation();
                        this.togglePeopleFilter();
                      }}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        padding: '0.375em 2.5em 0.375em 0.625em',
                        fontSize: '0.875rem',
                        border: '1px solid rgba(0, 0, 0, 0.2)',
                        borderRadius: '4px',
                        backgroundColor: 'transparent',
                        color: 'inherit',
                        cursor: 'pointer',
                        minHeight: '2.25em',
                        position: 'relative'
                      }}
                    >
                      {this.state.selectedPeople.length === 0 
                        ? 'Select people...'
                        : `${this.state.selectedPeople.length} ${this.state.selectedPeople.length === 1 ? 'person' : 'people'} selected`
                      }
                      <span style={{ position: 'absolute', right: '0.625em', top: '50%', transform: 'translateY(-50%)' }}>
                        <i className={`fas fa-chevron-${this.state.peopleFilterOpen ? 'up' : 'down'}`} style={{ fontSize: '0.75rem' }}></i>
                      </span>
                    </button>
                    {this.state.peopleFilterOpen && (
                      <div 
                        className="people-filter-dropdown-menu" 
                        onClick={(e) => e.stopPropagation()}
                        style={{
                        position: 'absolute',
                        top: '100%',
                        left: 0,
                        right: 0,
                        marginTop: '4px',
                        backgroundColor: '#fff',
                        border: '1px solid #dbdbdb',
                        borderRadius: '4px',
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                        zIndex: 1000,
                        maxHeight: '300px',
                        display: 'flex',
                        flexDirection: 'column'
                      }}>
                        <div style={{ padding: '8px', borderBottom: '1px solid #dbdbdb' }}>
                          <input
                            type="text"
                            className="input is-small"
                            placeholder="Search people..."
                            value={this.state.peopleFilterSearch}
                            onChange={this.handlePeopleFilterSearch}
                            style={{
                              width: '100%',
                              fontSize: '0.875rem',
                              padding: '0.375em 0.625em'
                            }}
                            autoFocus
                          />
                        </div>
                        <div style={{ overflowY: 'auto', maxHeight: '250px' }}>
                          {(() => {
                            // Get all people, sorted alphabetically
                            const allPeople = Object.keys(people_data)
                              .map(slug => ({ slug, name: people_data[slug].name }))
                              .sort((a, b) => a.name.localeCompare(b.name));
                            
                            // Filter by search query
                            const filtered = this.state.peopleFilterSearch
                              ? allPeople.filter(p => 
                                  p.name.toLowerCase().includes(this.state.peopleFilterSearch.toLowerCase())
                                )
                              : allPeople;
                            
                            // Show selected first, then others
                            const selected = filtered.filter(p => this.state.selectedPeople.includes(p.slug));
                            const unselected = filtered.filter(p => !this.state.selectedPeople.includes(p.slug));
                            const sorted = [...selected, ...unselected];
                            
                            return sorted.map(({ slug, name }) => (
                              <div
                                key={slug}
                                onClick={() => this.togglePersonSelection(slug)}
                                style={{
                                  padding: '8px 12px',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '8px',
                                  backgroundColor: this.state.selectedPeople.includes(slug) ? 'rgba(0, 0, 0, 0.05)' : 'transparent',
                                  transition: 'background-color 0.15s'
                                }}
                                onMouseEnter={(e) => {
                                  if (!this.state.selectedPeople.includes(slug)) {
                                    e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.05)';
                                  }
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.backgroundColor = this.state.selectedPeople.includes(slug) ? 'rgba(0, 0, 0, 0.05)' : 'transparent';
                                }}
                              >
                                <input
                                  type="checkbox"
                                  checked={this.state.selectedPeople.includes(slug)}
                                  onChange={() => {}} // Handled by parent onClick
                                  style={{ cursor: 'pointer' }}
                                />
                                <span>{name}</span>
                              </div>
                            ));
                          })()}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            {this.state.selectedPeople.length > 0 && (
              <div className="field is-align-self-flex-end">
                <div className="control">
                  <button 
                    className="button is-small is-light"
                    onClick={() => this.setState({ selectedPeople: [] })}
                  >
                    Clear filter
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
        <div 
          ref={this.galleryContainerRef}
          style={{ position: 'relative' }}
        >
          <MasonryPhotoAlbum
            key={`gallery-${this.state.selectedPeople.join(',')}-${this.state.sortOrder}-${displayPhotos.length}`}
            photos={displayPhotos.map((image, i) => {
              // Create a new object to ensure reference changes
              return {
                src: image.srcSet["(500, 500)w"] || image.src,
                width: image.width,
                height: image.height,
                alt: image.name,
                key: image.slug || i,
                // Store original image data for onClick handler
                originalImage: image
              };
            })}
            columns={(containerWidth) => {
              if (containerWidth < 600) return 1;
              if (containerWidth < 900) return 2;
              if (containerWidth < 1200) return 3;
              if (containerWidth < 1500) return 4;
              return 5;
            }}
            spacing={10}
            padding={0}
            onClick={({ index, photo }) => {
              console.log('Photo clicked:', {
                index: index,
                photoObject: photo,
                hasOriginalImage: !!photo.originalImage,
                photoSrc: photo.src,
                photoKey: photo.key
              });
              
              // Verify the photo matches what we expect
              const clickedPhoto = photo.originalImage;
              if (!clickedPhoto) {
                console.error('No originalImage found in photo object!', photo);
                return;
              }
              
              const expectedPhoto = displayPhotos[index];
              
              console.log('Photo comparison:', {
                clickedSlug: clickedPhoto.slug,
                clickedName: clickedPhoto.name,
                clickedSrc: clickedPhoto.src,
                expectedSlug: expectedPhoto?.slug,
                expectedName: expectedPhoto?.name,
                expectedSrc: expectedPhoto?.src,
                index: index,
                displayPhotosLength: displayPhotos.length
              });
              
              // Debug: log if there's a mismatch
              if (expectedPhoto && clickedPhoto.slug !== expectedPhoto.slug) {
                console.warn('Photo mismatch detected:', {
                  index: index,
                  clickedSlug: clickedPhoto.slug,
                  clickedName: clickedPhoto.name,
                  expectedSlug: expectedPhoto.slug,
                  expectedName: expectedPhoto.name
                });
              }
              
              // Create a synthetic event for openModal using the clicked photo's slug and albumSlug
              const syntheticEvent = {
                target: {
                  attributes: {
                    slug: { value: clickedPhoto.slug },
                    'data-album-slug': clickedPhoto.albumSlug ? { value: clickedPhoto.albumSlug } : undefined
                  }
                }
              };
              
              console.log('Opening modal with slug:', clickedPhoto.slug, 'albumSlug:', clickedPhoto.albumSlug);
              this.openModal(syntheticEvent);
            }}
            renderPhoto={({ imageProps, photo, index }) => {
              // Use the index from react-photo-album, which matches displayPhotos array order
              // react-photo-album calculates width/height for masonry - don't override
              // Merge className to ensure both react-photo-album's class and ours are applied
              const className = imageProps.className 
                ? `${imageProps.className} gallery-image`
                : 'gallery-image';
              
              // Verify the photo data matches what we expect
              const originalImage = photo.originalImage;
              const expectedPhoto = displayPhotos[index];
              
              if (originalImage && expectedPhoto && originalImage.slug !== expectedPhoto.slug) {
                console.warn('Render mismatch:', {
                  index: index,
                  renderedSlug: originalImage.slug,
                  renderedName: originalImage.name,
                  expectedSlug: expectedPhoto.slug,
                  expectedName: expectedPhoto.name,
                  renderedSrc: photo.src,
                  expectedSrc: expectedPhoto.srcSet?.["(500, 500)w"] || expectedPhoto.src
                });
              }
              
              // Create a new props object to ensure data-photo-index is set
              const finalProps = {
                ...imageProps,
                className: className,
                'data-photo-index': String(index),
                'data-photo-slug': originalImage?.slug || '',
                'data-album-slug': originalImage?.albumSlug || '',
                draggable: allowDownload,
                onContextMenu: allowDownload ? undefined : (e) => e.preventDefault()
              };
              
              return (
                <img {...finalProps} />
              );
            }}
          />
        </div>
        {isPhotos && (() => {
          // Calculate header height once per render to ensure consistency
          const headerHeight = this.getHeaderHeight();
          return (
            <TimelineScrollbar
              photos={displayPhotos}
              sortOrder={this.state.sortOrder}
              scrollContainerRef={this.galleryContainerRef}
              headerHeight={headerHeight}
            />
          );
        })()}
        <Modal
          isOpen={this.state.viewerIsOpen}
          onRequestClose={this.closeModal}
          preventScroll={true}
          
          style={{
            overlay: {
              backgroundColor: 'rgba(0, 0, 0, 0.85)',
              zIndex: 9999
            },
            content: {
              inset: '10px',
              padding: '10px',
              backgroundColor: 'rgba(0, 0, 0, 1)',
              border: 'none',
              outline: 'none',
              zIndex: 10000
            }
          }}
        >
          <button className="button is-text modal-close-button" onClick={this.closeModal} >
            <span className="icon is-small">
              <i className="fas fa-times"></i>
            </span>
          </button>
          <div className="modal-info-bar">
            <span className="photo-counter">{this.state.currentPhotoIndex + 1} / {totalPhotos}</span>
            <button className="button is-text modal-info-button" onClick={this.handleZoomIn} title="Zoom in (+)">
              <span className="icon is-small">
                <i className="fas fa-search-plus"></i>
              </span>
            </button>
            <button className="button is-text modal-info-button" onClick={this.handleZoomOut} title="Zoom out (-)">
              <span className="icon is-small">
                <i className="fas fa-search-minus"></i>
              </span>
            </button>
            {this.state.zoomLevel > 1.0 && (
              <button className="button is-text modal-info-button" onClick={this.handleResetZoom} title="Reset zoom (Escape)">
                <span className="icon is-small">
                  <i className="fas fa-compress"></i>
                </span>
              </button>
            )}
            {currentPhoto && currentPhoto.faces && currentPhoto.faces.length > 0 && (
              <button className={`button is-text modal-info-button ${this.state.showFaceTags ? 'is-active' : ''}`} onClick={this.toggleFaceTags} title="Toggle face tags">
                <span className="icon is-small">
                  <i className="fas fa-user-friends"></i>
                </span>
              </button>
            )}
            {site_data.allow_download && currentPhoto && (
              <button className="button is-text modal-info-button" onClick={() => this.handleDownload(currentPhoto)} title="Download original photo">
                <span className="icon is-small">
                  <i className="fas fa-download"></i>
                </span>
              </button>
            )}
            <button className="button is-text modal-info-button" onClick={this.togglePhotoInfo}>
              <span className="icon is-small">
                <i className="fas fa-info-circle"></i>
              </span>
            </button>
          </div>
          {this.state.showPhotoInfo && currentPhoto && (
            <div className="photo-info-panel">
              <div className="photo-info-content">
                <p className="photo-info-item">
                  <span className="photo-info-label">File:</span>
                  <span className="photo-info-value">{currentPhoto.name}</span>
                </p>
                {currentPhoto.width && currentPhoto.height && (
                  <p className="photo-info-item">
                    <span className="photo-info-label">Dimensions:</span>
                    <span className="photo-info-value">{currentPhoto.width} × {currentPhoto.height}</span>
                  </p>
                )}
                {site_data.albums_enabled && currentPhoto.albumSlug && albums_data && albums_data[currentPhoto.albumSlug] && (
                  <div className="photo-info-item">
                    <span className="photo-info-label">Album:</span>
                    <span className="photo-info-value">
                      <a 
                        className="photo-info-person-link"
                        href={`#/collections/albums/${currentPhoto.albumSlug}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          // Close modal first, then navigate after a brief delay to ensure cleanup
                          this.closeModal();
                          setTimeout(() => {
                            this.props.navigate(`/collections/albums/${currentPhoto.albumSlug}`);
                          }, 100);
                        }}
                      >
                        {albums_data[currentPhoto.albumSlug].name}
                      </a>
                    </span>
                  </div>
                )}
                {photoPeople.length > 0 && (
                  <div className="photo-info-item">
                    <span className="photo-info-label">People:</span>
                    <span className="photo-info-value">
                      {photoPeople.map((person, idx) => (
                        <a 
                          key={person.slug}
                          className="photo-info-person-link"
                          href={`#/collections/people/${person.slug}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            e.preventDefault();
                            // Close modal first, then navigate after a brief delay to ensure cleanup
                            this.closeModal();
                            setTimeout(() => {
                              this.props.navigate(`/collections/people/${person.slug}`);
                            }, 100);
                          }}
                        >
                          {person.name}
                          {idx < photoPeople.length - 1 ? ', ' : ''}
                        </a>
                      ))}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
          <Swiper
            slidesPerView={1}
            preloadImages={false}
            onSlideChange={this.handleSlideChange}
            onSwiper={(swiper) => { 
              this.swiperRef = swiper;
              // Set initial photo index if opening from URL hash
              // Use displayPhotos which is already filtered and sorted
              if (this.props.params.image) {
                // Use albumSlug from URL params if available for disambiguation
                const albumSlug = this.props.params.albumSlug;
                console.log('onSwiper called with image param:', this.props.params.image, 'albumSlug:', albumSlug);
                console.log('displayPhotos at onSwiper:', {
                  length: displayPhotos.length,
                  firstFew: displayPhotos.slice(0, 5).map(p => ({ slug: p.slug, name: p.name, albumSlug: p.albumSlug })),
                  lookingFor: this.props.params.image
                });
                
                const photoIndex = this.findPhotoIndex(displayPhotos, this.props.params.image, albumSlug);
                console.log('Found photo at index:', photoIndex);
                
                if (photoIndex !== -1) {
                  console.log('Opening modal to photo:', {
                    slug: this.props.params.image,
                    albumSlug: albumSlug,
                    index: photoIndex,
                    photoName: displayPhotos[photoIndex].name,
                    photoAlbumSlug: displayPhotos[photoIndex].albumSlug,
                    totalPhotos: displayPhotos.length,
                    firstFewSlugs: displayPhotos.slice(0, 3).map(p => ({ slug: p.slug, albumSlug: p.albumSlug }))
                  });
                  this.setState({ currentPhotoIndex: photoIndex });
                  // Use requestAnimationFrame to ensure DOM is ready
                  requestAnimationFrame(() => {
                    swiper.slideTo(photoIndex);
                    console.log('Called swiper.slideTo with index:', photoIndex);
                  });
                } else {
                  // Photo not found in filtered list - might be filtered out
                  console.warn('Photo not found in filtered displayPhotos:', this.props.params.image, 'albumSlug:', albumSlug, 'Available slugs (first 5):', displayPhotos.slice(0, 5).map(p => ({ slug: p.slug, albumSlug: p.albumSlug })));
                }
              }
            }}
            navigation={{
              enabled: this.state.zoomLevel === 1.0,
            }}
            keyboard={{ 
              enabled: this.state.zoomLevel === 1.0,
            }}
            allowTouchMove={this.state.zoomLevel === 1.0}
            simulateTouch={this.state.zoomLevel === 1.0}
            pagination={{ clickable: true, }}
            hashNavigation={{
              watchState: true,
            }}
            modules={[Keyboard, HashNavigation, Pagination, Navigation]}
            className={`swiper ${this.state.zoomLevel > 1.0 ? 'swiper-zoomed' : ''}`}
          >
            {
              displayPhotos.map(x => {
                const collectionType = this.props.params.collectionType || 'photos';
                const collection = this.props.params.collection;
                
                // For photos view, include albumSlug to avoid name collisions
                // URL format: /collections/photos/{albumSlug}/{slug}
                // For albums/people, URL is /collections/{type}/{collection}/{slug}
                let hashUrl;
                if (collectionType === 'photos') {
                  if (x.albumSlug) {
                    hashUrl = `/collections/photos/${x.albumSlug}/${x.slug}`;
                  } else {
                    // Fallback for backward compatibility
                    hashUrl = `/collections/photos/${x.slug}`;
                  }
                } else {
                  hashUrl = `/collections/${collectionType}/${collection}/${x.slug}`;
                }
                
                return (
                  <SwiperSlide key={x.slug} slug={x.slug} data-hash={hashUrl}>
                  <div 
                    className="swiper-slide-content"
                    onPointerDown={this.state.zoomLevel > 1.0 && x.slug === currentPhoto?.slug ? this.handlePointerDown : undefined}
                    onMouseDown={this.state.zoomLevel > 1.0 && x.slug === currentPhoto?.slug ? this.handlePointerDown : undefined}
                    style={this.state.zoomLevel > 1.0 && x.slug === currentPhoto?.slug ? { cursor: 'grab' } : undefined}
                  >
                    <img 
                      title={x.name} 
                      src={x.src}
                      className={`swiper-image ${this.state.zoomLevel > 1.0 && x.slug === currentPhoto?.slug ? 'zoomed' : ''}`}
                      data-slug={x.slug}
                      draggable={allowDownload && this.state.zoomLevel === 1.0}
                      onContextMenu={allowDownload ? undefined : (e) => e.preventDefault()}
                      onDoubleClick={this.handleDoubleClick}
                      style={this.state.zoomLevel > 1.0 && x.slug === currentPhoto?.slug ? {
                        transform: `translate(calc(-50% + ${this.state.panX}px), calc(-50% + ${this.state.panY}px)) scale(${this.state.zoomLevel})`,
                        transition: this._isDragging ? 'none' : 'transform 0.2s ease'
                      } : undefined}
                      ref={(imgEl) => {
                        // Attach native event listeners directly to bypass React/Swiper
                        if (imgEl && this.state.zoomLevel > 1.0 && x.slug === currentPhoto?.slug) {
                          // Remove old listeners if they exist
                          if (imgEl._panHandler) {
                            imgEl.removeEventListener('mousedown', imgEl._panHandler);
                            imgEl.removeEventListener('pointerdown', imgEl._panHandler);
                          }
                          // Create new handler
                          imgEl._panHandler = (e) => {
                            console.log('Native handler called', { zoomLevel: this.state.zoomLevel });
                            this.handlePointerDown(e);
                          };
                          imgEl.addEventListener('mousedown', imgEl._panHandler, { capture: true });
                          imgEl.addEventListener('pointerdown', imgEl._panHandler, { capture: true });
                          this.currentImageRef = imgEl;
                        }
                      }}
                      onLoad={(e) => {
                        // Update refs for the currently active photo when its image loads
                        // Check both slug and index to ensure we're updating the right image
                        const currentPhoto = displayPhotos[this.state.currentPhotoIndex];
                        if (currentPhoto && x.slug === currentPhoto.slug) {
                          this.imageRef = e.target;
                          this.currentImageRef = e.target;
                          this.slideContentRef = e.target.parentElement;
                          // Force update when image loads so FaceTagOverlay can recalculate
                          // Use multiple requestAnimationFrame calls and a small delay to ensure image is fully rendered and dimensions are stable
                          if (this.state.showFaceTags) {
                            requestAnimationFrame(() => {
                              requestAnimationFrame(() => {
                                // Additional delay to ensure browser has finished layout calculations
                                setTimeout(() => {
                                  this.forceUpdate();
                                }, 50);
                              });
                            });
                          }
                        }
                      }}
                    />
                    {this.state.showFaceTags && this.state.zoomLevel === 1.0 && x.faces && x.faces.length > 0 && x.slug === (displayPhotos[this.state.currentPhotoIndex]?.slug) && this.imageRef && this.slideContentRef && 
                     this.imageRef.complete && this.imageRef.naturalWidth > 0 && this.imageRef.naturalHeight > 0 && (
                      <FaceTagOverlay 
                        key={x.slug}
                        faces={x.faces} 
                        imageRef={this.imageRef}
                        containerRef={this.slideContentRef}
                        originalWidth={x.width} 
                        originalHeight={x.height}
                        navigate={this.props.navigate}
                        onCloseModal={this.closeModal}
                      />
                    )}
                  </div>
                  </SwiperSlide>
                );
              })
            }
          </Swiper>
        </Modal>
      </div>
    );
  }
}

export default withRouter(Collection)