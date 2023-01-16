import React, { Component } from "react";
import Gallery from "react-photo-gallery";
import { Swiper, SwiperSlide } from 'swiper/react';

import { Keyboard, History, Pagination, HashNavigation, Navigation } from "swiper";
import 'swiper/swiper.min.css';
import 'swiper/modules/navigation/navigation.min.css'
import 'swiper/modules/pagination/pagination.min.css'


import Modal from 'react-modal';
import "./Gallery.css";

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
        this.closeModal(null,
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
      <div className="container" >
        <section className="hero is-small">
          <div className="hero-body">
            <nav className="breadcrumb" aria-label="breadcrumbs">
              <ul>
                <li onClick={(e) => this.props.changeCollectionType("people")}>
                  <i className="fas fa-user-friends fa-lg"></i>
                  <a className="title is-4">&nbsp;&nbsp;People</a>
                </li>
                <li className="is-active">
                  <a className="title is-4">{this.props.person["name"]}</a>
                </li>
              </ul>
            </nav>
          </div>
        </section>
        <Gallery photos={this.props.person["photos"]} onClick={this.openLightbox} />
        {/* <ModalGateway>
          {this.state.viewerIsOpen ? (
            <Modal onClose={this.closeLightbox}>
              <Carousel
                frameProps={{autoSize:true}}
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
        </ModalGateway> */}
        <Modal
          isOpen={this.state.viewerIsOpen}
          // onAfterOpen={afterOpenModal}
          onRequestClose={this.closeModal}
          contentLabel="Example Modal"
        >
        <Swiper 
          slidesPerView={1}
          preloadImages={false}
          navigation={{ enabled:true, }}  
          keyboard={{ enabled: true, }}
          pagination={{ clickable: true, }} 
          hashNavigation= {{ 
            replaceState: true, 
            watchState: true, 
          }}
          modules={[History, Keyboard, HashNavigation, Pagination]}
          className="swiper">
          {
            this.props.person["photos"].map(x => 
              <SwiperSlide data-hash={x.name}>
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
