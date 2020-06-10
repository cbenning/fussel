import React from "react";
import "./Navbar.css";
import logo from '../images/animal-track.jpg';

export default class Navbar extends React.Component {

  generateAlbumsButton = () => {
    return(
      <a className="navbar-item" onClick={(e) => this.props.changeCollectionType("albums")}>
        <span className="icon">
          <i className="fas fa-book"></i>
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
        <a className="navbar-item" onClick={(e) => this.props.changeCollectionType("people")}>
          <span className="icon">
            <i className="fas fa-user-friends"></i>
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
      <nav className="navbar is-light has-shadow" role="navigation" aria-label="main navigation">
        <div className="navbar-brand" onClick={(e) => this.props.changeCollectionType("albums")}>
          <a className="navbar-item">
            <img src={logo} alt="logo" width="36" height="36" />
          </a>
        </div>
          <div className="navbar-menu is-active">
            <div className="navbar-start">
              {this.generateAlbumsButton()}
              {this.generatePeopleButton(this.props.people)}
            </div>
          </div>
          <div className="navbar-end">
          </div>
      </nav>
    );
  }
}
