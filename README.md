# Obstruction Adaptive Elevation Mask API
This software computes an Obstruction Adaptive Elevation Mask (OAEM) for a given position using CityGML models. An OAEM describes the obstruction of the sky view, e.g. due to buildings, using azimuth and elevation pairs. The term Obstruction Adaptive Elevation Mask was first used by [Zimmermann 2019](https://www.researchgate.net/publication/329833465_GPS-Multipath_Analysis_using_Fresnel-Zones). The CityGML models are retrieved from a Web Feature Service (WFS).

An OAEM can be useful in various scenarios including GNSS Signal filtering:

![](images/oaem.gif)

The code is designed for the LOD1 building model Web Feature Service of Geobasis NRW, Germany. In its current state, it is therefore only usefully applicable within North Rhine-Westphalia, Germany.

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

Depending on the Web Feature Service height definition you may need geoid undulations. For NRW, Germany you can download them for free at https://gdz.bkg.bund.de/index.php/default/quasigeoid-der-bundesrepublik-deutschland-quasigeoid.html.

## Usage
Run the server with
```bash
uvicorn main:app --host 0.0.0.0
```

### Endpoints
Once the server is running, you can see the documentation using http://127.0.0.1:8000/docs.
#### **/api**
The /api endpoint is used to request the obstruction adaptive elevation mask (OAEM). The OAEM represents the obstruction of the sky view due to
buildings using elevation angles. The endpoint returns a JSON object containing the OAEM in "azimuth:elevation, ..."-format. It is given with an azimuth resolution of 1 degree.

**Note:** The OAEM data provided by this API is currently available only for the state of North Rhine-Westphalia (NRW), Germany.
If the provided position is outside the area of operation, an empty OAEM is returned.

**Args:**

- `pos_x` (float): The x-coordinate of the position.
- `pos_y` (float): The y-coordinate of the position.
- `pos_z` (float): The z-coordinate of the position.
- `epsg` (int): The EPSG code specifying the coordinate reference system (CRS) of the provided position.

**Returns:**

A JSON object with:

- `data` (str): The OAEM data represented as a string in azimuth:elevation format.
  If the position is outside the area of operation, the OAEM will be empty.
  Azimuth and elevation are given in radians.
- `within_area` (bool): A boolean indicating whether the provided position is within the area of operation.


Example:
```bash
curl "http://127.0.0.1:8000/api?pos_x=364903.3642&pos_y=5621136.1693&pos_z=109.7938&epsg=25832"
```
Returns
```console
{"data":"0.009:0.164,0.017:0.163,...,6.274:0.168,6.283:0.166,", within_area":true}
```

#### **/plot**
Computes the Obstruction Adaptive Elevation Mask (OAEM) for a given position and EPSG code, and returns a plot of the OAEM.

**Note:** The OAEM data provided by this API is currently available only for the state of North Rhine-Westphalia (NRW), Germany.

**Args:**

- `pos_x` (float): The x-coordinate of the position.
- `pos_y` (float): The y-coordinate of the position.
- `pos_z` (float): The z-coordinate of the position.
- `epsg` (int): The EPSG code of the position.
- `width` (int, optional): The width of the plot in pixels. Defaults to 600.
- `height` (int, optional): The height of the plot in pixels. Defaults to 600.
- `heading` (float, optional): The heading of the plot in degrees. Defaults to 0.0.

**Returns:**

A JSON string representation of the Plotly figure.

#### **/**
The / endpoint returns a simple HTML page with a Plotly plot of the obstruction adaptive elevation mask. The position is requested from the browser using the Geolocation API (https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API).

## Configuration
The configuration file is located at oaemapi/config.py. The following parameters can be set:

Example:
```python	
import logging
import numpy as np

OAEM_RES = np.deg2rad(1)

N_RANGE = 80
N_RES = 40

FAVICON_PATH = "./app/data/favicon.ico"

AREA_SHAPEFILE = "./app/data/area.shp"

GEOID_FILE = "./app/data/geoid.txt"
GEOID_EPSG = 4258
GEOID_RES = 100

WFS_EPSG = 25832
WFS_URL = "https://www.wfs.nrw.de/geobasis/wfs_nw_3d-gebaeudemodell_lod1"
WFS_BASE_REQUEST = "Service=WFS&REQUEST=GetFeature&VERSION=1.1.0&TYPENAME=bldg:Building"

APP_HOST = "0.0.0.0"
APP_PORT = 8000
logging.basicConfig(
    format="%(levelname)-8s %(asctime)s.%(msecs)03d - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="./oaemapi.log",
)
logger = logging.getLogger("root")

with open("./app/version", "r") as f:
    VERSION = f.read().strip()

```

* `OAEM_RES`: Resolution of the azimuth grid of the OAEM in radians.
* `APP_HOST`: Host of the server.
* `APP_PORT`: Port of the server.
* `FAVICON_PATH`: Path to the favicon
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