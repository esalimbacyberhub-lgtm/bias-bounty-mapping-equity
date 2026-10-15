import pandas as pd

frames = []
for region in ["northern-ca", "eastern-ok", "maricopa-az", "eastern-wa", "south-central-tx"]:
    d = pd.read_csv(f"consequence_{region}.csv", dtype={"GEOID": str, "COUNTYFP": str})
    d["region"] = region
    frames.append(d[["region", "GEOID", "ur_class", "pop_total", "class_share", "bld_share_OpenStreetMap"]])
a = pd.concat(frames, ignore_index=True)
a["class_share"] = a.class_share.fillna(0)
a["osm"] = a["bld_share_OpenStreetMap"].fillna(0)

print("--- Spearman: label share vs OSM share, by region ---")
for r, x in a.groupby("region"):
    print(r, round(x.class_share.corr(x.osm, method="spearman"), 3))

a["osm_bin"] = pd.cut(a.osm, [-0.001, 0.1, 0.5, 0.9, 1.0], labels=["0-10%", "10-50%", "50-90%", "90-100%"])

print("\n--- median label share and tract counts by OSM-share bin and urban/rural (all 3 regions pooled) ---")
t = a.groupby(["osm_bin", "ur_class"], observed=True).agg(
    tracts=("GEOID", "count"), median_label_share=("class_share", "median")).round(3)
print(t.to_string())

print("\n--- same, by region ---")
for r, x in a.groupby("region"):
    print("\n" + r)
    t = x.groupby(["osm_bin", "ur_class"], observed=True).agg(
        tracts=("GEOID", "count"), median_label_share=("class_share", "median")).round(3)
    print(t.to_string())
