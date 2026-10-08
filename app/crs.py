import shapely
from pyproj import CRS, Transformer


def utm_epsg_for(lon: float, lat: float) -> int:
    """UTM zone EPSG code for a lon/lat point."""
    zone = int((lon + 180) / 6) + 1
    return (32600 if lat >= 0 else 32700) + zone


def pick_projected_crs(geoms, source_crs) -> CRS:
    """Pick a projected CRS to measure in.

    If source_crs is already projected, use it as-is. Otherwise pick a UTM
    zone from the centroid of all the geometries combined.
    """
    crs = CRS.from_user_input(source_crs) if source_crs else CRS.from_epsg(4326)
    if not crs.is_geographic:
        return crs

    xs, ys = [], []
    for g in geoms:
        if g is None or g.is_empty:
            continue
        c = g.centroid
        xs.append(c.x)
        ys.append(c.y)
    lon = sum(xs) / len(xs) if xs else 0.0
    lat = sum(ys) / len(ys) if ys else 0.0
    return CRS.from_epsg(utm_epsg_for(lon, lat))


def transform_geom(geom, src_crs, dst_crs):
    """Reproject a shapely geometry from src_crs to dst_crs."""
    src = CRS.from_user_input(src_crs)
    dst = CRS.from_user_input(dst_crs)
    if src == dst:
        return geom
    transformer = Transformer.from_crs(src, dst, always_xy=True)
    return shapely.transform(geom, transformer.transform, interleaved=False)
