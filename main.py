import logging
from functools import lru_cache
from time import time

import numpy as np
from fastapi import FastAPI
from pointset import PointSet

from oaemapi.geoid import Geoid, Interpolator
from oaemapi.neighborhood import Neighborhood
from oaemapi.oaem import Oaem

NRANGE = 50
GEOID_FILE = "./oaemapi/GCG2016NRW.txt"

logging.basicConfig(
    format="%(levelname)-8s %(asctime)s.%(msecs)03d - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI()
geoid: Geoid = None


@app.on_event("startup")
async def startup_event():
    global geoid
    geoid = Geoid(filename=GEOID_FILE, interpolator=Interpolator.NEAREST)


@app.get("/")
async def oaem_request(pos_x: float, pos_y: float, pos_z: float, epsg: int):
    logging.info("Received OAEM request")
    query_time = time()
    oaem = get_oaem(f"{pos_x},{pos_y},{pos_z}", epsg)
    oaem_str = str(oaem.az_el_str)
    logging.info(f"Cache info: {get_oaem.cache_info()}")

    response_time = time()
    logging.info(
        f"Computed OAEM for position [{pos_x:.3f}, {pos_y:.3f}, {pos_z:.3f}], EPSG: {epsg} in {(response_time-query_time)*1000:.3f} ms"
    )
    return {"Data": oaem_str}


@lru_cache(maxsize=4096)
def get_oaem(position: str, epsg: int) -> Oaem:
    pos = PointSet(xyz=np.fromstring(position, sep=",", dtype=float), epsg=epsg, init_local_transformer=False)
    pos.z -= geoid.interpolate(pos=pos.round_to(20))
    neighborhood = Neighborhood(pos=pos, nrange=NRANGE)
    return Oaem.from_neighborhood(neighborhood=neighborhood)
