import argparse
from dataclasses import dataclass
import os
import xmltodict
from tqdm import tqdm
import pandas as pd


@dataclass
class DummyParser:
    path: str = "data/bonn_lod2"
    out: str = "bonn_lod2.csv"


def handle_surface_member(surface_member: dict) -> list[tuple[float]]:
    polygon = (
        surface_member.get("gml:Polygon", {})
        .get("gml:exterior", {})
        .get("gml:LinearRing", {})
        .get("gml:posList", {})
        .get("#text")
    )

    if polygon is None:
        return []

    coords = [float(c) for c in polygon.split(" ")]

    if len(coords) % 3 != 0:
        return []

    if len(coords) < 6:
        return []

    return [coords[i : i + 6] for i in range(0, len(coords) - 3, 3)]


def extract_roof_surface(surface: dict) -> list[tuple[float]]:
    surface_members = (
        surface.get("bldg:lod2MultiSurface", {})
        .get("gml:MultiSurface", {})
        .get("gml:surfaceMember", [])
    )

    if not surface_members:
        return []

    coords = []

    if isinstance(surface_members, list):
        for surface_member in surface_members:
            coords.extend(handle_surface_member(surface_member))
    else:
        coords.extend(handle_surface_member(surface_members))

    return coords


def gml2geocollection(gml: str) -> list[tuple[float]]:
    data = xmltodict.parse(gml)

    if "core:CityModel" not in data:
        return ""

    if "core:cityObjectMember" not in data["core:CityModel"]:
        return ""

    building_coordinates = []

    buildings = data["core:CityModel"]["core:cityObjectMember"]

    if not isinstance(buildings, list):
        buildings = [buildings]

    for bdata in buildings:
        if "bldg:Building" not in bdata:
            continue

        building = bdata["bldg:Building"]

        if "bldg:boundedBy" not in building:
            continue

        bounded_by = building["bldg:boundedBy"]

        for surfaces in bounded_by:
            for surface in surfaces.values():
                building_coordinates.extend(extract_roof_surface(surface))

    return building_coordinates


def main() -> None:
    # parser = argparse.ArgumentParser()

    # parser.add_argument("--path", type=str, required=True, help="Path to GML files")
    # parser.add_argument("--out", type=str, required=True, help="Output File")
    # args = parser.parse_args()
    args = DummyParser()
    filepath: str = args.path
    outpath: str = os.path.abspath(args.out)
    dirpath: str = os.path.dirname(outpath)

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    file_coordinates = []
    for file in tqdm(os.listdir(filepath)):
        if not file.endswith(".gml"):
            continue

        with open(os.path.join(filepath, file), "r", encoding="utf-8") as f:
            data = f.read()
            file_coordinates.extend(gml2geocollection(data))

    # write all coordinates to file
    df = pd.DataFrame(file_coordinates)
    df.to_csv(outpath, index=False, header=False)


if __name__ == "__main__":
    main()
