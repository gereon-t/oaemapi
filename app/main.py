import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import VERSION
from app.routes import router

app = FastAPI(
    title="OAEM-API",
    version=VERSION,
)
app.include_router(router)
app.mount("/static", StaticFiles(directory="./app/static"), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
