import logging
from time import time

import numpy as np
import plotly.graph_objects as go
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pointset import PointSet

from oaemapi.config import GEOID_FILE, HOST, LOG_FILE, LOG_LEVEL, PORT, VERSION
from oaemapi.core.oaem import Oaem, oaem_from_pointset
from oaemapi.geoid import Geoid, Interpolator

logging.basicConfig(
    format="%(levelname)-8s %(asctime)s.%(msecs)03d - %(message)s",
    level=LOG_LEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=LOG_FILE,
)

app = FastAPI()
templates = Jinja2Templates(directory="oaemapi/templates")

geoid: Geoid = None


def oaem_ellipsoidal_height(pos_x: float, pos_y: float, pos_z: float, epsg: int) -> Oaem:
    pos = PointSet(xyz=np.array([pos_x, pos_y, pos_z]), epsg=epsg, init_local_transformer=False)
    pos.z -= geoid.interpolate(pos=pos)
    return oaem_from_pointset(pos=pos)


@app.on_event("startup")
async def startup_event():
    global geoid
    geoid = Geoid(filename=GEOID_FILE, interpolator=Interpolator.NEAREST)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api")
async def oaem_request(pos_x: float, pos_y: float, pos_z: float, epsg: int):
    logging.debug("Received OAEM request")
    query_time = time()

    oaem = oaem_ellipsoidal_height(pos_x, pos_y, pos_z, epsg)
    oaem_str = str(oaem.az_el_str)
    logging.debug(f"Cache info: {oaem_from_pointset.cache_info()}")

    response_time = time()
    logging.debug(
        f"Computed OAEM for position [{pos_x:.3f}, {pos_y:.3f}, {pos_z:.3f}], EPSG: {epsg} in {(response_time-query_time)*1000:.3f} ms"
    )
    return {"Data": oaem_str}


@app.get("/plot")
async def plot(
    pos_x: float, pos_y: float, pos_z: float, epsg: int, width: int = 600, height: int = 600, heading: float = 0.0
):
    logging.info(
        f"Received plot request for position [{pos_x:.3f}, {pos_y:.3f}, {pos_z:.3f}], EPSG: {epsg}, heading: {heading:.3f} deg"
    )
    oaem = oaem_ellipsoidal_height(pos_x, pos_y, pos_z, epsg)
    fig = go.Figure(
        data=go.Scatterpolar(
            theta=np.rad2deg(oaem.azimuth),
            r=np.rad2deg(np.pi / 2 - oaem.elevation),
            mode="lines",
            text="Obstruction Adaptive Elevation Mask",
        ),
        layout=go.Layout(
            title={
                "text": f"Obstruction Adaptive Elevation Mask API {VERSION}",
                "x": 0.5,
                "y": 1,
                "xanchor": "center",
                "yanchor": "top",
                "font": {
                    "family": "Arial",
                    "size": 40,
                    "color": "black",
                },
            },
            polar=dict(
                angularaxis=dict(direction="clockwise", rotation=90 + heading),
                radialaxis=dict(angle=90),
            ),
            width=width,
            height=height,
            font=dict(size=30),
        ),
    )
    fig_json = fig.to_json()

    return {"plot": fig_json}


def main():
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
