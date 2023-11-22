import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import routes
from app.config import VERSION

app = FastAPI(
    title="OAEM-API",
    version=VERSION,
    docs_url=None,
    edoc_url=None,
)
app.include_router(routes.router)
app.mount("/static", StaticFiles(directory="./app/static"), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
