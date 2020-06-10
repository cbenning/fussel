import React from "react";
import "./People.css";

export default class People extends React.Component {

  generateCards = (people) => {
    return (
      <div className="columns is-multiline">
        {Object.keys(people).map(person => { return this.generateCard(people[person]) })}
      </div>
    )
  }

  generateCard = (person) => {
    return (
      <div className="column is-one-quarter" onClick={(e) => this.props.changePerson(person.name)}>
        <div className="card">
          <div className="card-image">
            <figure className="image is-4by3 person-photo">
              <img className="person-photo" src={person.src} alt={person.name} />
            </figure>
          </div>
          <div className="card-content">
            <div className="media-content">
              <p className="title is-5">{person.name}</p>
              <p className="subtitle is-7">{person["photos"].length} Photo{person["photos"].length === 1 ? '' : 's'}</p>
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
                  <i className="fas fa-user-friends fa-lg"></i>
                  <a className="title is-4">&nbsp;&nbsp;People</a>
                </li>
              </ul>
            </nav>
          </div>
        </section>
      {this.generateCards(this.props.people)}
      </div>
    );
  }

}
