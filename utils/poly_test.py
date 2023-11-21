from app.neighborhood import BoundingBox, Neighborhood
from matplotlib import pyplot as plt
import geopandas as gpd


def main():
    bbox1 = BoundingBox(min_x=0, min_y=0, max_x=2, max_y=2)
    bbox2 = BoundingBox(min_x=2, min_y=2, max_x=4, max_y=4)
    bbox3 = BoundingBox(min_x=1, min_y=1, max_x=3, max_y=3)
    bbox4 = BoundingBox(min_x=5, min_y=5, max_x=6, max_y=6)

    neighborhood = Neighborhood()

    for bbox in [bbox1, bbox2, bbox3, bbox4]:
        neighborhood.add_bounding_box(bbox)
        neighborhood.plot()

    bbox5 = BoundingBox(min_x=5.5, min_y=5.5, max_x=7, max_y=7)

    uncovered = neighborhood.uncovered(bbox5)

    gpd.GeoSeries([neighborhood.request_coverage, uncovered]).boundary.plot()

    print(uncovered)

    plt.show()


if __name__ == "__main__":
    main()
