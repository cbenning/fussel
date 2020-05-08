import React, { Component } from "react";
import Gallery from "react-photo-gallery";
import Carousel, { Modal, ModalGateway } from "react-images";

export default class Person extends Component {

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
              photo: props.person["photos"][index],
              previous: props.person["photos"][index - 1] || null,
              next: props.person["photos"][index + 1] || null,
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
    this.props.changePerson(this.props.person['name'])
    this.setState({
      currentImage: 0,
      viewerIsOpen: false
    })
  };

  viewChange = (index) => {
    this.props.changePhoto(
        "person",
        this.props.person['name'],
        this.props.person["photos"][index]["name"])
  }

  findIndexByName = (photoName) => {
    var index;
    for (index in this.props.person["photos"]) {
        if (this.props.person["photos"][index]["name"] === photoName) {
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
            <div class="container">
              <span class="icon is-large"><i class="fas fa-user-friends fa-lg"></i></span>
              <b class="title is-4">People</b>
              <span class="icon is-large"><i class="fas fa-angle-right fa-lg"></i></span>
              <b class="title is-4">{this.props.person["name"]}</b>
            </div>
          </div>
        </section>
        <Gallery photos={this.props.person["photos"]} onClick={this.openLightbox} />
        <ModalGateway>
          {this.state.viewerIsOpen ? (
            <Modal onClose={this.closeLightbox}>
              <Carousel
                currentIndex={this.state.currentImage}
                trackProps={{onViewChange:(index) => this.viewChange(index)}}
                views={this.props.person["photos"].map(x => ({
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
