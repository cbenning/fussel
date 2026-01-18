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
      showFaceTags: savedShowFaceTags
    };
    this.swiperRef = null;
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
    this.setState({
      currentPhotoIndex: newIndex
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
              enabled: true,
            }}
            keyboard={{ enabled: true, }}
            pagination={{ clickable: true, }}
            hashNavigation={{
              watchState: true,
            }}
            modules={[Keyboard, HashNavigation, Pagination, Navigation]}
            className="swiper"
          >
            {
              collection_data["photos"].map(x =>
                <SwiperSlide key={x.slug} slug={x.slug} data-hash={"/collections/" + this.props.params.collectionType + "/" + this.props.params.collection + "/" + x.slug}>
                  <div className="swiper-slide-content">
                    <img 
                      title={x.name} 
                      src={x.src}
                      className="swiper-image"
                      data-slug={x.slug}
                      draggable={allowDownload}
                      onContextMenu={allowDownload ? undefined : (e) => e.preventDefault()}
                      onLoad={(e) => {
                        // Update refs for the currently active photo when its image loads
                        // Check both slug and index to ensure we're updating the right image
                        const currentPhoto = collection_data["photos"]?.[this.state.currentPhotoIndex];
                        if (currentPhoto && x.slug === currentPhoto.slug) {
                          this.imageRef = e.target;
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