from app.config import WFS_EPSG, AREA_SHAPEFILE, GEOID_FILE
from app.core.geoid import Geoid, Interpolator


geoid = Geoid(filename=GEOID_FILE, interpolator=Interpolator.NEAREST)

if AREA_SHAPEFILE:
    import geopandas as gpd

    area_of_operation = gpd.read_file(AREA_SHAPEFILE)
    area_of_operation.to_crs(epsg=WFS_EPSG, inplace=True)
else:
    area_of_operation = None
