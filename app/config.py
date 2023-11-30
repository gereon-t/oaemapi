import logging

import numpy as np

OAEM_RES = np.deg2rad(1)

N_RANGE = 80
N_RES = 20

ROUNDING_EPSG = 25832

FAVICON_PATH = "./app/data/favicon.ico"

GEOID_FILE = "./app/data/geoid.txt"
GEOID_EPSG = 4258
GEOID_RES = 100

EDGE_SOURCE = "FILE"  # "WFS" or "FILE"
EDGE_DATA_PATH = "./data/bonn_lod2"
EDGE_LOD = 2  # 1 or 2
EDGE_EPSG = 25832

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
