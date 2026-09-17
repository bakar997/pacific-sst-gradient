"""Reproduce all tables and figures from the bundled, checksummed SST inputs."""
from pathlib import Path
import sys
import json
import platform
import importlib.metadata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.sst_gradient import load_sst, box_mean, annual_mean, trend_interval, residual_acf
from scripts.download_data import verify_inputs, SOURCES

COLORS = {"ERSSTv5": "#086b8f", "COBE-SST2": "#c46424"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                    "figure.dpi": 120, "savefig.dpi": 180, "axes.titleweight": "bold"})


def save(fig, name):
    fig.savefig(ROOT/"figures"/(name+".png"), bbox_inches="tight", facecolor="white")
    fig.savefig(ROOT/"figures"/(name+".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    config = json.loads((ROOT/"config.json").read_text())
    manifest = verify_inputs()
    for folder in ["figures", "results", "data/processed"]:
        (ROOT/folder).mkdir(parents=True, exist_ok=True)
    monthly_frames, annual_frames, coverage, trends, acfs = [], [], [], [], []
    fields = {}
    for source, spec in SOURCES.items():
        da = load_sst(ROOT/"data/raw"/spec["file"], config["start_year"], config["end_year"])
        fields[source] = da
        for band in config["latitude_half_widths"]:
            monthly = pd.DataFrame(index=pd.DatetimeIndex(da.time.values))
            for region in ["west", "east"]:
                monthly[region], info, weights = box_mean(da, (-band, band), config[region])
                coverage.append({"dataset": source, "latitude_half_width": band, "region": region, **info})
                weight_table = weights.to_series().rename("area_steradians").reset_index()
                weight_table[weight_table.area_steradians > 0].to_csv(
                    ROOT/f"data/processed/weights_{source}_{region}_{band}deg.csv", index=False)
            monthly["gradient"] = monthly.west-monthly.east
            annual = annual_mean(monthly)
            for frame, target, index_name in [(monthly, monthly_frames, "time"), (annual, annual_frames, "year")]:
                frame.index.name = index_name
                target.append(frame.reset_index().assign(dataset=source, latitude_half_width=band))
            for start in config["trend_start_years"]:
                window = annual.loc[start:config["end_year"]]
                for variable in ["west", "east", "gradient"]:
                    blocks = config["bootstrap_block_years"] if variable == "gradient" else [config["primary_block_years"]]
                    for block in blocks:
                        result = trend_interval(window.index, window[variable], block,
                            config["bootstrap_draws"], config["seed"])
                        trends.append({"dataset": source, "latitude_half_width": band,
                            "start_year": start, "end_year": config["end_year"],
                            "variable": variable, **result})
                if band == 3 and start in config["primary_start_years"]:
                    for lag, value in enumerate(residual_acf(window.index, window.gradient), 1):
                        acfs.append({"dataset": source, "start_year": start, "lag_years": lag, "acf": value})
    monthly = pd.concat(monthly_frames, ignore_index=True)
    annual = pd.concat(annual_frames, ignore_index=True)
    trend = pd.DataFrame(trends)
    acf = pd.DataFrame(acfs)
    monthly.to_csv(ROOT/"data/processed/monthly_indices.csv", index=False, float_format="%.10f")
    annual.to_csv(ROOT/"data/processed/annual_indices.csv", index=False, float_format="%.10f")
    pd.DataFrame(coverage).to_csv(ROOT/"results/coverage.csv", index=False)
    trend.to_csv(ROOT/"results/trends.csv", index=False, float_format="%.10f")
    acf.to_csv(ROOT/"results/residual_acf.csv", index=False)
    environment = {"python": platform.python_version(), "packages": {p: importlib.metadata.version(p)
        for p in ["numpy", "pandas", "matplotlib", "xarray", "netCDF4", "requests", "nbformat", "nbclient", "ipykernel"]}}
    (ROOT/"results/run_manifest.json").write_text(json.dumps({"configuration": config,
        "environment": environment, "input_sha256": {r["source"]: r["sha256"] for r in manifest["files"]}}, indent=2)+"\n")

    # Context map: lon/lat axes; grid-cell boundaries supplied explicitly.
    da = fields["ERSSTv5"]
    climatology = da.sel(time=slice("1981", "2010")).mean("time")
    fig, ax = plt.subplots(figsize=(11, 3.8), layout="constrained")
    im = ax.pcolormesh(da.lon, da.lat, climatology, shading="nearest", cmap="YlOrRd", vmin=23, vmax=30)
    for label, limits, color in [("West", config["west"], "#003b5c"), ("East", config["east"], "#003b5c")]:
        ax.add_patch(Rectangle((limits[0], -3), limits[1]-limits[0], 6, fill=False, ec=color, lw=2))
        ax.add_patch(Rectangle((limits[0], -5), limits[1]-limits[0], 10, fill=False, ec=color, lw=1, ls="--"))
        ax.text(np.mean(limits), 0, label, ha="center", weight="bold", color="white",
                bbox={"facecolor": color, "alpha": .85, "edgecolor": "none", "pad": 4})
    ax.set(xlim=(130, 280), ylim=(-6, 6), xlabel="Longitude (°E)", ylabel="Latitude (°)",
           title="Two equatorial Pacific boxes: west minus east")
    ax.set_yticks([-5, -3, 0, 3, 5])
    ax.grid(alpha=.15)
    fig.colorbar(im, ax=ax, label="ERSSTv5 mean SST, 1981–2010 (°C)", shrink=.9)
    fig.supxlabel("Solid outlines: primary ±3° band  |  Dashed: ±5° sensitivity  |  Native-grid area means", fontsize=9)
    save(fig, "01_regions")

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True, layout="constrained")
    for source in SOURCES:
        a = annual.query("dataset == @source and latitude_half_width == 3").set_index("year")
        baseline = a.loc[config["baseline"][0]:config["baseline"][1], ["west", "east"]].mean()
        for ax, var in zip(axes, ["west", "east", "gradient"]):
            values = a[var] if var == "gradient" else a[var]-baseline[var]
            ax.plot(a.index, values, color=COLORS[source], lw=.8, alpha=.38)
            ax.plot(a.index, values.rolling(5, center=True, min_periods=5).mean(),
                    color=COLORS[source], lw=2, label=source)
            ax.grid(alpha=.18)
    axes[0].set(title="Regional warming and the west-minus-east SST contrast", ylabel="Western anomaly (°C)")
    axes[1].set(ylabel="Eastern anomaly (°C)")
    axes[2].set(ylabel="West − east (°C)", xlabel="Year")
    for ax in axes[:2]:
        ax.axhline(0, color="grey", lw=.7)
    axes[0].legend(ncol=2, frameon=False)
    fig.supxlabel("±3° latitude | Regional anomalies: annual 1981–2010 baseline | Thin: annual; thick: centred 5-year mean\nTrends use unsmoothed annual values. The contrast is a temperature difference, not °C/km.", fontsize=9)
    save(fig, "02_time_series")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True, layout="constrained")
    labels = {"west": "Western SST", "east": "Eastern SST", "gradient": "West − east"}
    for ax, start in zip(axes, config["primary_start_years"]):
        subset = trend.query("latitude_half_width == 3 and start_year == @start and block_years == 5")
        for offset, source in [(-.12, "ERSSTv5"), (.12, "COBE-SST2")]:
            for j, variable in enumerate(labels):
                r = subset.query("dataset == @source and variable == @variable").iloc[0]
                slope = r.slope_C_per_decade
                ax.errorbar(slope, j+offset, xerr=[[slope-r.ci_low], [r.ci_high-slope]],
                            fmt="o", capsize=3, color=COLORS[source], label=source if j == 0 else None)
        ax.axvline(0, color="grey", lw=1)
        ax.set(title=f"{start}–2025", xlabel="Linear trend (°C per decade)", yticks=range(3), yticklabels=list(labels.values()))
        ax.grid(axis="x", alpha=.2)
    axes[0].invert_yaxis()
    axes[0].legend(frameon=False, loc="lower right")
    fig.supxlabel("±3° latitude | 95% circular residual-block bootstrap intervals; 5-year blocks, 5,000 draws\nIntervals describe conditional trend uncertainty; shared observations limit product independence.", fontsize=9)
    save(fig, "03_primary_trends")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True, layout="constrained")
    starts = config["trend_start_years"]
    for ax, band in zip(axes, config["latitude_half_widths"]):
        for offset, source in [(-.12, "ERSSTv5"), (.12, "COBE-SST2")]:
            for j, start in enumerate(starts):
                r = trend.query("dataset == @source and latitude_half_width == @band and start_year == @start and variable == 'gradient' and block_years == 5").iloc[0]
                slope = r.slope_C_per_decade
                ax.errorbar(slope, j+offset, xerr=[[slope-r.ci_low], [r.ci_high-slope]], fmt="o", capsize=3,
                            color=COLORS[source], label=source if j == 0 else None)
        ax.set(title=f"Latitude: {band}°S–{band}°N", xlabel="Gradient trend (°C per decade)",
               yticks=range(len(starts)), yticklabels=[f"{s}–2025" for s in starts])
        ax.axvline(0, color="grey", lw=1)
        ax.grid(axis="x", alpha=.2)
    axes[0].invert_yaxis()
    axes[0].legend(frameon=False)
    fig.supxlabel("Prespecified period and latitude sensitivity | 95% intervals, 5-year blocks\nShorter periods are particularly sensitive to variability and endpoint choices.", fontsize=9)
    save(fig, "04_sensitivity")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True, layout="constrained")
    for ax, start in zip(axes, config["primary_start_years"]):
        for source in SOURCES:
            a = acf.query("dataset == @source and start_year == @start")
            ax.plot(a.lag_years, a.acf, "o-", ms=4, color=COLORS[source], label=source)
        ax.axhline(0, color="grey", lw=.8)
        ax.set(title=f"Detrended gradient, {start}–2025", xlabel="Lag (years)", ylabel="Residual autocorrelation")
        ax.grid(alpha=.15)
    axes[0].legend(frameon=False)
    fig.supxlabel("Diagnostic of temporal dependence; no significance thresholds are implied.\nBlock lengths 3, 5 and 7 years are compared in results/trends.csv.", fontsize=9)
    save(fig, "05_residual_dependence")

    primary = trend[(trend.latitude_half_width == 3)&(trend.variable == "gradient")&(trend.block_years == 5)&trend.start_year.isin(config["primary_start_years"])]
    lines = ["# Computed results", "", "Units: °C per decade. Primary latitude band: 3°S–3°N.", "",
        "Intervals: 95% percentile circular residual-block bootstrap, 5-year blocks, 5,000 draws.", "",
        "| Dataset | Period | West − east trend | 95% interval |", "|---|---|---:|---:|"]
    for r in primary.itertuples():
        lines.append(f"| {r.dataset} | {r.start_year}–{r.end_year} | {r.slope_C_per_decade:+.3f} | [{r.ci_low:+.3f}, {r.ci_high:+.3f}] |")
    lines += ["", "See trends.csv for western and eastern component trends, both latitude bands, all four periods and three block lengths.",
        "", "These are descriptive observational trends. They neither identify a forced response nor establish mechanisms.",
        "The two reconstructions share observations. Bootstrap intervals do not include all observational or reconstruction uncertainty.", ""]
    (ROOT/"results/summary.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"Saved {len(monthly):,} monthly rows, {len(annual):,} annual rows and {len(trend)} trend estimates.")


if __name__ == "__main__":
    main()
