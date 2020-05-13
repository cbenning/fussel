import React from "react";
import "./Navbar.css";
import logo from '../images/animal-track.jpg';

export default class Navbar extends React.Component {

  generateAlbumsButton = () => {
    return(
      <a class="navbar-item" onClick={(e) => this.props.changeCollectionType("albums")}>
        <span class="icon">
          <i class="fas fa-book"></i>
        </span>
        <span>
          &nbsp;
          Albums
        </span>
      </a>
    )
  }

  generatePeopleButton = (people) => {
    if(Object.keys(people).length > 0) {
      return(
        <a class="navbar-item" onClick={(e) => this.props.changeCollectionType("people")}>
          <span class="icon">
            <i class="fas fa-user-friends"></i>
          </span>
          <span>
          	&nbsp;
            People
          </span>
        </a>
      )
    }
    return ''
  }

  render() {
    return (
      <nav class="navbar is-light has-shadow" role="navigation" aria-label="main navigation">
        <div class="navbar-brand" onClick={(e) => this.props.changeCollectionType("albums")}>
          <a class="navbar-item">
            <img src={logo} alt="logo" width="36" height="36" />
          </a>
        </div>
          <div class="navbar-menu is-active">
            <div class="navbar-start">
              {this.generateAlbumsButton()}
              {this.generatePeopleButton(this.props.people)}
            </div>
          </div>
          <div class="navbar-end">
          </div>
      </nav>
    );
  }
}
