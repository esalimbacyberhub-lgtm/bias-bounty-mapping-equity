# Bias Bounty notes (Northern CA first pass)
- Features per tract: buildings (centroid in tract), POIs, infra, road km (length by segment midpoint). Totals match source layers (POIs +4 from border double counts, road km -0.4%).
- No labels provided, so any gap score is a designed estimate, not a trained model.
- Raw density by urban/rural, tribal, SVI: mostly reflects settlement pattern, not mapping gaps.
- Lead: first-listed building source (Microsoft ML vs OSM) differs by community type.
- Check: pooled urban SVI gradient (15% to 45% ML share) is mostly a county composition effect.
  Within-county Spearman: 113=0.00, 067=-0.03, 007=0.10, 061=0.32, 089=0.40.
- Source differs hugely by county (2% to 94% ML share). Not yet shown to harm anyone.
- Simplification: "source" = first-listed entry in the sources list.

# Eastern OK (region_report.py)
- Totals match layers. Source dominance varies by county (2% to 98% ML share), replicating NCA.
- SVI vs ML share within county: mixed signs (-0.25 to +0.35). No gradient. Dropped.
- Tribal vs non-tribal within county (ML share): 017: 0.42 vs 0.09; 027: 0.95 vs 0.26; 109: 0.75 vs 0.02.
- Caveat: tribal_any covers 805 of 1192 tracts (68%), likely broad overlap. Need to control for urban/rural.

# Eastern OK consequence test (consequence.py)
- Type labels: OSM 33% filled, Microsoft ML 0%, Esri 0%. (NCA: OSM ~25%, ML 0%.) ML footprints do carry height.
- tribal_pct is ~binary (0 or 1); tribal_any = 68% of tracts. Within county x urban/rural, tribal vs non-tribal ML share:
  017 urban 0.31 vs 0.09; 109 urban 0.90 vs 0.02 (n 8 vs 238); 109 rural 0.32 vs 0.46 (reversed). Inconsistent, dropped.
- Fire/EMS/school places per 10k: no deficit in tribal tracts (tiny counts).
- Surviving lead: building type labels exist almost only where OSM supplies the footprint; source mix varies by county and is more ML-heavy in rural tracts.
- TODO: get the correct SampleSubmission.csv from the Zindi Data tab (earlier two files were from other challenges).

# Exposure (exposure.py): % residents in tracts with <5% of buildings type-labelled
- NCA: rural 75.5, urban 51.2. EOK: rural 89.4, urban 57.6. Replicates; labels scarce everywhere, scarcest rural.
- Tribal: EOK 71.5 vs 61.5 (likely rural confound, to test). NCA tribal n=15 tracts, no valid comparison.

# Exposure robustness (exposure2.py)
- Rural > urban share of residents in label-poor tracts at cutoffs 1/5/10/25% in NCA and EOK.
- EOK tribal vs non-tribal WITHIN urban/rural: rural 89.3 vs 90.8, urban 56.5 vs 58.8. Tribal gap was a rural confound. Dropped.
- Framing for writeup: provenance (which upstream source supplies footprints) and attribute availability, not just urban/rural.

# Maricopa replication (3 regions now)
- Residents in tracts with <5% of buildings type-labelled: rural vs urban. NCA 75.5/51.2, EOK 89.4/57.6, MAR 61.2/25.1. Same direction at 1/5/10/25% cutoffs.
- Maricopa urban footprints are ~96% OSM; OSM is the only source with type labels (46.7% filled). Suggests provenance is the mechanism.
- Maricopa: only 163 rural tracts; tribal flag covers 37 tracts (likely rural confound), not reported.
- Totals check: buildings exact, POIs +3 (border), road_km finite.
- TODO: test whether rural/urban label gap vanishes at equal OSM share (exposure3.py).

# exposure3.py: label share vs OSM share, urban vs rural
- Spearman (label share vs OSM share): EOK 0.72, MAR 0.45, NCA 0.38. Labels follow OSM.
- Hypothesis "provenance fully explains rural gap" REJECTED: pooled, urban > rural label share in every OSM-share bin
  (0-10%: .011/.004; 10-50%: .061/.027; 50-90%: .161/.051; 90-100%: .497/.072).
- Within-region: MAR 90-100% bin rural .061 vs urban .617 (n=24 vs 1039); EOK 10-50% .029 vs .065; NCA 50-90% tie, MAR 0-10% reversed (tiny n).
- Pooled table dominated by MAR in top bin; use by-region tables.
- Next: what do OSM building labels look like, urban vs rural (osm_labels.py).

# osm_labels.py: type-label rate among OSM-sourced buildings only
- Rural vs urban % labelled: NCA 19.6/25.6, EOK 24.9/36.8, MAR 22.7/49.3. Gap persists with source held fixed.
- Labels mostly "house"; urban has more apartments/retail/commercial, rural more barn/shed/industrial.
- Cannot show why, and cannot show harm to emergency response (class does not identify schools/hospitals/care homes).
- Remaining: eastern-wa, south-central-tx; correct SampleSubmission.csv from Zindi Data tab.

# Eastern WA (region_report.py, consequence.py)
- Sizes match bucket. Buildings 1,081,345 vs layer 1,081,346; POIs +1; road_km finite.
- Source mix: rural OSM 0.40 / ML 0.60; urban OSM 0.81 / ML 0.06. Same direction as other regions.
- Tribal ~3% of tracts, no valid comparison cells. Not reported.

# Eastern WA exposure + OSM-only labels
- Residents in label-poor tracts (<5%): rural 76.5 vs urban 42.2. Same direction at 1/5/10/25% cutoffs.
- OSM-only buildings with a type label: rural 15.7% vs urban 24.7%.
- 4 of 4 regions replicate so far (NCA, EOK, MAR, EWA). Texas pending.

# Zindi SampleSubmission.csv (correct file, from Data tab)
- 9,794 rows = all five regions scored (incl. eastern-wa). Columns: GEOID, coverage_gap_score, region, + optional component/defined columns. Values are placeholder zeros.
- Earlier files with ID,TargetF1,TargetRAUC / ID,Target belonged to other challenges.
- Texas job survived the shell closing; features and consequence files saved with 6010 tracts (template scores 6003; 7 water tracts dropped per README).

# Submission C (build_submission_C.py)
- Idea: tracts whose buildings come mostly from OpenStreetMap get a higher gap score; per-region z-score of OSM building share, mean 0.30, sd 0.05, clipped to [0,1].
- Decided before seeing the score: one test only, no sign-flipping or tuning of 0.30/0.05 against the public leaderboard.
- 2 of 9,794 tracts had no OSM share (filled with region median).
- C public RMSE: 0.263559579 (worse than A)

# Submissions (public leaderboard RMSE, ~30% of tracts)
- A constant 0.30: RMSE 0.256160316
- B peer-relative sparsity index (mean 0.30, sd 0.08): RMSE 0.267415119 (worse than A)
- Implied correlation of B's index with the true score is about -0.01, i.e. none. Peer-relative density (buildings/POIs/roads vs similar tracts) does not predict the coverage gap.
- A's score implies the true scores have a large spread (sd up to ~0.25); my assumed 0.08 spread was far too narrow.
- Rule followed: no reference layers used, no probing with extra constants.

# What A, B, C imply (same mean 0.30, so differences = tract-to-tract variation only)
- Public RMSE: A 0.256160316, C 0.263559579, B 0.267415119.
- Implied link with true score: B ~ +0.01 (none; earlier note said -0.01, corrected), C ~ -0.05 (wrong direction, weak).
- With links this weak, added spread costs more than it gains: even flipping C would give RMSE ~0.258, still worse than A.
- No further guessing submissions: avoid tuning to the public leaderboard.

# Texas exposure (exposure2.py), now 5 of 5 regions
- % of residents in tracts with <5% of buildings type-labelled, rural vs urban: NCA 75.5/51.2, EOK 89.4/57.6, MAR 61.2/25.1, EWA 76.5/42.2, TX 83.1/46.0.
- Same direction at 1/5/10/25% cutoffs in every region. TX is the largest sample (6,003 tracts).
- TODO: osm_labels.py for Texas (type-label rate among OSM-only buildings).
