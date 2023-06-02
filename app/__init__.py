from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from app.config import GEOID_FILE
from app.geoid.geoid import Geoid, Interpolator

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
geoid = Geoid(filename=GEOID_FILE, interpolator=Interpolator.NEAREST)

from app import routes
