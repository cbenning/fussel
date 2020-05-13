import React, { Component } from "react";
import Gallery from "react-photo-gallery";
import Carousel, { Modal, ModalGateway } from "react-images";

export default class Album extends Component {

  constructor(props) {
    super(props);
    this.state = {
      currentImage: 0,
      viewerIsOpen: false
    };
    if(props.photo != null) {
        var index = this.findIndexByName(props.photo)
        this.state = {
          currentImage: index,
          viewerIsOpen: true
        };
        this.openLightbox(null,
            {
              index,
              photo: props.album["photos"][index],
              previous: props.album["photos"][index - 1] || null,
              next: props.album["photos"][index + 1] || null,
              updateState: false
            },
        );
    }
  }

  openLightbox = (event, obj) => {
    this.viewChange(obj['index'])

    if(obj['updateState'] !== true) {
        this.setState({
          currentImage: obj['index'],
          viewerIsOpen: true
        })
    }
  };

  closeLightbox = () => {
    this.props.changeAlbum(this.props.album['name'])
    this.setState({
      currentImage: 0,
      viewerIsOpen: false
    })
  };

  viewChange = (index) => {
    this.props.changePhoto(
        "album",
        this.props.album['name'],
        this.props.album["photos"][index]["name"])
  }

  findIndexByName = (photoName) => {
    var index;
    for (index in this.props.album["photos"]) {
        if (this.props.album["photos"][index]["name"] === photoName) {
            return index
        }
    }
    console.log("didn't find index")
  }

  render() {
    return (
      <div class="container" >
        <section class="hero is-small">
          <div class="hero-body">
            <nav class="breadcrumb" aria-label="breadcrumbs">
              <ul>
                <li onClick={(e) => this.props.changeCollectionType("albums")}>
                  <i class="fas fa-book fa-lg"></i>
                  <a class="title is-4">&nbsp;&nbsp;Albums</a>
                </li>
                <li class="is-active">
                  <a class="title is-4">{this.props.album["name"]}</a>
                </li>
              </ul>
            </nav>
          </div>
        </section>
        <Gallery photos={this.props.album["photos"]} onClick={this.openLightbox} />
        <ModalGateway>
          {this.state.viewerIsOpen ? (
            <Modal onClose={this.closeLightbox} >
              <Carousel
                currentIndex={this.state.currentImage}
                trackProps={{onViewChange:(index) => this.viewChange(index)}}
                views={this.props.album["photos"].map(x => ({
                  ...x,
                  srcset: x.srcSet,
                  caption: x.title
                }))}
              />
            </Modal>
          ) : null}
        </ModalGateway>
      </div>
    );
  }
}
