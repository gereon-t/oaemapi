from dataclasses import dataclass, field

import geopandas as gpd
from shapely.geometry import Polygon


@dataclass
class BoundingBox:
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0

    @property
    def polygon(self) -> Polygon:
        return Polygon(
            [
                (self.min_x, self.min_y),
                (self.max_x, self.min_y),
                (self.max_x, self.max_y),
                (self.min_x, self.max_y),
            ]
        )


@dataclass
class Neighborhood:
    request_coverage: Polygon = field(init=False, default_factory=Polygon)

    def add_bounding_box(self, bounding_box: BoundingBox) -> None:
        self.request_coverage = self.request_coverage.union(bounding_box.polygon)

    def uncovered(self, bounding_box: BoundingBox) -> bool:
        return bounding_box.polygon - self.request_coverage

    def plot(self) -> None:
        gpd.GeoSeries([self.request_coverage]).boundary.plot()
