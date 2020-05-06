import React from "react";

export default class Navbar extends React.Component {

  constructor(props) {
    super(props)
  }

  render() {
    return (
      <nav class="navbar is-light" role="navigation" aria-label="main navigation">
        <div class="navbar-brand">
          <a class="navbar-item">
            <img src="/static/img/animal-track.jpg" alt="logo" width="32" height="32" />
          </a>
          <a role="button" class="navbar-burger burger" aria-label="menu" aria-expanded="false" data-target="navbarBasicExample">
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
          </a>
        </div>
        <div class="navbar-menu">
          <div class="navbar-start">
            <a class="navbar-item" onClick={(e) => this.props.changeCollectionType("albums")}>
              Albums
            </a>
            <a class="navbar-item" onClick={(e) => this.props.changeCollectionType("people")}>
              People
            </a>
          </div>
        </div>
      </nav>
    );
  }
}
