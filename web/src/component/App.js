import React, {Component} from 'react';
import Navbar from "./Navbar";
import People from "./People";
import Person from "./Person";
import Albums from "./Albums";
import Album from "./Album";
import { albums_data } from "../_gallery/albums_data.js"
import { people_data } from "../_gallery/people_data.js"
import { withRouter } from "react-router-dom";

class App extends Component {

  constructor(props) {
    super(props);

    this.state = {
      collectionType: this.findCollectionType(),
      collection: this.findCollection(),
      photo: this.findPhoto(),
      component: this.findComponent()
    };
  }

  componentWillMount() {
    this.unlisten = this.props.history.listen((location, action) => {

      let params = this.urlParams()
      this.setState({
        collectionType: params.get('collectionType'),
        collection: params.get('collection'),
        photo: params.get('photo'),
        component: this.findComponent()
      })
    });
  }

  componentWillUnmount() {
      this.unlisten();
  }

  urlParams = () => {
    let search = window.location.search;
    return new URLSearchParams(search);
  }

  findCollection = () => {
    return this.urlParams().get('collection');
  }

  findCollectionType = () => {
    let collectionType = this.urlParams().get('collectionType');
    if (collectionType === "people" || collectionType === "albums" ||
      collectionType === "person" || collectionType === "album") {
      return collectionType
    }
    return "albums"
  }

  findPhoto = () => {
    return this.urlParams().get('photo');
  }

  findComponent = (collectionType, collection, photo) => {
    if (collectionType === "people") {
      return <People people={people_data} changePerson={this.handleSelectPerson} />
    }
    else if (collectionType === "albums") {
      return <Albums albums={albums_data} changeAlbum={this.handleSelectAlbum} />
    }
    else if (collectionType === "person") {
      return <Person person={people_data[collection]} photo={photo} changePhoto={this.handleSelectPhoto} changePerson={this.handleSelectPerson} />
    }
    else if (collectionType === "album") {
      return <Album album={albums_data[collection]} photo={photo} changePhoto={this.handleSelectPhoto} changeAlbum={this.handleSelectAlbum} />
    }
    return <Albums albums={albums_data} changeAlbum={this.handleSelectAlbum} />
  }

  handleChangeCollectionType = (newCollectionType) => {
    this.props.history.push({
      search: this.buildUrlParams(newCollectionType, null, null)
    })
  }

  handleSelectAlbum = (albumName) => {
    this.props.history.push({
      search: this.buildUrlParams("album", albumName, null)
    })
  }

  handleSelectPerson = (personName) => {
    this.props.history.push({
      search: this.buildUrlParams("person", personName, null)
    })
  }

  handleSelectPhoto = (collectionType, collection, photo) => {
    this.props.history.push({
      search: this.buildUrlParams(collectionType, collection, photo)
    })
  }

  handleSelect = (collectionType, collection) => {
    this.props.history.push({
      pathname: '/',
      search: this.buildUrlParams(collectionType, collection)
    })
  }

  buildUrlParams = (collectionType, collection, photo) => {
    let params = '?collectionType=' + collectionType
    if (typeof collection !== 'undefined' && collection != null) {
      params += '&collection=' + collection
    }
    if (typeof photo !== 'undefined' && photo != null) {
      params += '&photo=' + photo
    }
    return params
  }

  render() {
    return (
      <div>
        <Navbar changeCollectionType={this.handleChangeCollectionType} />

        { this.findComponent(this.state.collectionType, this.state.collection, this.state.photo) }
      </div>
    );
  }
}

export default withRouter(App);
