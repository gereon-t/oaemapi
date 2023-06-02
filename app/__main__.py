import logging
import uvicorn
from app import app
from app.config import HOST, LOG_FILE, LOG_LEVEL, PORT

logging.basicConfig(
    format="%(levelname)-8s %(asctime)s.%(msecs)03d - %(message)s",
    level=LOG_LEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=LOG_FILE,
)


def main():
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
