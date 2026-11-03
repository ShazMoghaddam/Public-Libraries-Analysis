# Changelog

All notable changes to this project are listed here. Versions are dated by month, like `v2026.11`.

## v2026.11 · November 2026

A full rebuild, from a single notebook into a tested, reproducible analysis.

### Fixed

- The model's 99.5% score came from a column that was the answer recalculated: visits divided by population. That
  column alone scores the same. It's replaced by a fair test that learns from 2010 to 2017 and predicts 2019
- The number printed as "RMSE" was the squared error. The real figure is 0.27, not 0.072
- Dropping every row with a blank threw away 44% of the data and every year before 2005. Nothing is dropped that way now
- The data was described as US public libraries. It's Connecticut only
- The "cleaned" CSV was the raw file with one extra column. It's removed, and `data/prepare.py` now does real cleaning:
  renamed libraries are joined up, each library is matched to its town, closed branches' zeros become blanks and 2024
  materials spending, which was counted differently, is left out
- The "Top 10 counties" chart showed all eight of Connecticut's counties and gave a small branch the same weight as a
  city library. Figures are now worked out per resident, by town
- Money is now adjusted for inflation, using the US Consumer Price Index

### Added

- A findings report with seven findings, every number worked out from the data
- Seven charts and three headline tiles, all drawn with [bezel-charts](https://pypi.org/project/bezel-charts/)
- `data/prepare.py`, tidy data, an inflation index and a record of sources in `data/sources.json`
- Tests, an automatic check on every pull request, Dependabot and a security policy
- Social preview image in `assets/social-preview.png`

### Changed

- New folder structure: `data/`, `findings/`, `notebooks/`, `charts/` and `tests/`
- README rewritten around the findings
- Notebook rewritten and moved to `notebooks/public_libraries_analysis.ipynb`

## November 2025

- First version: one notebook, the raw data and a README
