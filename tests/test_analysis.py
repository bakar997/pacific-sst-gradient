import unittest
import numpy as np
import pandas as pd
import xarray as xr
from src.sst_gradient import canonical_grid, overlap_weights, box_mean, annual_mean, trend_interval


class TestAnalysis(unittest.TestCase):
    def field(self):
        return xr.DataArray(np.ones((24, 9, 79))*25, dims=("time", "lat", "lon"),
            coords={"time": pd.date_range("2000-01-01", periods=24, freq="MS"),
                    "lat": np.arange(-8, 9, 2), "lon": np.arange(128, 285, 2)})

    def test_overlap_integrates_box_and_splits_boundary(self):
        da = self.field()
        w = overlap_weights(da, (-3, 3), (140, 170))
        expected = np.deg2rad(30)*(np.sin(np.deg2rad(3))-np.sin(np.deg2rad(-3)))
        self.assertAlmostEqual(float(w.sum()), expected, places=12)
        self.assertAlmostEqual(float(w.sel(lon=140).sum())*2, float(w.sel(lon=142).sum()))

    def test_grid_convention_and_constant_field(self):
        da = self.field()
        modified = da.assign_coords(lon=((da.lon+180) % 360)-180).isel(lat=slice(None, None, -1))
        canonical = canonical_grid(modified)
        xr.testing.assert_equal(canonical, da)
        series, _, _ = box_mean(canonical, (-3, 3), (190, 270))
        np.testing.assert_allclose(series, 25)

    def test_missing_mask_is_explicit(self):
        da = self.field()
        da.loc[dict(time=da.time[0], lat=0, lon=150)] = np.nan
        with self.assertRaisesRegex(ValueError, "Intermittent"):
            box_mean(da, (-3, 3), (140, 170))
        da.loc[dict(lat=0, lon=150)] = np.nan
        values, info, _ = box_mean(da, (-3, 3), (140, 170))
        np.testing.assert_allclose(values, 25)
        self.assertLess(info["valid_fraction_of_geometric_box"], 1)

    def test_day_weighted_leap_year_and_incomplete_year(self):
        dates = pd.date_range("2000-01-01", periods=12, freq="MS")
        frame = pd.DataFrame({"sst": [0, 1]+[0]*10}, index=dates)
        self.assertAlmostEqual(annual_mean(frame).iloc[0, 0], 29/366)
        with self.assertRaises(ValueError):
            annual_mean(frame.iloc[:-1])
        duplicate = pd.concat([frame, frame.iloc[[0]]])
        with self.assertRaises(ValueError):
            annual_mean(duplicate)

    def test_known_gradient_trend_and_bootstrap(self):
        years = np.arange(1950, 2026)
        west = 28+0.02*(years-1950)
        east = 25+0.005*(years-1950)
        result = trend_interval(years, west-east, draws=300)
        for key in ["slope_C_per_decade", "ci_low", "ci_high"]:
            self.assertAlmostEqual(result[key], 0.15, places=10)
        noisy = west-east+np.random.default_rng(4).normal(size=len(years))*0.2
        self.assertEqual(trend_interval(years, noisy, draws=300), trend_interval(years, noisy, draws=300))
        with self.assertRaises(ValueError):
            trend_interval(years[::2], noisy[::2])


if __name__ == "__main__":
    unittest.main()
