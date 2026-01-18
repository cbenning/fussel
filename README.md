# Fussel

![License Badge](https://img.shields.io/github/license/cbenning/fussel)
![Version Badge](https://img.shields.io/github/v/release/cbenning/fussel)

**Fussel** is a static photo gallery generator that builds beautiful, mobile-friendly photo galleries from a directory of photos. Once generated, your gallery is a completely static site with no server-side code required.

**[View Demo Site](https://benninger.ca/fussel-demo/)**

## ✨ Features

- 🖼️ **Static Site Generation** - No server-side code required once generated
- 👥 **People Detection** - Automatically creates galleries for people found in XMP face tags
- 🎨 **Watermarking** - Add watermarks to protect your photos
- 📱 **Mobile Friendly** - Responsive design that works on all devices
- 🌙 **Dark Mode** - Automatic dark mode support
- 🔄 **EXIF Support** - Uses EXIF data to automatically rotate photos
- 🔗 **Clean URLs** - Predictable slug-based URLs for easy sharing
- ⚡ **Fast Generation** - Parallel processing for quick builds

## 📸 Screenshots

| Albums View | Album View |
|-------------|------------|
| ![Albums Screenshot](https://user-images.githubusercontent.com/153700/81897761-1e904780-956c-11ea-9450-fbdb286b95fc.png?raw=true "Albums Screenshot") | ![Album Screenshot](https://user-images.githubusercontent.com/153700/81897716-120bef00-956c-11ea-9204-b8e90ffb24f8.png?raw=true "Album Screenshot") |

| People View | Person View |
|-------------|-------------|
| ![People Screenshot](https://user-images.githubusercontent.com/153700/81897685-fef91f00-956b-11ea-8df6-9c23fad83bb2.png?raw=true "People Screenshot") | ![Person Screenshot](https://user-images.githubusercontent.com/153700/81897698-091b1d80-956c-11ea-9acb-6195d9673407.png?raw=true "Person Screenshot") |

## 🎬 Demo

![Demo Gif](https://user-images.githubusercontent.com/153700/81898094-d58cc300-956c-11ea-90eb-f8ce5561f63d.gif?raw=true "Modal Screenshot")

## 🚀 Quick Start

### Option 1: Using Docker (Recommended - No Dependencies Required)

Docker is the easiest way to run Fussel without installing any dependencies locally.

#### Using Docker Compose (Easiest)

1. **Set your paths** using environment variables:
   ```bash
   export INPUT_DIR=/absolute/path/to/your/photos
   export OUTPUT_DIR=/absolute/path/to/output
   docker-compose up
   ```
   
   Or edit `docker-compose.yml` directly and replace the path placeholders.


2. **Optional: Customize settings** via environment variables or `.env` file:
   ```bash
   # Example .env file (or export these before running docker-compose)
   INPUT_DIR=/home/user/photos
   OUTPUT_DIR=/home/user/gallery-output
   PUID=1000              # Your user ID (run 'id -u' to find it)
   PGID=1000              # Your group ID (run 'id -g' to find it)
   PARALLEL_TASKS=4
   FACE_TAG_ENABLE=True
   WATERMARK_ENABLE=True
   ```

3. **After generation completes**, your gallery will be in the `OUTPUT_DIR` you specified. You can preview it locally or upload it to a web host.

#### Using Docker Run

```bash
docker run \
  -v <input-dir>:/input:ro \
  -v <output-dir>:/output \
  -e PGID=$(id -g) \
  -e PUID=$(id -u) \
  -e INPUT_PATH="/input" \
  -e OUTPUT_PATH="/output" \
  -e PARALLEL_TASKS="4" \
  ghcr.io/cbenning/fussel:latest
```

**Notes:**
- Replace `<input-dir>` and `<output-dir>` with absolute paths to your directories
- The `PGID` and `PUID` environment variables set the output folder permissions to match your user, preventing root-owned files
- After the container completes, your generated gallery will be in `<output-dir>`

See [Docker Configuration](#-docker-configuration) below for all available options.

### Option 2: Local Installation

If you prefer not to use Docker or want to develop Fussel, you can install it locally.

#### Prerequisites

- **Python** 3.8+ (3.7+ supported, but 3.8+ recommended)
- **Node.js** v18+ (LTS recommended)
- **Yarn** 1.22+ (required)
- **Make** (optional, but recommended for easier setup)

#### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cbenning/fussel.git
   cd fussel
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Configure Fussel:**
   ```bash
   cp sample_config.yml config.yml
   ```
   
   Edit `config.yml` and set at minimum:
   - `gallery.input_path` - Path to your photos directory
   - `gallery.output_path` - Where to generate the site (default: `site/`)

4. **Generate your gallery:**
   ```bash
   make generate
   ```

5. **Preview your site:**
   ```bash
   make serve
   ```
   
   Then visit `http://localhost:8000` in your browser.

## 📁 Organizing Your Photos

Your photo directory structure determines your album structure. Each subfolder becomes an album. This section explains how to organize your photos before generating your gallery.

### Directory Structure

Point `gallery.input_path` to a directory containing subfolders, where each subfolder name becomes an album name:

```
/home/user/Photos/gallery/
├── Album 1/
│   ├── photo1.jpg
│   └── photo2.jpg
├── Album 2/
│   ├── Sub Album 1/
│   │   └── photo3.jpg
│   └── photo4.jpg
└── Album 3/
    └── Sub Album 2/
        └── photo5.jpg
```

### Supported Image Formats

Fussel supports common image formats:
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)

## ⚙️ Configuration

The `config.yml` file (or Docker environment variables) controls all aspects of gallery generation.

### Gallery Settings

```yaml
gallery:
  input_path: "/path/to/photos"      # Required: Your photos directory
  output_path: "site/"               # Where to generate the site
  overwrite: False                   # Force rebuild all photos
  parallel_tasks: 4                  # Parallel processing workers
  exif_transpose: False              # Use EXIF rotation data
```

### Album Settings

```yaml
gallery:
  albums:
    recursive: True                  # Process subfolders as albums
    recursive_name_pattern: "{parent_album} > {album}"  # Sub-album naming
```

### People/Face Detection

```yaml
gallery:
  people:
    enable: True                     # Enable face detection from XMP tags
```

### Watermark Settings

```yaml
gallery:
  watermark:
    enable: True                     # Enable watermarks
    path: "web/src/images/fussel-watermark.png"  # Watermark image
    size_ratio: 0.3                  # Watermark size (0.0-1.0)
```

### Site Settings

```yaml
site:
  http_root: "/"                     # URL root (include trailing slash)
  title: "Fussel Gallery"            # Browser tab title
```

## 🐳 Docker Configuration

This section provides detailed information about Docker configuration options. For a quick start, see the [Docker Quick Start](#option-1-using-docker-recommended---no-dependencies-required) section above.

### Available Environment Variables

See `docker/template_config.yml` for all available configuration options. Key variables:

- `INPUT_PATH` - Path to input photos (inside container)
- `OUTPUT_PATH` - Path to output directory (inside container)
- `PARALLEL_TASKS` - Number of parallel workers (default: 1)
- `OVERWRITE` - Force rebuild of all photos (default: False)
- `EXIF_TRANSPOSE` - Use EXIF data for rotation (default: False)
- `FACE_TAG_ENABLE` - Enable face detection (default: True)
- `WATERMARK_ENABLE` - Enable watermarks (default: True)
- `SITE_TITLE` - Gallery title (default: "Fussel Gallery")
- `SITE_ROOT` - HTTP root path (default: "/")

### Complete Docker Run Example

For advanced users who want to customize all options:

```bash
docker run \
  -v <input-dir>:/input:ro \
  -v <output-dir>:/output \
  -e PGID=$(id -g) \
  -e PUID=$(id -u) \
  -e INPUT_PATH="/input" \
  -e OUTPUT_PATH="/output" \
  -e PARALLEL_TASKS="4" \
  -e OVERWRITE="False" \
  -e EXIF_TRANSPOSE="False" \
  -e RECURSIVE="True" \
  -e RECURSIVE_NAME_PATTERN="{parent_album} > {album}" \
  -e FACE_TAG_ENABLE="True" \
  -e WATERMARK_ENABLE="True" \
  -e WATERMARK_PATH="web/src/images/fussel-watermark.png" \
  -e WATERMARK_SIZE_RATIO="0.3" \
  -e SITE_ROOT="/" \
  -e SITE_TITLE="Fussel Gallery" \
  ghcr.io/cbenning/fussel:latest
```

## 🌐 Hosting Your Gallery

Once generated, your gallery is a static site. You can host it anywhere:

1. **Upload to any web host** - Copy the contents of `gallery.output_path` to your web server's document root
2. **Use GitHub Pages** - Push the output directory to a GitHub repository and enable Pages
3. **Use a CDN** - Upload to services like Netlify, Vercel, or Cloudflare Pages
4. **Local preview** - Use `make serve` (see [Quick Start](#-quick-start) for details) or Python's built-in server:
   ```bash
   make serve
   ```
   
   Or manually:
   ```bash
   python -m http.server --directory <output_path>
   ```

## 🛠️ Development

### Development Mode

Run the web app in development/watch mode:

```bash
make dev
```

Or manually:
```bash
cd fussel/web && yarn start
```

### Running Tests

```bash
make test
```

This will:
- Install test dependencies if needed
- Run all tests with coverage
- Generate coverage reports in `htmlcov/`

### Project Structure

```
fussel/
├── fussel/              # Main Python package
│   ├── generator/       # Gallery generation logic
│   └── web/             # React frontend
├── tests/               # Test suite
├── docker/              # Docker configuration
├── config.yml           # Your configuration (not in git)
└── sample_config.yml    # Configuration template
```

## ❓ FAQ

### I get an error 'JavaScript heap out of memory'

Try increasing Node.js memory allocation:

```bash
NODE_OPTIONS="--max-old-space-size=2048" yarn build
```

Reference: [Issue #25](https://github.com/cbenning/fussel/issues/25)

### How do I update Fussel?

If installed via `make install`:
```bash
git pull
make install
```

If using Docker:
```bash
docker pull ghcr.io/cbenning/fussel:latest
```

### Can I customize the gallery appearance?

The gallery uses a React-based frontend. You can modify the styles in `fussel/web/src/` and rebuild.

### Does Fussel modify my original photos?

No. Fussel only reads from your input directory and writes to your output directory. Your original photos are never modified.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔗 Links

- [Demo Site](https://benninger.ca/fussel-demo/)
- [GitHub Repository](https://github.com/cbenning/fussel)
- [Issue Tracker](https://github.com/cbenning/fussel/issues)
