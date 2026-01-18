import React, { Component } from "react";
import Masonry, { ResponsiveMasonry } from "react-responsive-masonry"
import withRouter from './withRouter';
import { albums_data } from "../_gallery/albums_data.js"
import { people_data } from "../_gallery/people_data.js"
import { site_data } from "../_gallery/site_data.js"
import { Keyboard, Pagination, HashNavigation, Navigation } from "swiper/modules";
import { Swiper, SwiperSlide } from 'swiper/react';
import 'swiper/css';
import 'swiper/css/navigation'
import 'swiper/css/pagination'
import Modal from 'react-modal';

import { Link } from "react-router-dom";
import "./Collection.css";

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
    const { faces, imageRef, containerRef, originalWidth, originalHeight, navigate } = this.props;
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
      isDragging: false
    };
    this.swiperRef = null;
    this.dragStartX = 0;
    this.dragStartY = 0;
    this.dragStartPanX = 0;
    this.dragStartPanY = 0;
    this.currentImageRef = null;
    this._isDragging = false; // Synchronous flag for dragging state
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

    var closedModalUrl = "/collections/" + this.props.params.collectionType + "/" + this.props.params.collection

    if (this.state.viewerIsOpen) {
      if (
        oldPath[1] != closedModalUrl &&
        newPath[1] == closedModalUrl
      ) {
        this.setState({
          viewerIsOpen: false
        })
        // var page = document.getElementsByTagName('body')[0];
        // page.classList.remove('noscroll');
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
        // this.props.navigate("/collections/" + this.props.params.collectionType + "/" + this.props.params.collection + "/" + event.target.attributes.slug.value);
        // var page = document.getElementsByTagName('body')[0];
        // page.classList.add('noscroll');
      }
    }
  }

  openModal = (event) => {

    this.props.navigate("/collections/" + this.props.params.collectionType + "/" + this.props.params.collection + "/" + event.target.attributes.slug.value);
    this.setState({
      viewerIsOpen: true
    })
    // Add listener to detect if the back button was pressed and the modal should be closed
    window.addEventListener('hashchange', this.modalStateTracker, false);
    // var page = document.getElementsByTagName('body')[0];
    // page.classList.add('noscroll');
  };

  closeModal = () => {

    this.props.navigate("/collections/" + this.props.params.collectionType + "/" + this.props.params.collection);
    this.setState({
      viewerIsOpen: false
    })
    // var page = document.getElementsByTagName('body')[0];
    // page.classList.remove('noscroll');
  };

  title = (collectionType) => {
    var titleStr = "Unknown"
    if (collectionType == "albums") {
      titleStr = "Albums"
    }
    else if (collectionType == "people") {
      titleStr = "People"
    }
    return titleStr
  }

  collection = (collectionType, collection) => {
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

    // Escape to reset zoom
    if (e.key === 'Escape' && this.state.zoomLevel > 1.0) {
      e.preventDefault();
      e.stopPropagation();
      this.handleResetZoom();
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
  }

  componentWillUnmount() {
    window.removeEventListener('keydown', this.handleKeyDown, true);
    // Clean up mouse event listeners
    document.removeEventListener('mousemove', this.handleMouseMove, { capture: true });
    document.removeEventListener('mouseup', this.handleMouseUp, { capture: true });
  }

  render() {
    let collection_data = this.collection(this.props.params.collectionType, this.props.params.collection)
    const totalPhotos = collection_data["photos"] ? collection_data["photos"].length : 0;
    const currentPhoto = collection_data["photos"] ? collection_data["photos"][this.state.currentPhotoIndex] : null;
    const photoPeople = currentPhoto ? this.getPhotoPeople(currentPhoto.slug) : [];
    const allowDownload = site_data.allow_download;
    return (
      <div className="container" >
        <section className="hero is-small">
          <div className="hero-body">
            <nav className="breadcrumb" aria-label="breadcrumbs">
              <ul>
                <li>
                  <i className="fas fa-book fa-lg"></i>
                  <Link className="title is-5" to={"/collections/" + this.props.params.collectionType}>&nbsp;&nbsp;{this.title(this.props.params.collectionType)}</Link>
                </li>
                <li className="is-active">
                  <a className="title is-5">{collection_data["name"]}</a>
                </li>
              </ul>
            </nav>
          </div>
        </section>
        <ResponsiveMasonry
          columnsCountBreakPoints={{ 300: 1, 600: 2, 900: 3, 1200: 4, 1500: 5 }}
        >
          <Masonry
            gutter="10px"
          >
            {collection_data["photos"].map((image, i) => (
              <img
                className="gallery-image"
                key={i}
                src={image.srcSet["(500, 500)w"]}
                alt={image.name}
                slug={image.slug}
                loading="lazy"
                draggable={allowDownload}
                onContextMenu={allowDownload ? undefined : (e) => e.preventDefault()}
                onClick={this.openModal}
              />
            ))}
          </Masonry>
        </ResponsiveMasonry>
        <Modal
          isOpen={this.state.viewerIsOpen}
          onRequestClose={this.closeModal}
          preventScroll={true}
          
          style={{
            overlay: {
              backgroundColor: 'rgba(0, 0, 0, 0.85)'
            },
            content: {
              inset: '10px',
              padding: '10px',
              backgroundColor: 'rgba(0, 0, 0, 1)',
              border: 'none',
              outline: 'none',
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
                            this.setState({ viewerIsOpen: false });
                            this.props.navigate(`/collections/people/${person.slug}`);
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
              if (this.props.params.image) {
                const photoIndex = collection_data["photos"].findIndex(p => p.slug === this.props.params.image);
                if (photoIndex !== -1) {
                  this.setState({ currentPhotoIndex: photoIndex });
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
              collection_data["photos"].map(x =>
                <SwiperSlide key={x.slug} slug={x.slug} data-hash={"/collections/" + this.props.params.collectionType + "/" + this.props.params.collection + "/" + x.slug}>
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
                        const currentPhoto = collection_data["photos"]?.[this.state.currentPhotoIndex];
                        if (currentPhoto && x.slug === currentPhoto.slug) {
                          this.imageRef = e.target;
                          this.currentImageRef = e.target;
                          this.slideContentRef = e.target.parentElement;
                          // Force update when image loads so FaceTagOverlay can recalculate
                          // Use requestAnimationFrame to ensure image is fully rendered
                          if (this.state.showFaceTags) {
                            requestAnimationFrame(() => {
                              requestAnimationFrame(() => {
                                this.forceUpdate();
                              });
                            });
                          }
                        }
                      }}
                    />
                    {this.state.showFaceTags && x.faces && x.faces.length > 0 && x.slug === (collection_data["photos"]?.[this.state.currentPhotoIndex]?.slug) && this.imageRef && this.slideContentRef && (
                      <FaceTagOverlay 
                        key={x.slug}
                        faces={x.faces} 
                        imageRef={this.imageRef}
                        containerRef={this.slideContentRef}
                        originalWidth={x.width} 
                        originalHeight={x.height}
                        navigate={this.props.navigate}
                      />
                    )}
                  </div>
                </SwiperSlide>
              )
            }
          </Swiper>
        </Modal>
      </div>
    );
  }
}

export default withRouter(Collection)