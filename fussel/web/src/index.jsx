import React from "react";
import ReactDOM from "react-dom/client";
import App from "./component/App";
import "./index.css";

import { HashRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById("app")).render(
  <React.StrictMode>
    <HashRouter>
      <App id='appElement' />
    </HashRouter>
  </React.StrictMode>
);