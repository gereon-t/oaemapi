import logging

N_RANGE = 50
N_RES = 0.05
N_MAX_DIST = 50

GEOID_FILE = "./app/geoid/data.txt"
GEOID_EPSG = 4258
GEOID_INTERP_EPSG = 25832
GEOID_RES = 20

WFS_EPSG = 25832
WFS_URL = "https://www.wfs.nrw.de/geobasis/wfs_nw_3d-gebaeudemodell_lod1"
WFS_BASE_REQUEST = "Service=WFS&REQUEST=GetFeature&VERSION=1.1.0&TYPENAME=bldg:Building"

HOST = "127.0.0.1"
PORT = 8000
LOG_LEVEL = logging.INFO
LOG_FILE = "./oaemapi.log"

OAEM_PARAM = 1.5
GRID_RES = 1e-4
WIN_SIZE = 3
FACE_INTERP_RES = 0.1

with open("./app/version", "r") as f:
    VERSION = f.read().strip()
