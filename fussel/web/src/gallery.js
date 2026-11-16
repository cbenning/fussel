// Gallery data is generated per gallery as JSON files next to the photos. It is
// fetched at runtime so one prebuilt web app bundle works for every gallery.
//
// The exports are ES module live bindings: they hold empty defaults until
// loadGallery() resolves, so call it (and await it) before rendering.

const DATA_PATH = "static/_gallery/data";

export let site_data = {};
export let albums_data = {};
export let people_data = {};
export let photos_data = [];

async function fetchJson(name) {
  // Relative URL: resolves against the page, so the gallery works under any http_root.
  const response = await fetch(`${DATA_PATH}/${name}.json`);
  if (!response.ok) {
    throw new Error(`Failed to load ${name}.json: HTTP ${response.status}`);
  }
  return response.json();
}

export async function loadGallery() {
  [site_data, albums_data, people_data, photos_data] = await Promise.all([
    fetchJson("site"),
    fetchJson("albums"),
    fetchJson("people"),
    fetchJson("photos"),
  ]);
}
