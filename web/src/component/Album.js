import React, { Component } from "react";
import Gallery from "react-photo-gallery";
import { Swiper, SwiperSlide } from 'swiper/react';

import { Keyboard, History, Pagination, HashNavigation, Navigation } from "swiper";
import 'swiper/swiper.min.css';
import 'swiper/modules/navigation/navigation.min.css'
import 'swiper/modules/pagination/pagination.min.css'


import Modal from 'react-modal';
import "./Gallery.css";



Modal.setAppElement('#app');

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
        this.closeModal(null,
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


  openModal = (event, obj) => {
    this.viewChange(obj['index'])

    if(obj['updateState'] !== true) {
        this.setState({
          currentImage: obj['index'],
          viewerIsOpen: true
        })
    }
  };

  closeModal = () => {
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
      <div className="container" >
        <section className="hero is-small">
          <div className="hero-body">
            <nav className="breadcrumb" aria-label="breadcrumbs">
              <ul>
                <li onClick={(e) => this.props.changeCollectionType("albums")}>
                  <i className="fas fa-book fa-lg"></i>
                  <a className="title is-4">&nbsp;&nbsp;Albums</a>
                </li>
                <li className="is-active">
                  <a className="title is-4">{this.props.album["name"]}</a>
                </li>
              </ul>
            </nav>
          </div>
        </section>
        <Gallery photos={this.props.album["photos"]} onClick={this.openModal} />
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
            this.props.album["photos"].map(x => 
              <SwiperSlide data-hash={x.name}>
                <img title={x.name} src={x.src} />
              </SwiperSlide>
            )
          }

      </Swiper>
      </Modal>
        {/* <ModalGateway>
          {this.state.viewerIsOpen ? (
            <Modal onClose={this.closeModal} >
              <Swiper
                spaceBetween={50}
                slidesPerView={1}
                onSlideChange={() => console.log('slide change')}
                onSwiper={(swiper) => console.log(swiper)}
              >
                <SwiperSlide>ASDF</SwiperSlide>
                <SwiperSlide>Slide 2</SwiperSlide>
                <SwiperSlide>Slide 3</SwiperSlide>
                <SwiperSlide>Slide 4</SwiperSlide>
              </Swiper>
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
        </ModalGateway> */}
      </div>
    );
  }
}
