from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
import logging
from app.geoid.geoid import Geoid, Interpolator
from app.config import GEOID_FILE, LOG_FILE, LOG_LEVEL


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
geoid = Geoid(filename=GEOID_FILE, interpolator=Interpolator.NEAREST)

logging.basicConfig(
    format="%(levelname)-8s %(asctime)s.%(msecs)03d - %(message)s",
    level=LOG_LEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=LOG_FILE,
)

from app import routes
