#!/usr/bin/python3
import argparse
import logging

import xarray as xr

from ec_land_db.xr_utils import update_longitude

logging.basicConfig(level=logging.INFO)

CLIM_FEATS = [
    "z0m",
    "geopot",
    "cvl",
    "cvh",
    "tvl",
    "tvh",
    "sotype",
    "sdor",
    "sdfor",
    "cu",
    "Ctype",
    "CLAKE",
]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-nc",
        "--nc_glob_pattern",
        type=str,
        required=True,
        help="input nc netcdf glob patterns",
    )
    ap.add_argument(
        "-out", "--output_filename", type=str, required=True, help="Output zarr file"
    )
    ap.add_argument(
        "-tstep",
        "--model_timestep",
        type=str,
        required=False,
        help="Time-step to average model output over",
        default="6H",
    )
    args = vars(ap.parse_args())

    logging.info(
        "Selecting requested climatological features and inflating time dimension..."
    )
    ds = xr.open_mfdataset(args["nc_glob_pattern"], engine="netcdf4", combine="nested")
    ds = (
        update_longitude(ds.set_coords(["lat", "lon"]))
        .isel(time=slice(0, -1))
        .resample(time=args["model_timestep"])
        .mean()
    )

    logging.info(f"Merging Datasets and saving to Zarr {args['output_filename']}...")
    ds = ds[sorted(ds.variables)].chunk({"x": -1, "time": -1})
    ds.astype("float32").to_zarr(args["output_filename"], consolidated=True)
    logging.info("Zarr conversion complete!")
