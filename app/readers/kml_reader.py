"""Reads KML placemarks into shapely geometries. KML is always lon/lat WGS84."""
from lxml import etree
from shapely.geometry import LineString, Point, Polygon


def _find(elem, tag):
    return elem.find(f".//{{*}}{tag}")


def _findall(elem, tag):
    return elem.findall(f".//{{*}}{tag}")


def _parse_coords(text):
    """Parse a KML coordinates string into a list of (lon, lat) tuples."""
    points = []
    for chunk in text.split():
        parts = chunk.split(",")
        lon, lat = float(parts[0]), float(parts[1])
        points.append((lon, lat))
    return points


def _parse_properties(placemark):
    props = {}
    name_el = _find(placemark, "name")
    if name_el is not None and name_el.text:
        props["name"] = name_el.text.strip()

    for data_el in _findall(placemark, "Data"):
        key = data_el.get("name")
        value_el = _find(data_el, "value")
        if key and value_el is not None:
            props[key] = value_el.text

    for simple_el in _findall(placemark, "SimpleData"):
        key = simple_el.get("name")
        if key:
            props[key] = simple_el.text

    return props


def _parse_geometry(placemark):
    point_el = _find(placemark, "Point")
    if point_el is not None:
        coords_el = _find(point_el, "coordinates")
        if coords_el is not None and coords_el.text:
            pts = _parse_coords(coords_el.text)
            if pts:
                return Point(pts[0])
        return None

    line_el = _find(placemark, "LineString")
    if line_el is not None:
        coords_el = _find(line_el, "coordinates")
        if coords_el is not None and coords_el.text:
            pts = _parse_coords(coords_el.text)
            if len(pts) >= 2:
                return LineString(pts)
        return None

    poly_el = _find(placemark, "Polygon")
    if poly_el is not None:
        outer_el = _find(poly_el, "outerBoundaryIs")
        if outer_el is None:
            return None
        outer_coords_el = _find(outer_el, "coordinates")
        if outer_coords_el is None or not outer_coords_el.text:
            return None
        exterior = _parse_coords(outer_coords_el.text)

        holes = []
        for inner_el in _findall(poly_el, "innerBoundaryIs"):
            inner_coords_el = _find(inner_el, "coordinates")
            if inner_coords_el is not None and inner_coords_el.text:
                holes.append(_parse_coords(inner_coords_el.text))

        if len(exterior) < 3:
            return None
        return Polygon(exterior, holes or None)

    return None


def read(data):
    """Read KML bytes or str. Returns (source_crs, features)."""
    if isinstance(data, str):
        data = data.encode("utf-8")

    # data comes straight from an upload, so disable entity/DTD loading to block XXE
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, dtd_validation=False)
    root = etree.fromstring(data, parser=parser)
    placemarks = root.findall(".//{*}Placemark")

    features = []
    index = 0
    for placemark in placemarks:
        geom = _parse_geometry(placemark)
        if geom is None:
            continue
        features.append(
            {
                "index": index,
                "geometry": geom,
                "geometry_type": geom.geom_type,
                "properties": _parse_properties(placemark),
            }
        )
        index += 1

    return "EPSG:4326", features
