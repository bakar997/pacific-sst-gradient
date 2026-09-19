# Data sources, provenance and references

Snapshot obtained **16 September 2026**. Analysis covers January 1950–December 2025. Raw inputs are small regional subsets, obtained from NOAA PSL's THREDDS NetCDF Subset Service. Requested domain: approximately 130–280°E, 6°S–6°N; the server snaps to native grid cells.

## NOAA ERSSTv5

- Producer: NOAA National Centers for Environmental Information.
- Native grid: 2° latitude × 2° longitude; monthly absolute SST.
- [NOAA product documentation](https://www.ncei.noaa.gov/products/extended-reconstructed-sst).
- [NOAA PSL distribution page](https://psl.noaa.gov/data/gridded/data.noaa.ersst.v5.html).
- Data citation: Huang, B., Thorne, P. W., Banzon, V. F., Boyer, T., Chepurin, G., Lawrimore, J. H., Menne, M. J., Smith, T. M., Vose, R. S., and Zhang, H.-M. (2017). *NOAA Extended Reconstructed Sea Surface Temperature (ERSST), Version 5*. NOAA NCEI. [doi:10.7289/V5T72FNM](https://doi.org/10.7289/V5T72FNM). Regional monthly subset described above, accessed 2026-09-16.
- Methods: Huang et al. (2017). *Extended Reconstructed Sea Surface Temperature, Version 5 (ERSSTv5): Upgrades, Validations, and Intercomparisons*. Journal of Climate. [doi:10.1175/JCLI-D-16-0836.1](https://doi.org/10.1175/JCLI-D-16-0836.1).

ERSSTv6 is now available. This project explicitly uses v5 for consistency with the motivating literature and a fixed two-product comparison. It does not describe v5 as the newest product. The NetCDF license attribute states no constraints on data access or use; provider attribution is retained.

## JMA COBE-SST2

- Producer: Japan Meteorological Agency; distributed here by NOAA PSL.
- Native grid: 1° latitude × 1° longitude; monthly absolute SST.
- [NOAA PSL distribution page](https://psl.noaa.gov/data/gridded/data.cobe2.html).
- [JMA/MRI original data directory](https://climate.mri-jma.go.jp/pub/ocean/cobe-sst2/).
- Methods and product reference: Hirahara, S., Ishii, M., and Fukuda, Y. (2014). *Centennial-Scale Sea Surface Temperature Analysis and Its Uncertainty*. Journal of Climate, 27, 57–75. [doi:10.1175/JCLI-D-12-00837.1](https://doi.org/10.1175/JCLI-D-12-00837.1).

The subset retains the provider's global attributes. Repository licensing does not supersede JMA/NOAA terms or claim ownership of these data.

## Index definition and scientific context

Byrne, H., Seager, R., and Smerdon, J. E. *CMIP6 models cannot capture long-term forced changes in the tropical Pacific sea surface temperature gradient*. Nature Communications, 17, 142 (2026; online publication 6 December 2025). [doi:10.1038/s41467-025-66839-w](https://doi.org/10.1038/s41467-025-66839-w).

The primary 3°S–3°N, western 140–170°E and eastern 170–90°W boxes follow this paper. The present project is an observational follow-up with its own documented averaging, periods and uncertainty calculation. No figures, text passages or model results are copied from the paper.

## Audit trail and acknowledgment

`data/provenance.json` contains exact query URLs, file sizes, SHA-256 digests, coordinate extents in time, and provider global attributes. `scripts/download_data.py` verifies the snapshot by default. Explicit `--refresh` downloads a new snapshot and rewrites the manifest.

Data access was provided by NOAA Physical Sciences Laboratory, Boulder, Colorado, USA, through [psl.noaa.gov](https://psl.noaa.gov/). Credit the original producers and cited methods as well as the distributor when reusing this work.
