from datetime import timedelta
import numpy as np
from pointset import PointSet
from app.core.oaem import Oaem
from app.core.sunspan import SunSpan

pos = PointSet(xyz=np.array([50.816614, 6.121062, 110]), epsg=4326)
sunspan = SunSpan.from_position(pos=pos, sym_half_range=timedelta(hours=6))

oaem = Oaem(pos=pos)
oaem.elevation += np.random.rand(len(oaem.elevation)) * np.pi / 2
sunspan.intersect_with_oaem(oaem)

print(
    f"Sun is visible between: {sunspan.sun_start: .3f} and {sunspan.sun_end: .3f} ({sunspan.sun_end - sunspan.sun_start:.3f} seconds)"
)
