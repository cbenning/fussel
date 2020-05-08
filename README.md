# Fussel

TODO

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
