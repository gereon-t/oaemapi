<div align="center">
<h1>Obstruction Adaptive Elevation Mask API</h1>

#### API to query an Obstruction Adaptive Elevation Mask (OAEM) for a given position using CityGML models.

<img src="images/oaemapi.jpg" width=400/>
</div>

An Obstruction Adaptive Elevation Mask (OAEM) describes the obstruction of the sky view, e.g. due to buildings, using azimuth and elevation pairs. The term Obstruction Adaptive Elevation Mask was first used by [Zimmermann 2019](https://www.researchgate.net/publication/329833465_GPS-Multipath_Analysis_using_Fresnel-Zones). The CityGML models are XML based representations of buildings and can either be retrieved from [local file storage](https://www.opengeodata.nrw.de/produkte/geobasis/3dg/lod2_gml/lod2_gml/) or from the [Web-Feature-Service (WFS) of Geobasis North Rhine-Westphalia (NRW)](https://www.wfs.nrw.de/geobasis/wfs_nw_3d-gebaeudemodell_lod1). The code is designed for LOD1 or LOD2 building models from Geobasis NRW, Germany. In its current state, it is therefore only applicable within North Rhine-Westphalia, Germany.

An OAEM can be useful in various scenarios including GNSS Signal filtering:

![](images/oaem.gif)

This software uses and includes the Quasigeoid from:

> © [BKG](https://www.bkg.bund.de/) (Jahr des letzten Datenbezugs) [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) , Datenquellen: https://sgx.geodatenzentrum.de/web_public/Datenquellen_Quasigeoid.pdf


## Install and run

Using Docker Compose:

```yaml
services:
  oaemapi:
    image: gtombrink/oaemapi:latest
    ports:
      - "8000:8000"
    volumes:
      - ./gmldata:/app/gmldata
      - ./config.py:/app/config.py

volumes:
  gmldata:
```

Start the container with:

```bash
docker-compose up -d
```

The CityGML data is stored in the gmldata volume. The config.py file is mounted to the container to configure the API. The API is then available at http://localhost:8000.



## Endpoints

In summary, the following endpoints are available:

| Endpoint | Description |
| --- | --- |
| / | Very simple frontend showing a skyplot at the current user location with the OAEM and the current sun position. |
| /oaem | Returns the OAEM for a given position. |
| /plot | Returns a plot of the OAEM for a given position. |
| /sunvis | Returns the sun visibility for a given position. |

You can find detailed information about the Endpoints at http://127.0.0.1:8000/docs after starting the server.

## Configuration

Configuration is done in the config.py file:

```python
import logging

import numpy as np

OAEM_RES = np.deg2rad(1)  # resolution of the OAEM grid in radians

N_RANGE = 80  # neighborhood radius in meters
N_RES = 20  # request neighborhood every N_RES meters

ROUNDING_EPSG = 25832  # EPSG code of the coordinate system used for rounding (relevant for N_RES)

FAVICON_PATH = "./app/data/favicon.ico"

GEOID_FILE = "./app/data/geoid.txt" # needs to be downloaded from BKG
GEOID_EPSG = 4258
GEOID_RES = 100

EDGE_SOURCE = "FILE"  # "WFS" or "FILE"
EDGE_DATA_PATH = "./gmldata"  # only relevant if EDGE_SOURCE == "FILE"
EDGE_LOD = 2  # 1 or 2, 2 includes roof shapes and more detailed buildings but is slower
EDGE_EPSG = 25832  # EPSG of the CityGML data source

WFS_EPSG = 25832
WFS_URL = "https://www.wfs.nrw.de/geobasis/wfs_nw_3d-gebaeudemodell_lod1"
WFS_BASE_REQUEST = "Service=WFS&REQUEST=GetFeature&VERSION=1.1.0&TYPENAME=bldg:Building"

APP_HOST = "0.0.0.0"
APP_PORT = 8000
logging.basicConfig(
    format="%(levelname)-8s %(asctime)s.%(msecs)03d - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    # filename="./oaemapi.log",
)
logger = logging.getLogger("root")

with open("./app/version", "r", encoding="utf-8") as f:
    VERSION = f.read().strip()
```

The geoid file is available at [BKG](https://gdz.bkg.bund.de/index.php/default/quasigeoid-der-bundesrepublik-deutschland-quasigeoid.html). The CityGML data can be downloaded from [Geobasis NRW](https://www.opengeodata.nrw.de/produkte/geobasis/3dg/lod2_gml/lod2_gml/). The data is available under the [DL-DE->Zero-2.0](https://www.govdata.de/dl-de/zero-2-0) license. Alternatively, the data can be retrieved from the [WFS of Geobasis NRW](https://www.wfs.nrw.de/geobasis/wfs_nw_3d-gebaeudemodell_lod1) by setting `EDGE_SOURCE` to `FILE`. The WFS is only available for LOD1 buildings.