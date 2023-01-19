import React from "react";
import { Outlet, NavLink } from "react-router-dom";
import "./Navbar.css";
import logo from '../images/animal-track-transparent.png';

export default class Navbar extends React.Component {

  generateAlbumsButton = () => {
    return (
      <NavLink className="navbar-item" to="/collections/albums">
        <span className="icon">
          <i className="fas fa-book"></i>
        </span>
        <span className="navbar-text">
          &nbsp;
          Albums
        </span>
      </NavLink>
    )
  }

  generatePeopleButton = () => {
    if (this.props.hasPeople) {
      return (
        <NavLink className="navbar-item" to="/collections/people">
          <span className="icon">
            <i className="fas fa-user-friends"></i>
          </span>
          <span className="navbar-text">
            &nbsp;
            People
          </span>
        </NavLink>
      )
    }
    return ''
  }

  render() {
    return (
      <div>
        <nav className="navbar has-shadow" role="navigation" aria-label="main navigation">
          <div className="navbar-brand">
            <div className="navbar-item">
              <img src={logo} alt="logo" width="36" height="36" />
            </div>
          </div>
          <div className="navbar-menu is-active">
            <div className="navbar-start">
              {this.generateAlbumsButton()}
              {this.generatePeopleButton()}
            </div>
          </div>
          <div className="navbar-end">
          </div>
        </nav>
        <Outlet />
      </div>
    );
  }
}
