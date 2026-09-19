# Understanding the Pacific SST analysis

This guide explains the data, calculations, and interpretation of the Pacific SST analysis. The project studies an observed sea-surface temperature (SST) contrast. It does not identify causes or run climate-model simulations.

## 1. Connect laboratory physics to climate computing

In a laboratory, you define measurements, select instruments, document calibration, propagate uncertainty, and check repeatability. The same habits apply here.

The “instrument record” is a gridded reconstruction assembled from observations. Each grid value represents an area. Reconstruction methods, incomplete historical sampling, and measurement changes affect the record. A second dataset tests sensitivity to reconstruction choices without removing these limitations.

Think of the workflow as successive measurements:

1. Read monthly temperatures and their coordinates.
2. Average temperatures over two specified ocean boxes.
3. Subtract the eastern average from the western average.
4. Convert the monthly contrast to annual values.
5. Estimate how that annual contrast changes through time.
6. Examine uncertainty and alternative reasonable choices.

Each step needs an equation, units, and an explainable check.

## 2. Know exactly what is being measured

The inputs are NOAA ERSSTv5, on a 2° grid, and JMA COBE-SST2, on a 1° grid, obtained through NOAA Physical Sciences Laboratory. Both cover the same analysis interval: January 1950–December 2025.

The western box is 140–170°E. The eastern box is 190–270°E, equivalent to 170–90°W. Both initially extend from 3°S to 3°N. A sensitivity calculation expands the latitude range to 5°S–5°N while retaining the longitude limits.

The index is

\[
G(t)=T_W(t)-T_E(t).
\]

Its units are °C. A positive value means the western box is warmer. A positive trend means that west-minus-east contrast increases. Although the project calls this a “gradient,” it is a temperature-difference index, not a spatial derivative in °C per kilometre. The unequal longitude widths are intentional; each box produces its own normalized area mean.

## 3. Understand the averaging

### Space: weight the part of each cell inside the box

Grid cells have area, and some cross a box boundary. Exact spherical box–cell overlap weights include only the intersecting portion. For overlapping longitude width \(\Delta\lambda\) and latitude bounds \(\phi_S,\phi_N\), the weight is proportional to

\[
\Delta\lambda\,[\sin(\phi_N)-\sin(\phi_S)].
\]

Angles are in radians. The common Earth-radius factor cancels when weights are normalized. This accounts for latitude-dependent cell area and partial boundary cells. Selecting cells solely by their centre coordinates answers a slightly different question.

A fixed valid mask retains a consistent set of usable cells across the analysis interval, separately for each dataset and box. Otherwise, changing data coverage could change the average even without actual temperature change. Check how the code defines validity and how much area remains.

### Time: weight months by their duration

Annual means weight each monthly value by its number of days. February receives 29 days in a leap year. All twelve months must be accounted for; an incomplete year should not silently become a comparable annual average.

For regional plots, anomalies subtract each product/region’s arithmetic mean of the 30 annual values in 1981–2010. This centres the series and makes variations easier to compare. Trends are fitted to raw annual values. Subtracting a constant baseline would leave a linear trend unchanged.

## 4. Read trends and uncertainty together

Ordinary least squares fits a straight line to annual values. A yearly slope multiplied by ten gives °C per decade. The primary periods are 1950–2025 and 1979–2025. The 1993–2025 and 2000–2025 fits are sensitivity checks, not replacements selected because they look more striking. Shorter periods can be strongly influenced by natural variability and endpoint choices.

Neighbouring years can be correlated. The uncertainty calculation therefore uses a seeded circular moving-block bootstrap with 5,000 resamples of detrended annual gradient residuals. Five-year blocks are the main choice; three- and seven-year blocks test sensitivity.

Detrending separates the fitted line from annual departures. Sampling contiguous residual blocks preserves some dependence between nearby years. “Circular” means a block can wrap from the end of the residual record to its beginning. Resampled residuals are added to the fitted line and the trend is refitted. The resulting slope distribution supplies the reported uncertainty interval. The seed makes this computation reproducible; it does not make the observations certain.

This approach still depends on assumptions about residual behaviour and block length. Its interval does not capture every measurement, reconstruction, or methodological uncertainty.

## 5. Read the results before telling a story

Start with coverage checks. Then inspect western and eastern temperatures separately, because the same contrast trend can arise through different regional changes. Read the annual index plot alongside its fitted slope and interval. Compare both datasets, both latitude widths, and all prespecified periods. State disagreement as well as agreement.

Avoid translating a temperature contrast directly into a claim about atmospheric circulation or human influence. Those questions need additional evidence. Insert numerical findings only after reproducing the actual outputs.

## 6. Scientific questions

1. **What is the research question?** How did the observed equatorial Pacific west-minus-east SST contrast change, and how sensitive are the estimates to dataset and analysis choices?
2. **Why two datasets?** To assess sensitivity to gridding and reconstruction. They may share observations, so agreement is not fully independent confirmation.
3. **Why use area weights?** Each cell contributes according to its actual overlap with the box.
4. **Why a fixed mask?** To prevent changing spatial coverage from becoming an artificial temperature signal.
5. **Why weight months by days?** Months have different durations; the annual mean should reflect time represented.
6. **What does a positive slope mean?** The western-minus-eastern temperature difference increases; both regions could still be warming.
7. **Why several periods?** They show whether the conclusion depends strongly on the chosen timescale and endpoints.
8. **Why bootstrap blocks?** Annual residuals can be correlated, so individual-year resampling can misrepresent uncertainty.
9. **Does the analysis establish a cause?** No. This is an observational description with robustness checks.

## 7. Reproducibility checks

The following checks can be used to examine the workflow; this list does not report additional completed validation:

- Compare temperature units, longitude conventions, calendars, missing values, and date coverage with the input metadata.
- Recalculate a monthly box mean from the saved weights and compare it with the pipeline output.
- Check a leap-year annual mean against its twelve day-weighted monthly values.
- Compare the ±3° and ±5° regions to assess sensitivity to latitude bounds.
- Compare raw and baseline-centred annual series; subtracting a constant should preserve the fitted slope.
- Repeat the bootstrap with fixed and alternative seeds and block lengths to distinguish reproducibility from methodological sensitivity.
