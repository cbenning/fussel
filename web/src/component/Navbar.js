import React from "react";
import "./Navbar.css";
import logo from '../images/animal-track.jpg';

export default class Navbar extends React.Component {

  generateAlbumsButton = () => {
    return(
      <a class="navbar-item" onClick={(e) => this.props.changeCollectionType("albums")}>
        Albums
      </a>
    )
  }

  generatePeopleButton = (people) => {
    if(Object.keys(people).length > 0) {
      return(
        <a class="navbar-item" onClick={(e) => this.props.changeCollectionType("people")}>
          People
        </a>
      )
    }
    return ''
  }

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
            {this.generateAlbumsButton()}
            {this.generatePeopleButton(this.props.people)}
          </div>
        </div>
      </nav>
    );
  }
}
