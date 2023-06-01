import logging
from functools import lru_cache
from time import time

import numpy as np
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pointset import PointSet
from oaemapi.config import GEOID_FILE, HOST

from oaemapi.geoid import Geoid, Interpolator
from oaemapi.neighborhood import Neighborhood
from oaemapi.oaem import Oaem
import plotly.graph_objects as go

logging.basicConfig(
    format="%(levelname)-8s %(asctime)s.%(msecs)03d - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI()
templates = Jinja2Templates(directory="oaemapi/templates")

geoid: Geoid = None


@app.on_event("startup")
async def startup_event():
    global geoid
    geoid = Geoid(filename=GEOID_FILE, interpolator=Interpolator.NEAREST)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api")
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


@app.get("/plot")
async def plot(pos_x: float, pos_y: float, pos_z: float, epsg: int, width: int = 600, height: int = 600):
    oaem = get_oaem(f"{pos_x},{pos_y},{pos_z}", epsg)

    fig = go.Figure(
        data=go.Scatterpolar(
            theta=np.rad2deg(oaem.azimuth),
            r=np.rad2deg(np.pi / 2 - oaem.elevation),
            mode="lines",
            text="Obstruction Adaptive Elevation Mask",
        ),
        layout=go.Layout(
            autosize=True,
            polar=dict(
                angularaxis=dict(direction="clockwise", rotation=90),
                radialaxis=dict(angle=90),
            ),
            width=width,
            height=height,
        ),
    )
    fig_json = fig.to_json()

    return {"plot": fig_json}


@lru_cache(maxsize=4096)
def get_oaem(position: str, epsg: int) -> Oaem:
    pos = PointSet(xyz=np.fromstring(position, sep=",", dtype=float), epsg=epsg, init_local_transformer=False)
    logging.info(f"Received position: {pos.xyz}")
    pos.z -= geoid.interpolate(pos=pos)
    neighborhood = Neighborhood(pos=pos)
    return Oaem.from_neighborhood(neighborhood=neighborhood)


def main():
    import uvicorn

    uvicorn.run(app, host=HOST, port=8000)
