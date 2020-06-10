import React from "react";
import "./Albums.css";

export default class Albums extends React.Component {

  generateCards = (albums) => {
    return (
      <div className="columns is-multiline">
        {Object.keys(albums).map(album => { return this.generateCard(albums[album]) })}
      </div>
    )
  }

  generateCard = (album) => {
    return (
      <div className="column is-one-quarter" onClick={(e) => this.props.changeAlbum(album.name)}>
        <div className="card">
          <div className="card-image">
            <figure className="image is-4by3 album-photo">
              <img className="album-photo" src={album.src} alt={album.name} />
            </figure>
          </div>
          <div className="card-content">
            <div className="media-content">
              <p className="title is-5">{album.name}</p>
              <p className="subtitle is-7">{album["photos"].length} Photo{album["photos"].length === 1 ? '' : 's'}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  render() {
    return (
      <div className="container">
        <section className="hero is-small">
          <div className="hero-body">
            <nav className="breadcrumb" aria-label="breadcrumbs">
              <ul>
                <li className="is-active">
                  <i className="fas fa-book fa-lg"></i>
                  <a className="title is-4">&nbsp;&nbsp;Albums</a>
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
