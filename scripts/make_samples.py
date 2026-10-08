"""Generates the two sample files under sample_data/ for manual testing.

Run with: ./.venv/Scripts/python.exe scripts/make_samples.py

Makes a KML (polygon + linestring, roughly Bangalore) and a zipped shapefile
(polygon + line, roughly central London) in plain EPSG:4326.
"""
import io
import zipfile
from pathlib import Path

import shapefile

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"

KML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Bangalore sample</name>
    <Placemark>
      <name>Cubbon Park (made up boundary)</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              77.5920,12.9780,0 77.5970,12.9780,0 77.5970,12.9740,0 77.5920,12.9740,0 77.5920,12.9780,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
    <Placemark>
      <name>MG Road (made up route)</name>
      <LineString>
        <coordinates>
          77.6050,12.9760,0 77.6090,12.9748,0 77.6130,12.9735,0
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
"""


def write_kml():
    path = SAMPLE_DIR / "bangalore_sample.kml"
    path.write_text(KML_TEMPLATE, encoding="utf-8")
    return path


def write_shapefile_zip():
    # a .shp file can only hold one shape type (that's the format, not a pyshp
    # limitation), so this sample is two polygons rather than a polygon + a line -
    # the KML sample already covers the linestring case.
    shp_buf, shx_buf, dbf_buf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    writer = shapefile.Writer(shp=shp_buf, shx=shx_buf, dbf=dbf_buf, shapeType=shapefile.POLYGON)
    writer.field("name", "C")

    # a block near St James's Park, London
    writer.poly([[(-0.1348, 51.5020), (-0.1300, 51.5020), (-0.1300, 51.4990),
                   (-0.1348, 51.4990), (-0.1348, 51.5020)]])
    writer.record(name="St James's block")

    # a second plot nearby, just so feature_count > 1
    writer.poly([[(-0.1200, 51.5090), (-0.1150, 51.5090), (-0.1150, 51.5060),
                   (-0.1200, 51.5060), (-0.1200, 51.5090)]])
    writer.record(name="Green Park block")
    writer.close()

    prj_wkt = (
        'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,'
        '298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
    )

    zip_path = SAMPLE_DIR / "survey.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("survey.shp", shp_buf.getvalue())
        zf.writestr("survey.shx", shx_buf.getvalue())
        zf.writestr("survey.dbf", dbf_buf.getvalue())
        zf.writestr("survey.prj", prj_wkt)
    return zip_path


if __name__ == "__main__":
    SAMPLE_DIR.mkdir(exist_ok=True)
    kml_path = write_kml()
    zip_path = write_shapefile_zip()
    print(f"wrote {kml_path}")
    print(f"wrote {zip_path}")
