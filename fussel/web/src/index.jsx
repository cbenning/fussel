import React from "react";
import ReactDOM from "react-dom/client";
import App from "./component/App";
import { loadGallery } from "./gallery.js";
import "./index.css";

import { HashRouter } from 'react-router';

const root = ReactDOM.createRoot(document.getElementById("app"));

loadGallery().then(
  () => root.render(
    <React.StrictMode>
      <HashRouter>
        <App id='appElement' />
      </HashRouter>
    </React.StrictMode>
  ),
  (error) => {
    console.error(error);
    root.render(<p style={{ padding: "2rem" }}>Failed to load the gallery data.</p>);
  }
);
