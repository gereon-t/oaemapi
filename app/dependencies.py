from .config import (
    logger,
    EDGE_DATA_PATH,
    EDGE_EPSG,
    EDGE_LOD,
    EDGE_SOURCE,
    GEOID_EPSG,
    GEOID_FILE,
)
from .geoid import Geoid
from .edge_provider import LocalEdgeProvider, WFSEdgeProvider

geoid = Geoid(filename=GEOID_FILE, epsg=GEOID_EPSG)

if EDGE_SOURCE == "FILE":
    edge_provider = LocalEdgeProvider(data_path=EDGE_DATA_PATH, epsg=EDGE_EPSG, lod=EDGE_LOD)
    logger.info("Using local edge data from %s", EDGE_DATA_PATH)
else:
    edge_provider = WFSEdgeProvider()
    logger.info("Using WFS edge data")
