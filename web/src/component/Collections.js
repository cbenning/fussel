import React, { Component } from 'react';
import { albums_data } from "../_gallery/albums_data.js"
import { people_data } from "../_gallery/people_data.js"
import { Link } from "react-router-dom";
import "./Collections.css";

import withRouter from './withRouter';


class Collections extends Component {

  constructor(props) {
    super(props);
    this.state = { };
  }

  generateCards = (collectionType, subjects) => {
    return (
      <div className="columns is-multiline">
        {Object.keys(subjects).map(subject => { return this.generateCard(collectionType, subjects[subject]) })}
      </div>
    )
  }

  generateCard = (collectionType, subject) => {
    return (
      <Link key={subject.slug} className="column is-one-quarter" to={"/collections/" + collectionType + "/" + subject.slug}>
        <div className="card">
          <div className="card-image">
            <figure className="image is-4by3 subject-photo">
              <img className="subject-photo" src={subject.src} alt={subject.name} />
            </figure>
          </div>
          <div className="card-content">
            <div className="media-content">
              <p className="title is-5">{subject.name}</p>
              <p className="subtitle is-7">{subject["photos"].length} Photo{subject["photos"].length === 1 ? '' : 's'}</p>
            </div>
          </div>
        </div>
      </Link>
    );
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

  collections = (collectionType) => {
    if (collectionType == "albums") {
      return albums_data
    }
    else if (collectionType == "people") {
      return people_data
    }
    return null
  }

  render() {

    // If this is the index we dont get this info from the route
    // so if we're missing the param we pull it from props which
    // will have been passed in manually
    if (!("collectionType" in this.props.params)) {
      if (this.props.collectionType != null) {
        this.props.params.collectionType = this.props.collectionType
      }
    }
    return (
      <div className="container">
        <section className="hero is-small">
          <div className="hero-body">
            <nav className="breadcrumb" aria-label="breadcrumbs">
              <ul>
                <li key="1" className="is-active">
                  <i className="fas fa-book fa-lg"></i>
                  <a className="title is-5">&nbsp;&nbsp;{this.title(this.props.params.collectionType)}</a>
                </li>
              </ul>
            </nav>
          </div>
        </section>
        {this.generateCards(this.props.params.collectionType, this.collections(this.props.params.collectionType))}
      </div>
    );
  }
}

export default withRouter(Collections)