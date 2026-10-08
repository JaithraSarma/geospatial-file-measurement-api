"""Reads a zipped shapefile (.shp/.shx/.dbf/.prj) into shapely geometries."""
import io
import zipfile

import shapefile
from pyproj import CRS
from shapely.geometry import shape as to_shape


def _find_member(names, suffix):
    suffix = suffix.lower()
    for name in names:
        # skip macOS zip junk: __MACOSX/ dirs and ._ AppleDouble shadow files
        basename = name.rsplit("/", 1)[-1]
        if name.startswith("__MACOSX/") or basename.startswith("._"):
            continue
        if name.lower().endswith(suffix):
            return name
    return None


def _crs_string(prj_text):
    try:
        crs = CRS.from_wkt(prj_text)
    except Exception:
        return None
    epsg = crs.to_epsg()
    if epsg:
        return f"EPSG:{epsg}"
    return crs.name or None


def read(data):
    """Read shapefile zip bytes. Returns (source_crs, features)."""
    zf = zipfile.ZipFile(io.BytesIO(data))
    names = zf.namelist()

    shp_name = _find_member(names, ".shp")
    if shp_name is None:
        raise ValueError("zip file does not contain a .shp member")
    dbf_name = _find_member(names, ".dbf")
    shx_name = _find_member(names, ".shx")
    prj_name = _find_member(names, ".prj")

    shp_buf = io.BytesIO(zf.read(shp_name))
    dbf_buf = io.BytesIO(zf.read(dbf_name)) if dbf_name else None
    shx_buf = io.BytesIO(zf.read(shx_name)) if shx_name else None

    reader = shapefile.Reader(shp=shp_buf, dbf=dbf_buf, shx=shx_buf)

    source_crs = None
    if prj_name:
        source_crs = _crs_string(zf.read(prj_name).decode("utf-8"))

    features = []
    for index, sr in enumerate(reader.iterShapeRecords()):
        geom = to_shape(sr.shape.__geo_interface__)
        features.append(
            {
                "index": index,
                "geometry": geom,
                "geometry_type": geom.geom_type,
                "properties": sr.record.as_dict(),
            }
        )

    return source_crs, features
