import React from "react";
import "./Albums.css";

export default class Albums extends React.Component {

  generateCards = (albums) => {
    return (
      <div class="columns is-multiline is-mobile">
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
            <div class="media-content">
              <p class="title is-5">{album.name}</p>
              <p class="subtitle is-7">{album["photos"].length} Photo{album["photos"].length === 1 ? '' : 's'}</p>
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
            <nav class="breadcrumb" aria-label="breadcrumbs">
              <ul>
                <li class="is-active">
                  <i class="fas fa-book fa-lg"></i>
                  <a class="title is-4">&nbsp;&nbsp;Albums</a>
                </li>
              </ul>
            </nav>
          </div>
        </section>
      {this.generateCards(this.props.albums)}
      </div>
    );
  }
}
