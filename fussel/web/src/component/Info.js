import React, { Component } from "react";
import withRouter from './withRouter.js';
import { albums_data } from "../_gallery/albums_data.js"
import { people_data } from "../_gallery/people_data.js"
import 'swiper/swiper.min.css';
import 'swiper/css/navigation'
import 'swiper/css/pagination'
import Modal from 'react-modal';
import "./Info.css";

import { Link } from "react-router-dom";

Modal.setAppElement('#app');


class Info extends Component {

  constructor(props) {
    super(props);
  }

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

  photo = (collection, slug) => {
    return collection.photos.find(photo => photo.slug === slug)
  }

  render() {
    let collection_data = this.collection(this.props.params.collectionType, this.props.params.collection)
    let photo = this.photo(collection_data, this.props.params.image)
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
                <li>
                  <Link className="title is-5" to={"/collections/" + this.props.params.collectionType + "/" + this.props.params.collection}>{collection_data.name}</Link>
                </li>
                <li className="is-active">
                  <a className="title is-5">{photo.name}</a>
                </li>
              </ul>
            </nav>
          </div>
        </section>
        <img
          className="image"
          src={photo.src}
          alt={photo.name}
          loading="lazy"
        />
        <div class="camera-info">
          {
            "Make" in photo.exif && <><div class="brand">{photo.exif.Make}</div><span class="separator">|</span></>
          }
          <div class="specs">
            {
              "Model" in photo.exif && <div class="model">{photo.exif.Model}</div>
            }
            {
              "LensModel" in photo.exif && <div class="len">{photo.exif.LensModel}</div>
            }
          </div>
        </div>
        <div class="photo-properties">{
          Object.entries(photo.exif).map((item, i) => (
            <div key={i}>
              <b>{item[0]}:</b> {item[1]}
            </div>
          ))
        }</div>
      </div>
    );
  }
}

export default withRouter(Info)