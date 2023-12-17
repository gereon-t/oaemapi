import logging

import numpy as np

OAEM_RES = np.deg2rad(1)  # resolution of the OAEM grid in radians

N_RANGE = 80  # neighborhood radius in meters
N_RES = 20  # request neighborhood every N_RES meters

ROUNDING_EPSG = 25832  # EPSG code of the coordinate system used for rounding (relevant for N_RES)

FAVICON_PATH = "./app/data/favicon.ico"

GEOID_FILE = "./app/data/geoid.txt"
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
