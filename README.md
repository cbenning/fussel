# Fussel

![License Badge](https://img.shields.io/github/license/cbenning/fussel)
![Version Badge](https://img.shields.io/github/v/release/cbenning/fussel)

Fussel is a static photo gallery generator. It can build a simple static photo gallery site
with nothing but a directory full of photos. 

Features and Properties:
 - Absolutely no server-side code to worry about once deployed
 - Builds special "Person" gallery for people found in XMP face tags.
 - Adds watermarks
 - Mobile friendly

## Screenshots
| ![Albums Screenshot](https://user-images.githubusercontent.com/153700/81897761-1e904780-956c-11ea-9450-fbdb286b95fc.png?raw=true "Albums Screenshot") | ![Album Screenshot](https://user-images.githubusercontent.com/153700/81897716-120bef00-956c-11ea-9204-b8e90ffb24f8.png?raw=true "Album Screenshot") |  
|---|---|
| ![People Screenshot](https://user-images.githubusercontent.com/153700/81897685-fef91f00-956b-11ea-8df6-9c23fad83bb2.png?raw=true "People Screenshot") | ![Person Screenshot](https://user-images.githubusercontent.com/153700/81897698-091b1d80-956c-11ea-9acb-6195d9673407.png?raw=true "PersonScreenshot") | 

## Demo
![Demo Gif](https://user-images.githubusercontent.com/153700/81898094-d58cc300-956c-11ea-90eb-f8ce5561f63d.gif?raw=true "Modal Screenshot")

## Setup

### Requirements

 - Python 3
 - Node + Yarn

## Install dependencies

### Site Generator
 - `pip install -r requirements`
 
### Node Frontend
 - `cd web`
 - `yarn install`
 - `cd ../`
 
## Setup Site

### Configure

 - Copy `.env.example` to `.env`
 - Edit `.env` to your needs
 
### Generate your site

 - `./generate_site.sh`
 
 ### Generate frontend

 - `cd web`
 - `yarn build`
 - `cd ../`
 
 
### Host your site

Point your web server at `web/build`

#### Quick setup

After running `generate_site.sh`

 - `python -m http.server --directory web/build` (go to localhost:8000 in browser)

#### Development setup

 - `cd web`
 - `yarn start`
