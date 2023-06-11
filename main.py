from fastapi import FastAPI
from app import routes
from app.config import VERSION

app = FastAPI(title="OAEM-API", version=VERSION)
app.include_router(routes.router)
