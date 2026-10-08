"""Builders for test fixtures: in-memory shapefile zips and KML strings."""
import io
import zipfile

import shapefile

WGS84_WKT = (
    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
)


def make_shapefile_zip(shape_type=shapefile.POLYGON, records=None, prj_wkt=WGS84_WKT):
    """Build a zipped shapefile in memory and return the zip bytes.

    records is a list of (coords, field_values) tuples. coords is whatever
    pyshp wants for the given shape_type (a ring for polygon, a line for
    polyline, an (x, y) tuple for point).
    """
    if records is None:
        records = []

    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    writer = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shape_type)
    writer.field("name", "C")
    writer.field("val", "N")

    for coords, field_values in records:
        if shape_type == shapefile.POLYGON:
            writer.poly([coords])
        elif shape_type == shapefile.POLYLINE:
            writer.line([coords])
        elif shape_type == shapefile.POINT:
            writer.point(*coords)
        writer.record(*field_values)

    writer.close()

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("data.shp", shp.getvalue())
        zf.writestr("data.shx", shx.getvalue())
        zf.writestr("data.dbf", dbf.getvalue())
        if prj_wkt is not None:
            zf.writestr("data.prj", prj_wkt)

    return zip_buf.getvalue()


def make_polygon_shapefile_zip():
    coords = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
    return make_shapefile_zip(
        shape_type=shapefile.POLYGON,
        records=[(coords, ["plot1", 5])],
    )


def make_kml_bytes():
    kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>field-a</name>
      <ExtendedData>
        <Data name="crop"><value>wheat</value></Data>
      </ExtendedData>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              77.0,12.0,0 77.0,12.01,0 77.01,12.01,0 77.01,12.0,0 77.0,12.0,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
    <Placemark>
      <name>road-a</name>
      <ExtendedData>
        <Data name="surface"><value>gravel</value></Data>
      </ExtendedData>
      <LineString>
        <coordinates>
          77.0,12.0,0 77.02,12.02,0
        </coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>point-a</name>
      <Point>
        <coordinates>77.0,12.0,0</coordinates>
      </Point>
    </Placemark>
    <Placemark>
      <name>no-geom</name>
    </Placemark>
  </Document>
</kml>
"""
    return kml.encode("utf-8")
