import React, { Component } from "react";
import Masonry, { ResponsiveMasonry } from "react-responsive-masonry"
import withRouter from './withRouter';
import { albums_data } from "../_gallery/albums_data.js"
import { people_data } from "../_gallery/people_data.js"
import SwiperCore, { Keyboard, Pagination, HashNavigation, Navigation } from "swiper";
import { Swiper, SwiperSlide } from 'swiper/react';
import 'swiper/swiper.min.css';
import 'swiper/css/navigation'
import 'swiper/css/pagination'
import Modal from 'react-modal';

import { Link } from "react-router-dom";
import "./Collection.css";

SwiperCore.use([Navigation]); // Not sure why but need this for slide navigation buttons to be clickable
Modal.setAppElement('#app');


class Collection extends Component {

  constructor(props) {
    super(props);
    this.state = {
      viewerIsOpen: true ? this.props.params.image != undefined : false,
      infoModalIsOpen: false
    };
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
      viewerIsOpen: true,
      infoModalIsOpen: false
    })
    // Add listener to detect if the back button was pressed and the modal should be closed
    window.addEventListener('hashchange', this.modalStateTracker, false);
    // var page = document.getElementsByTagName('body')[0];
    // page.classList.add('noscroll');
  };

  closeModal = () => {

    this.props.navigate("/collections/" + this.props.params.collectionType + "/" + this.props.params.collection);
    this.setState({
      viewerIsOpen: false,
      infoModalIsOpen: false
    })
    // var page = document.getElementsByTagName('body')[0];
    // page.classList.remove('noscroll');
  };

  openInfoModal = () => {
    this.setState({
      infoModalIsOpen: true
    })
  };

  closeInfoModal = () => {
    this.setState({
      infoModalIsOpen: false
    })
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

  render() {
    let collection_data = this.collection(this.props.params.collectionType, this.props.params.collection)
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
              backgroundColor: 'rgba(0, 0, 0, 0.3)'
            },
            content: {
              inset: '10px',
              padding: '10px',
              backgroundColor: 'rgba(0, 0, 0, 1)',
            }
          }}
        >
          <button id="infoModal" className="button is-text modal-info-button" onClick={this.openInfoModal} style={{ visibility: this.state.infoModalIsOpen ? "hidden" : "visible" }}>
            <span className="icon is-small">
              <i className="fas fa-info-circle"></i>
            </span>
          </button>
          <button className="button is-text modal-close-button" onClick={this.closeModal} >
            <span className="icon is-small">
              <i className="fas fa-times"></i>
            </span>
          </button>
          <Modal
            isOpen={this.state.infoModalIsOpen}
            onRequestClose={this.closeInfoModal}
            preventScroll={true}
            className="info-modal"
            overlayClassName="info-modal-overlay"
            style={{
              overlay: {
                display: "inline-block",
                position: "absolute",
                right: 60,
                top: 20
              },
              content: {
                position: "relative",
                whiteSpace: "pre-wrap"
              }
            }}
          >
            <div onClick={this.closeInfoModal} class="info-popup">{collection_data["photos"].find(x => x.slug == this.props.params.image)?.exif}</div>
          </Modal>

          <Swiper
            slidesPerView={1}
            preloadImages={false}
            navigation={{
              enabled: true,
            }}
            keyboard={{ enabled: true, }}
            pagination={{ clickable: true, }}
            hashNavigation={{
              watchState: true,
            }}
            modules={[Keyboard, HashNavigation, Pagination]}
            className="swiper"
          >
            {
              collection_data["photos"].map(x =>
                <SwiperSlide slug={x.slug} data-hash={"/collections/" + this.props.params.collectionType + "/" + this.props.params.collection + "/" + x.slug}>
                  <img title={x.name} src={x.src} />
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