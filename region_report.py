import sys, re, duckdb, pandas as pd

region = sys.argv[1]
R = f"reference/{region}/{region}-"
S = f"strata/{region}/{region}-"

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
con.sql(f"""CREATE TABLE tracts AS
SELECT GEOID, geometry, ST_XMin(geometry) xmin, ST_YMin(geometry) ymin,
       ST_XMax(geometry) xmax, ST_YMax(geometry) ymax
FROM '{S}census-tracts.parquet'""")
print("tracts:", con.sql("SELECT count(*) FROM tracts").fetchone()[0])

def joined(layer, x, y, extra):
    con.sql(f"""CREATE OR REPLACE TABLE p AS
      SELECT {x} AS x, {y} AS y, {extra} FROM '{R}overture-{layer}.parquet'""")
    return con.sql("""SELECT t.GEOID, p.* EXCLUDE (x, y)
      FROM tracts t JOIN p
        ON p.x BETWEEN t.xmin AND t.xmax AND p.y BETWEEN t.ymin AND t.ymax
       AND ST_Intersects(t.geometry, ST_Point(p.x, p.y))""").df()

CX, CY = "ST_X(ST_Centroid(geometry))", "ST_Y(ST_Centroid(geometry))"
b = joined("buildings", CX, CY, "sources[1].dataset AS ds")
p = joined("pois", "ST_X(geometry)", "ST_Y(geometry)", "sources[1].dataset AS ds")
i = joined("infrastructure", CX, CY, "1 AS one")
# road length in km: always_xy is required or lengths come out as inf/NaN
r = joined("roads", CX, CY,
    "ST_Length(ST_Transform(geometry,'EPSG:4326','EPSG:5070', always_xy := true))/1000.0 AS km")

n_b = con.sql(f"SELECT count(*) FROM '{R}overture-buildings.parquet'").fetchone()[0]
n_p = con.sql(f"SELECT count(*) FROM '{R}overture-pois.parquet'").fetchone()[0]
print(f"--- totals: buildings {len(b)} (layer {n_b}), pois {len(p)} (layer {n_p}), road_km {r.km.sum():.1f} ---")
print("road_km finite:", bool(pd.Series(r.km).replace([float('inf'), float('-inf')], float('nan')).notna().all()))

f = pd.DataFrame({"GEOID": con.sql("SELECT GEOID FROM tracts").df()["GEOID"]})
f["n_buildings"] = f.GEOID.map(b.groupby("GEOID").size()).fillna(0)
f["n_pois"] = f.GEOID.map(p.groupby("GEOID").size()).fillna(0)
f["n_infra"] = f.GEOID.map(i.groupby("GEOID").size()).fillna(0)
f["road_km"] = f.GEOID.map(r.groupby("GEOID").km.sum()).fillna(0)

def shares(df, prefix, k=3):
    top = df.ds.value_counts().head(k).index.tolist()
    print(f"\n--- {prefix} first-listed source, overall ---")
    print(df.ds.value_counts().to_string())
    ct = pd.crosstab(df.GEOID, df.ds)
    out = ct[top].div(ct.sum(axis=1), axis=0)
    out.columns = [prefix + re.sub(r"\W+", "_", str(c)) for c in out.columns]
    return out.reset_index()

f = f.merge(shares(b, "bld_share_"), on="GEOID", how="left").merge(shares(p, "poi_share_"), on="GEOID", how="left")

s = con.sql(f"SELECT * FROM '{S}strata-tract-table.parquet'").df()
keep = [c for c in ["GEOID","COUNTYFP","pop_total","ALAND","ur_class","svi_overall","tribal_any","tribal_pct"] if c in s.columns]
a = con.sql(f"SELECT GEOID, housing_units FROM '{R}census-acs-housing.parquet'").df()
d = f.merge(s[keep], on="GEOID", how="left").merge(a, on="GEOID", how="left")
if "svi_overall" in d:
    d.loc[d.svi_overall < 0, "svi_overall"] = float("nan")
d["land_km2"] = d.ALAND / 1e6
d["bld_per_hu"] = d.n_buildings / d.housing_units.where(d.housing_units > 0)
d["road_km_per_km2"] = d.road_km / d.land_km2.where(d.land_km2 > 0)
d["pois_per_1000"] = d.n_pois / (d.pop_total.where(d.pop_total > 0) / 1000)
d.to_csv(f"features_{region}.csv", index=False)

share_cols = [c for c in d.columns if c.startswith(("bld_share_", "poi_share_"))]
ml = next((c for c in d.columns if "Microsoft_ML" in c and c.startswith("bld_share_")),
          next(c for c in d.columns if c.startswith("bld_share_")))
print("\nsource column used for the county tests:", ml)

for col in ["ur_class", "tribal_any"]:
    if col in d and d[col].nunique() > 1:
        print(f"\n=== median source share by {col} ===")
        g = d.groupby(col, observed=True)
        print(g[share_cols].median().round(3).T.to_string())
        print("n_tracts:", g.size().to_dict())

print(f"\n=== by county (10+ tracts): median {ml}, median SVI, tribal tracts ===")
cg = d.groupby("COUNTYFP").agg(n=("GEOID","count"), ml=(ml,"median"), svi=("svi_overall","median"),
        tribal=("tribal_any", lambda x: int(x.fillna(False).astype(bool).sum())) if "tribal_any" in d else ("GEOID","count"))
print(cg[cg.n >= 10].round(3).to_string())

print("\n=== within-county Spearman: SVI vs source share (counties with 25+ tracts) ===")
for c, x in d.groupby("COUNTYFP"):
    if len(x) >= 25:
        print(c, "n =", len(x), "spearman =", round(x.svi_overall.corr(x[ml], method="spearman"), 3))

if "tribal_any" in d:
    print("\n=== within-county tribal vs non-tribal median source share (5+ of each) ===")
    d["tribal_any"] = d.tribal_any.fillna(False).astype(bool)
    for c, x in d.groupby("COUNTYFP"):
        t, n = x[x.tribal_any], x[~x.tribal_any]
        if len(t) >= 5 and len(n) >= 5:
            print(c, "tribal n =", len(t), "median =", round(t[ml].median(), 3),
                  "| non-tribal n =", len(n), "median =", round(n[ml].median(), 3))
print("\nsaved", f"features_{region}.csv", d.shape)
