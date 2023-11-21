from app.config import (EDGE_DATA_PATH, EDGE_EPSG, EDGE_LOD, EDGE_SOURCE,
                        GEOID_EPSG, GEOID_FILE)
from app.edge_provider import LocalEdgeProvider, WFSEdgeProvider
from app.geoid import Geoid

geoid = Geoid(filename=GEOID_FILE, epsg=GEOID_EPSG)

if EDGE_SOURCE == "FILE":
    edge_provider = LocalEdgeProvider(
        data_path=EDGE_DATA_PATH, epsg=EDGE_EPSG, lod=EDGE_LOD
    )
else:
    edge_provider = WFSEdgeProvider()
