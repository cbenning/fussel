import React, { Component } from 'react';
import Navbar from "./Navbar";
import Collections from "./Collections";
import Collection from "./Collection";
import NotFound from "./NotFound";
import { site_data } from "../_gallery/site_data.js"
import { Routes, Route } from "react-router-dom";
import { Helmet, HelmetProvider } from "react-helmet-async";

export default class App extends Component {

  constructor(props) {
    super(props);
  }

  render() {
    return (
      <HelmetProvider>
      <div>
        <Helmet>
          <title>{site_data['site_name']}</title>
        </Helmet>
        <Routes>
          <Route path="/" element={<Navbar hasPeople={site_data.people_enabled} hasAlbums={site_data.albums_enabled} hasPhotos={site_data.photos_enabled} />}>
            <Route index element={<Collections collectionType="albums" />} />
            <Route path="collections/photos" element={<Collection />} />
            <Route path="collections/photos/:albumSlug/:image" element={<Collection />} />
            <Route path="collections/photos/:image" element={<Collection />} />
            <Route path="collections/:collectionType" element={<Collections />} />
            <Route path="collections/:collectionType/:collection" element={<Collection />} />
            <Route path="collections/:collectionType/:collection/:image" element={<Collection />} />

            {/* Using path="*"" means "match anything", so this route
                  acts like a catch-all for URLs that we don't have explicit
                  routes for. */}
            <Route path="*" element={<NotFound />} />
          </Route>

        </Routes>

      </div>
      </HelmetProvider>
    );
  }
}
