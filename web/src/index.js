import React from "react";
import ReactDOM from "react-dom";
import App from "./component/App";

import { BrowserRouter } from 'react-router-dom';

ReactDOM.render(
   <BrowserRouter>
     <App id='appElement' />
   </BrowserRouter>
  ,
  document.getElementById('app'));
