 Fussel

![License Badge](https://img.shields.io/github/license/cbenning/fussel)
![Version Badge](https://img.shields.io/github/v/release/cbenning/fussel)

Fussel is a static photo gallery generator. It can build a simple static photo gallery site
with nothing but a directory full of photos. 

**[Demo Site](https://benninger.ca/fussel-demo/)**

Features and Properties:
 - No server-side code to worry about once generated
 - Builds special "Person" gallery for people found in XMP face tags.
 - Adds watermarks
 - Mobile friendly
 - Automatic dark-mode
 - Uses EXIF hints to rotate photos
 - Predictable slug-basted urls

Common Use-cases:
 - Image Portfolios
 - Family Photos
 - Sharing Photo Archives
 - etc

## Screenshots
| ![Albums Screenshot](https://user-images.githubusercontent.com/153700/81897761-1e904780-956c-11ea-9450-fbdb286b95fc.png?raw=true "Albums Screenshot") | ![Album Screenshot](https://user-images.githubusercontent.com/153700/81897716-120bef00-956c-11ea-9204-b8e90ffb24f8.png?raw=true "Album Screenshot") |  
|---|---|
| ![People Screenshot](https://user-images.githubusercontent.com/153700/81897685-fef91f00-956b-11ea-8df6-9c23fad83bb2.png?raw=true "People Screenshot") | ![Person Screenshot](https://user-images.githubusercontent.com/153700/81897698-091b1d80-956c-11ea-9acb-6195d9673407.png?raw=true "PersonScreenshot") | 

## Demo
![Demo Gif](https://user-images.githubusercontent.com/153700/81898094-d58cc300-956c-11ea-90eb-f8ce5561f63d.gif?raw=true "Modal Screenshot")

## Setup

### Requirements

 - Python 3.7+
 - node v18.14.0 LTS
 - npm v9.3.1
 - yarn 1.22

## Install dependencies

 - `./setup.sh`
 
## Setup Site

### Configure

 - Copy `sample_config.yml` to `config.yml`
 - Edit `config.yml` to your needs (minimal change is to set INPUT_PATH)

### Curate photos
The folder you point `gallery.input_path` at must have subfolders inside it with the folder names as the name of the albums you want in the gallery. 

#### Example

If you have your .env setup with:
```
gallery:
  input_path: "/home/user/Photos/gallery"
```

Then that path should look like this:
```
/home/user/Photos/gallery:
  - Album 1
  - Album 2
    - Sub Album 1
  - Album 3
    - Sub Album 2
  - ...
```

### Generate your site
Run the following script to generate your site into the path you set in `gallery.output_path` folder.
 - `./generate_site.sh`
 
### Host your site

Point your web server at `gallery.output_path` folder or copy/upload the `gallery.output_path` folder to your web host HTTP root.

#### Quick setup

After running `generate_site.sh`

 - `python -m http.server --directory <output_path>` (go to localhost:8000 in browser)

#### Development setup

 - `cd fussel/web`
 - `yarn start`
 
## Docker

If you don't want to fuss with anything and would like to use docker instead to generate your site...

### Usage

Required:
 * `<input_dir>` is the absolute path to top-level photo folder
 * `<output_dir>` is the absolute path to where you want the generated site written to

Note: 
 * The two -e env variables PGID and PUID tells the container what to set the output folder permissions to
 once done. Otherwise it is set to root permissions
 * Look at docker/template_config.yml To see what ENV vars map to which config values

```
docker run \
  -v <input-dir>:/input:ro \
  -v <output-dir>:/output \
  -e PGID=$(id -g) \
  -e PUID=$(id -u) \
  -e INPUT_PATH="/input" \
  -e OUTPUT_PATH="/output" \
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

Once complete you can upload the output folder to your webserver, or see what it looks like with
`python -m http.server --directory <output_path>`


## FAQ

### I get an error 'JavaScript heap out of memory'

Try increasing your Node memory allocation: `NODE_OPTIONS="--max-old-space-size=2048" yarn build` 

Reference: https://github.com/cbenning/fussel/issues/25