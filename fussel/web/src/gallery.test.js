import { describe, it, expect, vi, beforeEach } from 'vitest';

const files = {
  site: { site_name: 'Test' },
  albums: { a: { name: 'A' } },
  people: {},
  photos: [{ slug: 'p' }],
};

describe('loadGallery', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn(async (url) => {
      const name = url.split('/').pop().replace('.json', '');
      return { ok: true, status: 200, json: async () => files[name] };
    }));
  });

  it('fetches the data files relative to the page and updates the exports', async () => {
    const gallery = await import('./gallery.js');
    expect(gallery.albums_data).toEqual({});

    await gallery.loadGallery();

    expect(fetch).toHaveBeenCalledWith('static/_gallery/data/albums.json');
    expect(gallery.site_data).toEqual(files.site);
    expect(gallery.albums_data).toEqual(files.albums);
    expect(gallery.people_data).toEqual(files.people);
    expect(gallery.photos_data).toEqual(files.photos);
  });

  it('rejects when a data file is missing', async () => {
    fetch.mockResolvedValue({ ok: false, status: 404 });
    const gallery = await import('./gallery.js');
    await expect(gallery.loadGallery()).rejects.toThrow('HTTP 404');
  });
});
