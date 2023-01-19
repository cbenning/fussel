import React from "react";
import ReactDOM from "react-dom/client";
import App from "./component/App";

import { BrowserRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById("app")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App id='appElement' />
    </BrowserRouter>
  </React.StrictMode>
);