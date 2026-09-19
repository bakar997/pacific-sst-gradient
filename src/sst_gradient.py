"""Small, auditable functions for native-grid SST indices and trend intervals."""
from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr


def canonical_grid(da: xr.DataArray) -> xr.DataArray:
    """Normalize longitude to [0, 360), sort coordinates and validate the grid."""
    if set(da.dims) != {"time", "lat", "lon"}:
        raise ValueError("Expected exactly time, lat and lon dimensions")
    da = da.assign_coords(lon=da.lon % 360).sortby("lon").sortby("lat")
    for coord in ("lat", "lon"):
        x = da[coord].values.astype(float)
        dx = np.diff(x)
        if len(x) < 2 or np.any(dx <= 0) or not np.allclose(dx, dx[0]):
            raise ValueError(f"{coord} must be a unique, regular coordinate")
    return da.transpose("time", "lat", "lon")


def validate_months(time, start_year: int, end_year: int) -> None:
    actual = pd.DatetimeIndex(time).to_period("M")
    expected = pd.period_range(f"{start_year}-01", f"{end_year}-12", freq="M")
    if not actual.equals(expected):
        raise ValueError("Expected all months exactly once, in chronological order")


def load_sst(path, start_year=1950, end_year=2025) -> xr.DataArray:
    with xr.open_dataset(path) as ds:
        da = ds.sst.sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31")).load()
    if da.attrs.get("units", "").lower() not in {"degc", "degree_celsius", "degrees_c"}:
        raise ValueError(f"Unexpected SST units: {da.attrs.get('units')}")
    validate_months(da.time.values, start_year, end_year)
    da = canonical_grid(da)
    finite = da.values[np.isfinite(da.values)]
    if not len(finite) or finite.min() < -5 or finite.max() > 45:
        raise ValueError("Invalid or implausible SST values")
    return da


def overlap_weights(da: xr.DataArray, lat_bounds, lon_bounds) -> xr.DataArray:
    """Spherical box/cell overlap area in steradians (Earth radius cancels).

    Coordinates must already be sorted and regular. Boxes must not cross 0°.
    Native cell boundaries are halfway between adjacent centres.
    """
    south, north = lat_bounds
    west, east = lon_bounds
    if not (-90 <= south < north <= 90 and 0 <= west < east <= 360):
        raise ValueError("Unsupported box bounds")
    lat, lon = da.lat.values.astype(float), da.lon.values.astype(float)
    dy, dx = np.diff(lat)[0], np.diff(lon)[0]
    if lat[0]-dy/2 > south or lat[-1]+dy/2 < north or lon[0]-dx/2 > west or lon[-1]+dx/2 < east:
        raise ValueError("Input grid does not cover the requested box")
    lo = np.maximum(lat-dy/2, south)
    hi = np.minimum(lat+dy/2, north)
    latitude = np.where(hi > lo, np.sin(np.deg2rad(hi))-np.sin(np.deg2rad(lo)), 0)
    longitude = np.deg2rad(np.maximum(0, np.minimum(lon+dx/2, east)-np.maximum(lon-dx/2, west)))
    return xr.DataArray(latitude[:, None]*longitude[None, :], dims=("lat", "lon"),
                        coords={"lat": da.lat, "lon": da.lon}, name="overlap_steradians")


def box_mean(da: xr.DataArray, lat_bounds, lon_bounds):
    weights = overlap_weights(da, lat_bounds, lon_bounds)
    finite = xr.apply_ufunc(np.isfinite, da)
    always = finite.all("time")
    sometimes = finite.any("time")
    if bool(((weights > 0) & sometimes & ~always).any()):
        raise ValueError("Intermittent missing data inside box: review mask explicitly")
    valid_weights = weights.where(always, 0)
    area = float(valid_weights.sum())
    if area <= 0:
        raise ValueError("No fixed valid ocean area in box")
    # Fill permanently missing cells only after excluding their weight.
    mean = (da.fillna(0)*valid_weights).sum(("lat", "lon"))/area
    info = {"retained_cells": int((valid_weights > 0).sum()),
            "overlap_cells": int((weights > 0).sum()),
            "valid_area_steradians": area,
            "valid_fraction_of_geometric_box": area/float(weights.sum())}
    return mean.to_series(), info, valid_weights


def annual_mean(monthly: pd.DataFrame) -> pd.DataFrame:
    """Day-weighted annual means, refusing partial years or missing values."""
    monthly = monthly.copy()
    monthly.index = pd.DatetimeIndex(monthly.index)
    validate_months(monthly.index, monthly.index[0].year, monthly.index[-1].year)
    if not np.isfinite(monthly.to_numpy()).all():
        raise ValueError("Annual means require finite monthly values")
    days = pd.Series(monthly.index.days_in_month, index=monthly.index)
    numerator = monthly.mul(days, axis=0).groupby(monthly.index.year).sum()
    denominator = days.groupby(monthly.index.year).sum()
    result = numerator.div(denominator, axis=0)
    result.index.name = "year"
    return result


def trend_interval(years, values, block=5, draws=5000, seed=20260916):
    """OLS trend and percentile circular residual-block bootstrap CI.

    Fit unsmoothed annual values. Residual blocks wrap around the record;
    sampled residuals are added to the fitted line and slopes are refitted.
    The interval is conditional on the observed record, linear trend and
    residual stationarity. It does not include reconstruction uncertainty.
    """
    x, y = np.asarray(years, dtype=float), np.asarray(values, dtype=float)
    if x.ndim != 1 or y.shape != x.shape or len(x) < 3 or not np.isfinite(y).all():
        raise ValueError("Need matching finite annual series")
    if not np.allclose(np.diff(x), 1):
        raise ValueError("Trend input must contain consecutive annual values")
    if not 1 <= block <= len(x) or draws < 100:
        raise ValueError("Invalid bootstrap settings")
    xc = x-x.mean()
    denominator = xc @ xc
    slope = (xc @ y)/denominator
    fitted = y.mean()+slope*xc
    residual = y-fitted
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(y), size=(draws, int(np.ceil(len(y)/block))))
    indices = ((starts[..., None]+np.arange(block)) % len(y)).reshape(draws, -1)[:, :len(y)]
    slopes = slope + (residual[indices] @ xc)/denominator
    lo, hi = np.quantile(slopes*10, [0.025, 0.975])
    sst = np.sum((y-y.mean())**2)
    return {"slope_C_per_decade": float(slope*10), "ci_low": float(lo), "ci_high": float(hi),
            "n_years": len(y), "block_years": block, "bootstrap_draws": draws,
            "r_squared": float(1-np.sum(residual**2)/sst) if sst > 0 else 0.0}


def residual_acf(years, values, max_lag=15):
    x, y = np.asarray(years, float), np.asarray(values, float)
    fit = np.polyval(np.polyfit(x-x.mean(), y, 1), x-x.mean())
    r = y-fit
    denominator = r @ r
    return np.array([np.dot(r[:-k], r[k:])/denominator if denominator > 0 else 0
                     for k in range(1, min(max_lag, len(r)-1)+1)])
