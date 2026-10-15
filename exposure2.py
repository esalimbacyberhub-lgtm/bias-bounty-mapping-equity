import pandas as pd

for region in ["northern-ca", "eastern-ok", "maricopa-az", "eastern-wa", "south-central-tx"]:
    d = pd.read_csv(f"consequence_{region}.csv", dtype={"GEOID": str, "COUNTYFP": str})
    d["tribal_any"] = d.tribal_any.fillna(False).astype(bool)
    d["class_share"] = d.class_share.fillna(0)
    print(f"\n##### {region}: % of residents in label-poor tracts, by cutoff and urban/rural")
    for cut in [0.01, 0.05, 0.10, 0.25]:
        row = []
        for u, x in d.groupby("ur_class"):
            row.append(f"{u} {100*x.loc[x.class_share < cut, 'pop_total'].sum()/x.pop_total.sum():.1f}")
        print(f"cutoff {int(cut*100)}%: " + " | ".join(row))
    if region == "eastern-ok":
        print("\n--- eastern-ok: tribal vs non-tribal WITHIN urban/rural (cutoff 5%) ---")
        for u, x in d.groupby("ur_class"):
            for t, g in x.groupby("tribal_any"):
                pct = 100 * g.loc[g.class_share < 0.05, "pop_total"].sum() / g.pop_total.sum()
                print(f"{u} tribal={t}: tracts={len(g)}, pop={int(g.pop_total.sum())}, pct label-poor={pct:.1f}")
