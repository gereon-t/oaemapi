import logging
import numpy as np

OAEM_RES = np.deg2rad(1)

N_RANGE = 150
N_RES = 50

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
