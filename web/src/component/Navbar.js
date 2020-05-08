import React from "react";
import "./Navbar.css";
import logo from '../images/animal-track.jpg';

export default class Navbar extends React.Component {

  render() {
    return (
      <nav class="navbar is-light" role="navigation" aria-label="main navigation">
        <div class="navbar-brand">
          <a class="navbar-item">
            <img src={logo} alt="logo" width="32" height="32" />
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
