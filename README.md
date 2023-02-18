# Fussel

![License Badge](https://img.shields.io/github/license/cbenning/fussel)
![Version Badge](https://img.shields.io/github/v/release/cbenning/fussel)

Fussel is a static photo gallery generator. It can build a simple static photo gallery site
with nothing but a directory full of photos. 

**[Demo Site](https://benninger.ca/fussel-demo/)**

Features and Properties:
 - Absolutely no server-side code to worry about once deployed
 - Builds special "Person" gallery for people found in XMP face tags.
 - Adds watermarks
 - Mobile friendly
 - Automatic dark-mode

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
 * For the label-based config to work you must mount `/var/run/docker.sock` into the container, eg: `-v /var/run/docker.sock:/var/run/docker.sock fussel`

Optional:
 You can provide any value found in the config.yml file in a docker label variable using `--label item=value`

```
docker run \
-e PGID=$(id -g) \
-e PUID=$(id -u) \
-v <input_dir>:/input:ro \
-v <output_dir>:/output \
--label gallery.input_path="/input" \
--label gallery.output_path="/output" \
--label gallery.overwrite=False \
--label albums.recursive=True \
--label albums.recursive_name_pattern="{parent_album} > {album}" \
--label people.enable=True \
--label watermark.enable=True \
--label watermark.path="web/src/images/fussel-watermark.png" \
--label watermark.size_ratio=0.3 \
--label site.http_root="/" \
--label site.title="Fussel Gallery" \
-v /var/run/docker.sock:/var/run/docker.sock fussel
```

Once complete you can upload the output folder to your webserver, or see what it looks like with
`python -m http.server --directory <output_dir>`


## FAQ

### I get an error 'JavaScript heap out of memory'

Try increasing your Node memory allocation: `NODE_OPTIONS="--max-old-space-size=2048" yarn build` 

Reference: https://github.com/cbenning/fussel/issues/25