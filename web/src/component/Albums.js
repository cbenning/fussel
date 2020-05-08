import React from "react";
import "./Albums.css";

export default class Albums extends React.Component {

  constructor(props) {
    super(props);
  }

  generateCards = (albums) => {
    return (
      <div class="columns is-multiline">
        {Object.keys(albums).map(album => { return this.generateCard(albums[album]) })}
      </div>
    )
  }

  generateCard = (album) => {
    return (
      <div class="column is-one-quarter" onClick={(e) => this.props.changeAlbum(album.name)}>
        <div class="card">
          <div class="card-image">
            <figure class="image is-4by3 album-photo">
              <img class="album-photo" src={album.src} alt={album.name} />
            </figure>
          </div>
          <div class="card-content">
            <div class="content">
                <p class="title is-6">{album.name}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  render() {
    return (
      <div class="container">
        <section class="hero is-small">
          <div class="hero-body">
            <div class="container">
              <span class="icon is-large"><i class="fas fa-book fa-lg"></i></span>
              <b class="title is-3">Albums</b>
            </div>
          </div>
        </section>
      {this.generateCards(this.props.albums)}
      </div>
    );
  }
}
