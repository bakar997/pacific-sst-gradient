"""Verify frozen inputs, or explicitly download new NOAA PSL subsets.

Usage: python scripts/download_data.py [--refresh]
Without --refresh, existing files are verified against provenance.json.
With --refresh, current provider bytes replace the snapshot and its manifest.
"""
from pathlib import Path
import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlencode
import requests
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "ERSSTv5": {"file": "ersstv5_pacific.nc", "dataset": "noaa.ersst.v5/sst.mnmean.nc",
                 "doi": "https://doi.org/10.7289/V5T72FNM",
                 "description": "NOAA Extended Reconstructed Sea Surface Temperature, version 5"},
    "COBE-SST2": {"file": "cobe_sst2_pacific.nc", "dataset": "COBE2/sst.mon.mean.nc",
                  "doi": "https://doi.org/10.1175/JCLI-D-12-00837.1",
                  "description": "JMA COBE-SST2; subset distributed by NOAA PSL"}}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_url(source, historical_snapshot=False):
    # Original ERSST request returned an extra January 2026 due to NCSS date
    # snapping. load_sst explicitly selects 1950–2025. Refresh requests avoid it.
    end = "2025-12-31" if historical_snapshot and source == "ERSSTv5" else "2025-12-01"
    query = urlencode({"var": "sst", "north": 6, "south": -6, "west": 130, "east": 280,
        "time_start": "1950-01-01T00:00:00Z", "time_end": end+"T00:00:00Z", "accept": "netcdf"})
    return "https://psl.noaa.gov/thredds/ncss/grid/Datasets/"+SOURCES[source]["dataset"]+"?"+query


def metadata(source, path, url):
    with xr.open_dataset(path) as ds:
        details = {"dimensions": dict(ds.sizes), "first_month": str(ds.time.values[0])[:10],
                   "last_month": str(ds.time.values[-1])[:10],
                   "sst_units": ds.sst.attrs.get("units"),
                   "provider_global_attributes": {k: str(v) for k, v in ds.attrs.items()}}
    return {**SOURCES[source], "source": source, "request_url": url,
            "snapshot_recorded_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": sha256(path), "size_bytes": path.stat().st_size, **details}


def verify_inputs():
    manifest = json.loads((ROOT/"data/provenance.json").read_text())
    for record in manifest["files"]:
        path = ROOT/"data/raw"/record["file"]
        if not path.exists() or sha256(path) != record["sha256"]:
            raise ValueError(f"Input missing or checksum changed: {path.name}. See data/provenance.json")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Replace snapshot using live provider data")
    args = parser.parse_args()
    manifest_path = ROOT/"data/provenance.json"
    if manifest_path.exists() and not args.refresh:
        manifest = verify_inputs()
        for record in manifest["files"]:
            print(f"Verified {record['source']}: {record['sha256'][:16]}…")
        return
    records = []
    (ROOT/"data/raw").mkdir(parents=True, exist_ok=True)
    for source, description in SOURCES.items():
        path = ROOT/"data/raw"/description["file"]
        url = source_url(source)
        print(f"Downloading {source} from NOAA PSL…", flush=True)
        response = requests.get(url, timeout=(30, 240))
        response.raise_for_status()
        if response.content[:3] not in [b"CDF", b"\x89HD"]:
            raise ValueError("Provider response is not a NetCDF file")
        temporary = path.with_suffix(".download")
        temporary.write_bytes(response.content)
        # Open before replacing a usable snapshot.
        with xr.open_dataset(temporary, engine="netcdf4") as ds:
            if "sst" not in ds:
                raise ValueError("Downloaded file has no SST variable")
        temporary.replace(path)
        records.append(metadata(source, path, url))
    manifest_path.write_text(json.dumps({"analysis_period": "1950-01 through 2025-12",
        "note": "Live source files may be revised; bundled checksummed inputs define this snapshot.",
        "files": records}, indent=2)+"\n")


if __name__ == "__main__":
    main()
