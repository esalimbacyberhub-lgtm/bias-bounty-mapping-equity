import numpy as np, pandas as pd

REGIONS = ["northern-ca", "eastern-ok", "maricopa-az", "eastern-wa", "south-central-tx"]
BASE, SCALE = 0.30, 0.05

tpl = pd.read_csv("SampleSubmission.csv", dtype={"GEOID": str})
frames = []
for r in REGIONS:
    d = pd.read_csv(f"features_{r}.csv", dtype={"GEOID": str})
    d["region"] = r
    if "bld_share_OpenStreetMap" not in d:
        print("WARNING: no OSM share column in", r)
        d["bld_share_OpenStreetMap"] = np.nan
    frames.append(d[["region", "GEOID", "bld_share_OpenStreetMap"]])
f = tpl[["GEOID", "region"]].merge(pd.concat(frames, ignore_index=True),
                                   on=["GEOID", "region"], how="left")
f["osm"] = f.bld_share_OpenStreetMap
print("missing OSM share:", int(f.osm.isna().sum()), "of", len(f))
f["osm"] = f.groupby("region").osm.transform(lambda s: s.fillna(s.median()))
f["z"] = f.groupby("region").osm.transform(lambda s: (s - s.mean()) / s.std()).clip(-3, 3)

f["gap_C"] = (BASE + SCALE * f.z).clip(0, 1)
f["gap_C"] = (f.gap_C + (BASE - f.gap_C.mean())).clip(0, 1)

out = f[["GEOID"]].copy()
out["coverage_gap_score"] = f.gap_C.round(5)
assert out.GEOID.nunique() == len(tpl) and set(out.GEOID) == set(tpl.GEOID)
assert out.coverage_gap_score.notna().all()
out.to_csv("submission_C_osm_share.csv", index=False)
print(out.shape, "mean", round(out.coverage_gap_score.mean(), 4),
      "min", out.coverage_gap_score.min(), "max", out.coverage_gap_score.max())
print(f.groupby("region").gap_C.agg(["count", "mean", "std"]).round(3).to_string())
