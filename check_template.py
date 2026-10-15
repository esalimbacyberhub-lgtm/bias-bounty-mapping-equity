import os, pandas as pd

s = pd.read_csv("SampleSubmission.csv", dtype={"GEOID": str})
print("rows:", len(s), "| unique GEOID:", s.GEOID.nunique())
print("GEOID lengths:", s.GEOID.str.len().value_counts().to_dict())
print("\nrows per region in template:")
print(s.region.value_counts().to_string())
print("\ncolumns:", s.columns.tolist())

print("\n--- match against processed regions ---")
for r in ["northern-ca", "eastern-ok", "maricopa-az", "eastern-wa", "south-central-tx"]:
    f = f"features_{r}.csv"
    t = set(s.loc[s.region == r, "GEOID"])
    if os.path.exists(f):
        have = set(pd.read_csv(f, dtype={"GEOID": str}).GEOID)
        print(r, "| template:", len(t), "| processed:", len(have), "| in both:", len(t & have),
              "| only in template:", len(t - have), "| only in processed:", len(have - t))
    else:
        print(r, "| template:", len(t), "| not processed yet")
