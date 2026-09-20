# Methods and interpretation

## Question and scope

Estimate descriptive linear changes in the equatorial Pacific west-minus-east SST contrast. Compare two reconstructions, two latitude widths, four periods and three bootstrap block lengths. Analysis settings are recorded in `config.json`, and the reported sensitivity checks examine the effects of alternative analysis periods, latitude bands and bootstrap block lengths. This is not a preregistered study.

The geographical boxes follow the index used by Byrne, Seager and Smerdon ([2026, Nature Communications 17, 142](https://doi.org/10.1038/s41467-025-66839-w); published online in December 2025). That study considers observations and climate-model ensembles. Here the scientific scope is limited to observational indices and sensitivity checks. The approach is inspired by its index, not a claim to reproduce its full analysis.

## 1. Inputs and quality checks

Use monthly absolute SST (`sst`, units `degC`) from ERSSTv5 and COBE-SST2. The analysis selects January 1950 through December 2025 explicitly. The archive has 912 months per product in the analysis window. ERSST's original subset request also returned January 2026; it is excluded by code before all averaging.

The pipeline checks input SHA-256 hashes, variable units, plausible temperature bounds, regular unique spatial coordinates, complete chronological monthly coverage, and missing values. Longitudes are normalized to [0, 360); latitude and longitude are sorted. No regridding is performed.

A finite grid value is a reconstruction estimate. It is not evidence that the cell had a direct observation that month. The spatial coverage report describes the reconstruction's fixed valid ocean grid, not historical observation density.

Both products use overlapping underlying observations. Differences test sensitivity to their reconstructions and grids; two similar answers do not remove shared sampling or bias errors. Provider files may be revised retrospectively. The bundled bytes and manifest define the reproducible snapshot.

## 2. Spatial index

For each month:

\[
G(t)=T_W(t)-T_E(t).
\]

- Western box: 140–170°E.
- Eastern box: 190–270°E (170–90°W).
- Primary latitude band: 3°S–3°N.
- Latitude sensitivity: 5°S–5°N, same longitude limits.

`G` is a temperature difference in °C, often called an SST-gradient index. It is not divided by the distance between the boxes and is not a spatial derivative. The longitude widths are deliberately unequal; the means are normalized within each region.

Infer regular cell boundaries halfway between coordinate centres. For each cell/box overlap, use

\[
w_i=\Delta\lambda_i\,[\sin(\phi_{i,N})-\sin(\phi_{i,S})],\quad
T_R(t)=\frac{\sum_{i\in R}w_i T_i(t)}{\sum_{i\in R}w_i}.
\]

Angles are in radians. The common squared Earth radius cancels, so weights are stored in steradians. Cells crossing the regional boundary contribute only their overlapping area. Weights and weighted accumulation use double precision. The within-cell value is assumed representative throughout that overlap; no extra spatial information is created.

Cells missing throughout the analysis period receive zero weight. A cell that is valid in some months but missing in others causes the pipeline to stop. This avoids an unnoticed time-dependent spatial mask. Coastlines are represented by each product's native mask, not exact subcell ocean fractions. The wider western box contains land-masked cells and slightly different valid areas across products.

Saved weight CSVs allow an independent manual regional-mean calculation. `results/coverage.csv` records retained cell counts and geometric coverage fractions.

## 3. Time averaging and baseline

Compute annual values as

\[
\overline{T}_y=\frac{\sum_{m=1}^{12}d_{y,m}T_{y,m}}{\sum_{m=1}^{12}d_{y,m}},
\]

where `d` is the calendar month's number of days, including leap years. All twelve months must exist. The same operation applies to the west-minus-east index, so annual differencing and annual averaging commute.

For the regional time-series figure only, subtract each product/region's arithmetic mean of the 30 annual values from 1981–2010. These are annual anomalies; no monthly seasonal-anomaly index is used. Gradient plots retain the absolute contrast. Thin lines show annual values and thick lines a centred five-year mean requiring all five years. Smoothing therefore stops two years before the plotted annual record ends. All regressions use unsmoothed raw annual values.

The context map is the arithmetic mean of the 360 monthly ERSSTv5 fields in 1981–2010. It only illustrates the boxes and background SST pattern; it is not used in trend calculations.

## 4. Trend estimates

Fit ordinary least squares with an intercept:

\[
y_t=a+b(t-\overline{t})+e_t.
\]

Report `10b`, in °C per decade. The primary periods are 1950–2025 (76 years) and 1979–2025 (47 years). Sensitivity periods are 1993–2025 (33 years) and 2000–2025 (26 years). These are fixed diagnostic windows, not breakpoint estimates. There is no statistical test here that the underlying trend accelerated between periods.

Estimate western, eastern and gradient slopes separately. Under common years and weights, the gradient slope equals the western slope minus the eastern slope. Its uncertainty is calculated directly from the gradient series, not by treating regional errors as independent.

## 5. Serial dependence and uncertainty

Use a circular moving-block bootstrap of OLS residuals:

1. Fit the line and retain annual residuals.
2. Choose block start indices uniformly, with replacement.
3. Take consecutive residuals in each block; wrap around the end of the record.
4. Concatenate enough blocks and truncate to the original number of years.
5. Add those residuals to the fitted line at the original years and refit its slope.
6. Repeat 5,000 times. Report the 2.5th and 97.5th percentiles of slopes.

The primary block length is five years. Gradient intervals are also calculated with three- and seven-year blocks. Seed `20260916` is fixed and restarted for every individual estimate to make comparisons reproducible. It does not create a joint confidence interval across products or choices. Regional component intervals use five-year blocks.

Residual autocorrelations are plotted for the primary gradient series. Their denominator is the full residual sum of squares. They are descriptive diagnostics without significance thresholds. A five-year block is a pragmatic sensitivity choice, not an estimated optimum or a complete model of decadal variability.

**Limits of the intervals:** the method assumes the detrended residual behaviour can be resampled as approximately stationary short blocks. It may underrepresent long-lived variability and does not explicitly model changing variance. Short windows contain few effectively independent blocks. Circular wrap-around joins endpoints. Percentile intervals are not bias-corrected or simultaneous, and comparing their overlap is not a formal test of product differences. The intervals exclude much of measurement, sampling, reconstruction and structural uncertainty. No p-values or causal claims are inferred from excluding zero.

## 6. Interpretation and next steps

Interpret the three variables together. A positive gradient trend may occur when both regions warm but the west warms faster. Similar gradient trends can conceal differences in regional warming estimates.

The analysis cannot partition forced change and internal variability, assess climate-model fidelity, infer wind-stress change, or establish a thermocline mechanism. Suitable next steps would combine additional SST products with independently evaluated wind stress and upper-ocean diagnostics, or compare model ensembles using matching periods and boxes. These are proposed extensions, not completed work.

Automated tests cover exact box area, boundary weights, coordinate conventions, constant fields, intermittent missingness, leap-year weighting, incomplete or duplicated months, known trends, and deterministic bootstrap sampling. They validate calculations; they do not validate all scientific assumptions.
