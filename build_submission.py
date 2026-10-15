import numpy as np, pandas as pd

REGIONS = ["northern-ca", "eastern-ok", "maricopa-az", "eastern-wa", "south-central-tx"]
BASE, SCALE = 0.30, 0.08   # BASE is a guess, not derived from data

tpl = pd.read_csv("SampleSubmission.csv", dtype={"GEOID": str})
frames = []
for r in REGIONS:
    d = pd.read_csv(f"features_{r}.csv", dtype={"GEOID": str})
    d["region"] = r
    frames.append(d[["region", "GEOID", "ur_class", "pop_total", "land_km2",
                     "housing_units", "n_buildings", "n_pois", "road_km"]])
f = tpl[["GEOID", "region"]].merge(pd.concat(frames, ignore_index=True),
                                   on=["GEOID", "region"], how="left")
assert f.n_buildings.notna().all(), "some template tracts have no features"
f["ur_class"] = f.ur_class.fillna("Unknown")

def resid(y, xs):
    ly = np.log1p(f[y].astype(float).values)
    X = np.column_stack([np.ones(len(f))] +
                        [np.log1p(f[x].astype(float).fillna(0).values) for x in xs])
    out = np.zeros(len(f))
    for (reg, ur), g in f.groupby(["region", "ur_class"]):
        idx = g.index.values
        fit = idx if len(idx) >= 40 else f.index[f.region == reg].values
        beta, *_ = np.linalg.lstsq(X[fit], ly[fit], rcond=None)
        out[idx] = ly[idx] - X[idx] @ beta
    return out

f["r_bld"] = resid("n_buildings", ["housing_units", "land_km2"])
f["r_poi"] = resid("n_pois", ["pop_total", "land_km2"])
f["r_road"] = resid("road_km", ["land_km2", "pop_total"])

for c in ["r_bld", "r_poi", "r_road"]:
    f[c] = f.groupby("region")[c].transform(lambda s: ((s - s.mean()) / s.std()).clip(-3, 3))
f["z"] = f[["r_bld", "r_poi", "r_road"]].mean(axis=1)
f["z"] = f.groupby("region").z.transform(lambda s: (s - s.mean()) / s.std())

f["gap_B"] = (BASE - SCALE * f.z).clip(0, 1)
f["gap_B"] = (f.gap_B + (BASE - f.gap_B.mean())).clip(0, 1)
f["gap_A"] = BASE

for name, col in [("A_constant", "gap_A"), ("B_index", "gap_B")]:
    out = f[["GEOID"]].copy()
    out["coverage_gap_score"] = f[col].round(5)
    assert out.GEOID.nunique() == len(tpl) and set(out.GEOID) == set(tpl.GEOID)
    assert out.coverage_gap_score.notna().all()
    out.to_csv(f"submission_{name}.csv", index=False)
    print(name, out.shape, "mean", round(out.coverage_gap_score.mean(), 4),
          "min", out.coverage_gap_score.min(), "max", out.coverage_gap_score.max())

print("\nB by region:")
print(f.groupby("region").gap_B.agg(["count", "mean", "std", "min", "max"]).round(3).to_string())
print("\nB by urban/rural:")
print(f.groupby("ur_class").gap_B.agg(["count", "mean"]).round(3).to_string())
