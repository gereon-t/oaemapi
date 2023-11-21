from functools import lru_cache
import xmltodict


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


def parse_building_bounds(bounds: dict) -> list[float]:
    building_coordinates = []
    for surfaces in bounds:
        for surface in surfaces.values():
            building_coordinates.extend(extract_roof_surface(surface))

    return building_coordinates


def parse_building_data(building_data: dict) -> list[float]:
    if "bldg:Building" not in building_data:
        return []

    building = building_data["bldg:Building"]

    building_coordinates = []
    if "bldg:boundedBy" in building:
        bounded_by = [building["bldg:boundedBy"]]
        for bounds in bounded_by:
            building_coordinates.extend(parse_building_bounds(bounds))

    if "bldg:consistsOfBuildingPart" in building:
        building_parts = building["bldg:consistsOfBuildingPart"]
        for part in building_parts:
            building_part = part["bldg:BuildingPart"]
            bounds = building_part["bldg:boundedBy"]
            building_coordinates.extend(parse_building_bounds(bounds))

    return building_coordinates


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
        building_coordinates.extend(parse_building_data(bdata))

    return building_coordinates


@lru_cache(maxsize=128)
def parse_citycml_lod2(filepath: str) -> list[float]:
    if not filepath.endswith(".gml"):
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()
        return gml2geocollection(data)


def main() -> None:
    filepath = "data/bonn_lod2/LoD2_32_364_5621_1_NW.gml"

    coords = parse_citycml_lod2(filepath)


if __name__ == "__main__":
    main()
