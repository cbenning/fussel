import React, { Component } from "react";
import Gallery from "react-photo-gallery";
import withRouter from './withRouter';
import { albums_data } from "../_gallery/albums_data.js"
import { people_data } from "../_gallery/people_data.js"
import SwiperCore, { Keyboard, Pagination, HashNavigation, Navigation } from "swiper";
import { Swiper, SwiperSlide } from 'swiper/react';
import 'swiper/swiper.min.css';
import 'swiper/modules/navigation/navigation.min.css'
import 'swiper/modules/pagination/pagination.min.css'
import Modal from 'react-modal';

import { Link } from "react-router-dom";
import "./Collection.css";

SwiperCore.use([Navigation]); // Not sure why but need this for slide navigation buttons to be clickable
Modal.setAppElement('#app');

class Collection extends Component {

  constructor(props) {
    super(props);
    this.state = {
      viewerIsOpen: true ? location.hash != "" : false
    };
  }

  openModal = (event, obj) => {
    this.setState({
      viewerIsOpen: true
    })
    history.pushState(null, null, "#" + obj.photo.slug)
  };

  closeModal = () => {
    this.setState({
      viewerIsOpen: false
    })
    var scrollV, scrollH, loc = window.location;
    history.pushState("", document.title, loc.pathname + loc.search);
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
                  <Link className="title is-4" to={"/collections/" + this.props.params.collectionType}>&nbsp;&nbsp;{this.title(this.props.params.collectionType)}</Link>
                </li>
                <li className="is-active">
                  <a className="title is-4">{collection_data["name"]}</a>
                </li>
              </ul>
            </nav>
          </div>
        </section>
        <Gallery photos={collection_data["photos"]} onClick={this.openModal} />
        <Modal
          isOpen={this.state.viewerIsOpen}
          onRequestClose={this.closeModal}
          preventScroll={true}
          style={{
            content: {
              inset: '10px',
              padding: '10px',
            }
          }}
        >
          <Swiper
            slidesPerView={1}
            preloadImages={false}
            navigation={{
              enabled: true,
            }}
            keyboard={{ enabled: true, }}
            pagination={{ clickable: true, }}
            hashNavigation={{
              replaceState: true,
              watchState: true,
            }}
            modules={[Keyboard, HashNavigation, Pagination]}
            className="swiper"
          >
            {
              collection_data["photos"].map(x =>
                <SwiperSlide data-hash={x.slug}>
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