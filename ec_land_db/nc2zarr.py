#!/usr/bin/python3
import argparse
import logging

import numpy as np
import xarray as xr

logging.basicConfig(level=logging.INFO)

TIMESTEP = "6H"
CLIM_FILE = "/home/daep/projects/ec_land_db/ec_land_db/scratch/surfclim_399_l4"
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
FC_GLOB_PATTERNS = [
    "/ec/res4/scratch/daep/ec_training_db_out/i6aj_20200101_fc_*.grb",
    "/ec/res4/scratch/daep/ec_training_db_out/i6aj_20191231_fc_*.grb",
]
AN_GLOB_PATTERNS = [
    "/ec/res4/scratch/daep/ec_training_db_out/i6aj_20200101_soil_*.grb",
    "/ec/res4/scratch/daep/ec_training_db_out/i6aj_20200101_snow_*.grb",
]
OUTPUT_FNAME = "/ec/res4/scratch/daep/ec_training_db_out/test.zarr"


def update_longitude(ds: xr.Dataset) -> xr.Dataset:
    """rescale the longitude values of an xr.Dataset from (0, 360) to (-180, 180)

    :param ds: dataset with longitude coordinate
    :return: dataset with rescaled longitude coordinate
    """
    if "lon" not in ds.variables:
        ds = ds.rename({"latitude": "lat", "longitude": "lon"})
    ds = ds.assign_coords(lon=(((ds.lon + 180) % 360) - 180))
    ds.lon.attrs["units"] = "degrees_east"
    ds.lon.attrs["long_name"] = "longitude"
    ds.lon.attrs["standard_name"] = "longitude"
    return ds


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
    ds = update_longitude(ds.set_coords(["lat", "lon"])).isel(time=slice(0,-1)).resample(time=TIMESTEP).mean()

    logging.info(f"Merging Datasets and saving to Zarr {args['output_filename']}...")
    ds = ds[sorted(ds.variables)].chunk({"x": -1, "time": -1})
    ds.astype("float32").to_zarr(args["output_filename"], consolidated=True)
    logging.info("Zarr conversion complete!")
