import React, { Component } from 'react';
import "./NotFound.css";
import withRouter from './withRouter';

class NotFound extends Component {

  constructor(props) {
    super(props);
    this.state = { };
  }

  render() {
    return (
        <div className="message">
          Not Found
        </div>
    );
  }
}

export default withRouter(NotFound)