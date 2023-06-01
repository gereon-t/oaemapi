# Obsctruction Adaptive Elevation Mask API

# Installation

## Using the repository
```bash
git clone https://github.com/gereon-t/oaemapi.git
```

```bash	
cd oaemapi
```

```bash
pip install -e .
```

## Using pip
```bash
pip install oaemapi
```

# Usage
Run the server with
```bash
oaemapi
```

## Endpoints
### /api
The /api endpoint is used to request the obstruction adaptive elevation mask. It returns a JSON object containing the obstruction adaptive elevation mask in "azimuth:elevation, ..."-format.

Example:
```bash
curl "http://127.0.0.1:8000/api?pos_x=364903.3642&pos_y=5621136.1693&pos_z=109.7938&epsg=25832"
```
Returns
```console
{"Data":"0.009:0.164,0.017:0.163,...,6.274:0.168,6.283:0.166,"}
```

### /plot
The /plot endpoint returns a Plotly (https://plotly.com/) plot of the obstruction adaptive elevation mask in JSON format.

### /
The / endpoint returns a simple HTML page with a Plotly plot of the obstruction adaptive elevation mask. The position is requested from the browser using the Geolocation API (https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API).

# Configuration
The configuration file is located at oaemapi/config.py. The following parameters can be set:

Example:
```python	
HOST = "127.0.0.1"
PORT = 8000
LOG_LEVEL = logging.INFO

N_RANGE = 50
N_RES = 0.05
N_MAX_DIST = 50

GEOID_FILE = "./oaemapi/resources/GCG2016NRW.txt"
GEOID_EPSG = 4258
GEOID_INTERP_EPSG = 25832
GEOID_RES = 20

WFS_EPSG = 25832
WFS_URL = "https://www.wfs.nrw.de/geobasis/wfs_nw_3d-gebaeudemodell_lod1"
WFS_BASE_REQUEST = "Service=WFS&REQUEST=GetFeature&VERSION=1.1.0&TYPENAME=bldg:Building"
```


* HOST: Host of the server.
* PORT: Port of the server.
* LOG_LEVEL: Log level of the server.
* N_RANGE: Neighbourhood range in meters centered around the requested position
* N_RES: Before requesting a new neighborhood, the requested position is rounded to multiples of N_RES. This is done to avoid requesting the same neighborhood multiple times if the position has only slightly changed.
* N_MAX_DIST: Maximum distance a neighborhood is requested from the WFS in meters. If a position is requested that is further away than N_MAX_DIST from the last requested position, an updated neighborhood is requested.
* GEOID_FILE: Path to the geoid file. The geoid file is a text file containing positions and their geoid height in the format "lat lon height". The geoid file is used to convert ellipsoidal heights to orthometric heights.
* GEOID_EPSG: EPSG code of the positions in the geoid file.
* GEOID_INTERP_EPSG: EPSG code of the positions used for interpolation. The interpolation should be done in a metric projected coordinate system.
* GEOID_RES: Before interpolating the geoid file, the positions are rounded to multiples of GEOID_RES. This is done to avoid interpolating the same position multiple times if the position has only slightly changed.
* WFS_EPSG: EPSG code of the positions used for requesting the Web Feature Service (WFS).
* WFS_URL: URL of the WFS.
* WFS_BASE_REQUEST: Base request for the WFS. The request is extended with the position and the neighbourhood range.
 
