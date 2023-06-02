import uvicorn
from app import app
from app.config import HOST, PORT


def main():
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
