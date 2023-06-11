# Obstruction Adaptive Elevation Mask API
An Obstruction Adaptive Elevation Mask (OAEM) describes the obstruction of the sky view, e.g. due to buildings, using azimuth and elevation pairs. The term Obstruction Adaptive Elevation Mask was first used by [Zimmermann 2019](https://www.researchgate.net/publication/329833465_GPS-Multipath_Analysis_using_Fresnel-Zones).

An OAEM can be useful in various scenarios including GNSS Signal filtering:

![](images/oaem.gif)

## Installation

```bash
git clone https://github.com/gereon-t/oaemapi.git
```

```bash	
cd oaemapi
```

```bash
pip install -e .
```

## Usage
Run the server with
```bash
uvicorn main:app --host 0.0.0.0
```

### Endpoints
Once the server is running, you can see the documentation using http://127.0.0.1:8000/docs.
#### /api
The /api endpoint is used to request the obstruction adaptive elevation mask. It returns a JSON object containing the obstruction adaptive elevation mask in "azimuth:elevation, ..."-format.

Example:
```bash
curl "http://127.0.0.1:8000/api?pos_x=364903.3642&pos_y=5621136.1693&pos_z=109.7938&epsg=25832"
```
Returns
```console
{"data":"0.009:0.164,0.017:0.163,...,6.274:0.168,6.283:0.166,", within_area":true}
```

#### /plot
The /plot endpoint returns a Plotly (https://plotly.com/) plot of the obstruction adaptive elevation mask in JSON format.

#### /
The / endpoint returns a simple HTML page with a Plotly plot of the obstruction adaptive elevation mask. The position is requested from the browser using the Geolocation API (https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API).

## Configuration
The configuration file is located at oaemapi/config.py. The following parameters can be set:

Example:
```python	
import logging
import numpy as np

OAEM_RES = np.deg2rad(1)

APP_HOST = "0.0.0.0"
APP_PORT = 8000
logging.basicConfig(
    format="%(levelname)-8s %(asctime)s.%(msecs)03d - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="./oaemapi.log",
)
logger = logging.getLogger("root")

N_RANGE = 150
N_RES = 50

AREA_SHAPEFILE = "./app/data/area.shp"

GEOID_FILE = "./app/data/geoid.txt"
GEOID_EPSG = 4258
GEOID_RES = 100

WFS_EPSG = 25832
WFS_URL = "https://www.wfs.nrw.de/geobasis/wfs_nw_3d-gebaeudemodell_lod1"
WFS_BASE_REQUEST = "Service=WFS&REQUEST=GetFeature&VERSION=1.1.0&TYPENAME=bldg:Building"



with open("./app/version", "r") as f:
    VERSION = f.read().strip()

```

* `OAEM_RES`: Resolution of the azimuth grid of the OAEM in radians.
* `APP_HOST`: Host of the server.
* `APP_PORT`: Port of the server.
* `N_RANGE`: Neighbourhood range in meters centered around the requested position
* `N_RES`: Before requesting a new neighborhood, the requested position is rounded to multiples of N_RES. This is done to avoid requesting the same neighborhood multiple times if the position has only slightly changed.
* `AREA_SHAPEFILE`: Path to the shapefile defining the area of operation. The area is mainly limited by the availability of (free) CityGML data. In this case, it is limited to Northrhine-Westphalia
* `GEOID_FILE`: Path to the geoid file. The geoid file is a text file containing positions and their geoid height in the format "lat lon height". The geoid file is used to convert ellipsoidal heights to orthometric heights.
* `GEOID_EPSG`: EPSG code of the positions in the geoid file.
* `GEOID_RES`: Before interpolating the geoid file, the positions are rounded to multiples of GEOID_RES. This is done to avoid interpolating the same position multiple times if the position has only slightly changed.
* `WFS_EPSG`: EPSG code of the positions used for requesting the Web Feature Service (WFS). The resulting corner points of the CityGML LOD1 buildings will also be given in this EPSG. Therefore, all positional handling will be done in the WFS_EPSG. Due to the OAEM computation algorithm, this EPSG code must refer to a metric projected coordinate system such as UTM.
* `WFS_URL`: URL of the WFS.
* `WFS_BASE_REQUEST`: Base request for the WFS. The request is extended with the position and the neighbourhood range.
 
## How does it work?
1. The user submits a position to the server.
2. The server retrieves relevant surrounding buildings by making a request to the Web-Feature-Service of Geobasis NRW (https://www.opengeodata.nrw.de/produkte/geobasis/3dg/lod1_gml/lod1_gml/).
3. The roof edges of these buildings are extracted and stored.
4. The azimuth values of these roof edges are calculated based on the user's submitted position (from step 1) and stored using an [Intervaltree](https://github.com/chaimleib/intervaltree) data structure.
5. An azimuth grid is created with a resolution specified by the user. For each azimuth value in the grid, the relevant edges are retrieved using the Interval Tree. The edge with the highest elevation, considering the user's position, is used to determine the elevation entry of the Obstruction Adaptive Elevation Mask (OAEM) at that particular azimuth.