# Bias Bounty Mapping Equity Challenge: analysis code

**Author:** Brian Esalimba | Nairobi, Kenya | Data analyst
**Zindi username:** esalimba_brian
**LinkedIn:** https://www.linkedin.com/in/brian-esalimba-895b7515b
**GitHub:** https://github.com/esalimbacyberhub-lgtm

Entry for the Zindi *Bias Bounty Mapping Equity Challenge* (Best Documentation and Best Bias Discovery).

## Main finding

Building **type labels** (house, apartments, commercial and so on) in Overture Maps (release 2026-08-19.0) are scarce everywhere and scarcest in rural tracts. This held in all five study regions, and it persisted when only buildings from the same upstream source (OpenStreetMap) were compared.

Share of residents living in label-poor tracts (fewer than 5% of buildings labelled):

| Region | Rural | Urban |
|---|---|---|
| Northern California | 75.5% | 51.2% |
| Eastern Oklahoma | 89.4% | 57.6% |
| Maricopa, Arizona | 61.2% | 25.1% |
| Eastern Washington | 76.5% | 42.2% |
| South-Central Texas | 83.1% | 46.0% |

Share of OpenStreetMap-sourced buildings with a type label:

| Region | Rural | Urban |
|---|---|---|
| Northern California | 19.6% | 25.6% |
| Eastern Oklahoma | 24.9% | 36.8% |
| Maricopa, Arizona | 22.7% | 49.3% |
| Eastern Washington | 15.7% | 24.7% |
| South-Central Texas | not run | not run |

Hypotheses tested and rejected: a social-vulnerability gradient and a tribal-tract effect (both were geography or rural effects once controlled).

## Leaderboard attempts (public RMSE)

There are no labels in the challenge data, so these are hand-built indices, all with mean 0.30.

| Submission | Idea | RMSE |
|---|---|---|
| A | Constant 0.30 | 0.256160316 |
| C | Higher gap where OpenStreetMap supplies more buildings | 0.263559579 |
| B | Higher gap where a tract has fewer buildings, POIs and roads than similar tracts | 0.267415119 |

Neither index beat the constant, so simple density and provenance indices carry no usable signal about the organiser scores.

## Rules compliance

Only the provided challenge data was used. The removed reference layers (TIGER roads, Microsoft Building Footprints, HIFLD, County Business Patterns) were not used or obtained elsewhere, and no attempt was made to reconstruct the organiser targets.

## Data

Not included here. Download from https://source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge into `reference/<region>/` and `strata/<region>/` (the README on that page has `aws s3 sync` commands). Regions: `northern-ca`, `eastern-ok`, `maricopa-az`, `eastern-wa`, `south-central-tx`.

## Environment

Python 3.12, installed with `pip install -r requirements.txt`.

## Run order

1. `python region_report.py <region>` builds `features_<region>.csv`
2. `python consequence.py <region>` builds `consequence_<region>.csv`
3. `python exposure2.py` share of residents in label-poor tracts by cutoff
4. `python exposure3.py` label share against OpenStreetMap share
5. `python osm_labels.py` label rate among OpenStreetMap-sourced buildings
6. `python check_template.py` checks tract IDs against Zindi's `SampleSubmission.csv`
7. `python build_submission.py` and `python build_submission_C.py` build submissions B and C

`WORKING_NOTES.md` holds the step-by-step working notes.

## Limitations

- "Source" is the first-listed entry in each feature's sources list.
- Features are assigned to tracts by centroid or midpoint, so a few border features are double-counted.
- The 5% cutoff is arbitrary; results were checked at 1, 5, 10 and 25%.
- This analysis does not show why labels are scarcer in rural areas, or that emergency response is worse there.
