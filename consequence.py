import sys, duckdb, pandas as pd

region = sys.argv[1]
R = f"reference/{region}/{region}-"
S = f"strata/{region}/{region}-"

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
con.sql(f"""CREATE TABLE tracts AS
SELECT GEOID, geometry, ST_XMin(geometry) xmin, ST_YMin(geometry) ymin,
       ST_XMax(geometry) xmax, ST_YMax(geometry) ymax
FROM '{S}census-tracts.parquet'""")

def joined(layer, x, y, extra):
    con.sql(f"""CREATE OR REPLACE TABLE p AS
      SELECT {x} AS x, {y} AS y, {extra} FROM '{R}overture-{layer}.parquet'""")
    return con.sql("""SELECT t.GEOID, p.* EXCLUDE (x, y)
      FROM tracts t JOIN p
        ON p.x BETWEEN t.xmin AND t.xmax AND p.y BETWEEN t.ymin AND t.ymax
       AND ST_Intersects(t.geometry, ST_Point(p.x, p.y))""").df()

CX, CY = "ST_X(ST_Centroid(geometry))", "ST_Y(ST_Centroid(geometry))"
b = joined("buildings", CX, CY, 'sources[1].dataset AS ds, ("class" IS NOT NULL) AS has_class')
p = joined("pois", "ST_X(geometry)", "ST_Y(geometry)", "categories.primary AS cat")

print("--- share of buildings with a type label, by first-listed source ---")
print(b.groupby("ds").has_class.mean().round(3).to_string())

schools = {"elementary_school", "middle_school", "high_school", "school", "private_school", "public_school"}
p["fire"] = p.cat.eq("fire_department")
p["ems"] = p.cat.eq("ambulance_and_ems_services")
p["school"] = p.cat.isin(schools)
pt = p.groupby("GEOID")[["fire", "ems", "school"]].sum()
bt = b.groupby("GEOID").has_class.mean().rename("class_share")

d = pd.read_csv(f"features_{region}.csv", dtype={"GEOID": str, "COUNTYFP": str})
d = d.merge(bt, on="GEOID", how="left").merge(pt, on="GEOID", how="left")
d[["fire", "ems", "school"]] = d[["fire", "ems", "school"]].fillna(0)
d["tribal_any"] = d.tribal_any.fillna(False).astype(bool)
ml = "bld_share_Microsoft_ML_Buildings"

if "tribal_pct" in d:
    print("\n--- tribal_pct (to choose a stricter definition later) ---")
    print(d.tribal_pct.describe().round(2).to_string())

rows = []
for (c, u), x in d.groupby(["COUNTYFP", "ur_class"]):
    t, n = x[x.tribal_any], x[~x.tribal_any]
    if len(t) >= 5 and len(n) >= 5:
        for label, g in [("tribal", t), ("non-tribal", n)]:
            pop = g.pop_total.sum()
            rows.append(dict(county=c, ur=u, group=label, n=len(g),
                ml_share=round(g[ml].median(), 3), class_share=round(g.class_share.median(), 3),
                fire_10k=round(1e4 * g.fire.sum() / pop, 2), ems_10k=round(1e4 * g.ems.sum() / pop, 2),
                school_10k=round(1e4 * g.school.sum() / pop, 2)))
print("\n=== within county AND urban/rural class (5+ tracts in each group) ===")
res = pd.DataFrame(rows)
print(res.to_string(index=False) if len(res) else "no cells with 5+ tribal and 5+ non-tribal tracts")

d.to_csv(f"consequence_{region}.csv", index=False)
print("\nsaved", f"consequence_{region}.csv", d.shape)
