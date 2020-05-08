import React from "react";
import "./People.css";

export default class People extends React.Component {

  generateCards = (people) => {
    return (
      <div class="columns is-multiline">
        {Object.keys(people).map(person => { return this.generateCard(people[person]) })}
      </div>
    )
  }

  generateCard = (person) => {
    console.log(person)
    return (
        <div class="column is-one-quarter" onClick={(e) => this.props.changePerson(person.name)}>
          <div class="card">
            <div class="card-image">
              <figure class="image is-4by3 person-photo">
                <img class="person-photo" src={person.src} alt={person.name} />
              </figure>
            </div>
            <div class="card-content">
              <div class="media-content">
                <p class="title is-5">{person.name}</p>
                <p class="subtitle is-7">{person["photos"].length} Photo{person["photos"].length === 1 ? '' : 's'}</p>
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
              <span class="icon is-large"><i class="fas fa-user-friends fa-lg"></i></span>
              <b class="title is-4">People</b>
            </div>
          </div>
        </section>
      {this.generateCards(this.props.people)}
      </div>
    );
  }

}
