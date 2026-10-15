import duckdb, pandas as pd

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")

for region in ["northern-ca", "eastern-ok", "maricopa-az", "eastern-wa", "south-central-tx"]:
    R = f"reference/{region}/{region}-"
    S = f"strata/{region}/{region}-"
    con.sql(f"""CREATE OR REPLACE TABLE tracts AS
      SELECT c.GEOID, s.ur_class, c.geometry,
             ST_XMin(c.geometry) xmin, ST_YMin(c.geometry) ymin,
             ST_XMax(c.geometry) xmax, ST_YMax(c.geometry) ymax
      FROM '{S}census-tracts.parquet' c
      JOIN '{S}strata-tract-table.parquet' s USING (GEOID)""")
    con.sql(f"""CREATE OR REPLACE TABLE p AS
      SELECT ST_X(ST_Centroid(geometry)) x, ST_Y(ST_Centroid(geometry)) y, "class" AS cls
      FROM '{R}overture-buildings.parquet'
      WHERE sources[1].dataset = 'OpenStreetMap'""")
    df = con.sql("""SELECT t.ur_class, p.cls, count(*) n
      FROM tracts t JOIN p
        ON p.x BETWEEN t.xmin AND t.xmax AND p.y BETWEEN t.ymin AND t.ymax
       AND ST_Intersects(t.geometry, ST_Point(p.x, p.y))
      GROUP BY 1, 2""").df()
    print(f"\n##### {region}: OpenStreetMap-sourced buildings only")
    for u, x in df.groupby("ur_class"):
        tot = x.n.sum()
        lab = x[x.cls.notna()].n.sum()
        print(f"\n{u}: {tot} OSM buildings, {100*lab/tot:.1f}% have a type label")
        top = x[x.cls.notna()].sort_values("n", ascending=False).head(6)
        print("  top labels:", ", ".join(f"{c} {100*n/tot:.1f}%" for c, n in zip(top.cls, top.n)))
