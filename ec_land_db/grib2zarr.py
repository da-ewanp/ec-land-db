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


def open_surfclim(clim_path: str) -> xr.Dataset:
    ds_clim = update_longitude(xr.open_dataset(clim_path, decode_times=False))
    return ds_clim


def preprocess_fc_grib(ds: xr.Dataset) -> xr.Dataset:
    drop_lst = list(ds.coords)
    for dim in ["latitude", "longitude", "step"]:
        if dim in drop_lst:
            drop_lst.remove(dim)
    time_arr = ds.valid_time.values
    ds = ds.drop(drop_lst).rename({"step": "time", "values": "x"})
    ds["time"] = time_arr
    if "time" not in list(ds.dims.keys()):
        ds = ds.expand_dims({"time": [ds.time.values]})
    return update_longitude(ds)


def open_grib_fc(fc_glob: str, idx_arr: [np.ndarray, None] = None) -> xr.Dataset:
    ds_fc = xr.open_mfdataset(
        fc_glob,  # "/ec/res4/scratch/daep/ec_training_db_out/i6aj_20200101_fc_*.grb",
        engine="cfgrib",
        combine="nested",
        # compat="override",
        preprocess=preprocess_fc_grib,
        parallel=True,
    )
    if idx_arr is not None:
        ds_fc = ds_fc.isel(x=idx_arr)
    return ds_fc


def open_grib_an(an_glob: str, idx_arr: [np.ndarray, None] = None) -> xr.Dataset:
    ds_an = xr.open_mfdataset(
        an_glob,  # "/ec/res4/scratch/daep/ec_training_db_out/i6aj_20200101_soil_*.grb",
        engine="cfgrib",
        combine="nested",
        compat="override",
        parallel=True,
    )
    drop_lst = list(ds_an.drop(["latitude", "longitude", "time"]).coords)
    dims_lst = list(ds_an.dims.keys())
    dim_layer_idx = np.where(["layer" in x.lower() for x in dims_lst])[0]
    if len(dim_layer_idx) == 1:
        datavars_lst = list(ds_an.data_vars)
        layer_dim = dims_lst[dim_layer_idx[0]]
        for layer in ds_an[layer_dim].values:
            for var in datavars_lst:
                ds_an[f"{var}_l{int(layer)}"] = ds_an[var].sel({layer_dim: int(layer)})
        ds_an = ds_an.drop(datavars_lst)
    ds_an = update_longitude(ds_an.drop(drop_lst).rename({"values": "x"}))
    if idx_arr is not None:
        ds_an = ds_an.isel(x=idx_arr)
    return ds_an


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-fc",
        "--fc_glob_pattern",
        nargs="*",
        required=True,
        help="input fc grib glob patterns",
    )
    ap.add_argument(
        "-an",
        "--an_glob_pattern",
        nargs="*",
        required=True,
        help="input an grib glob patterns",
    )
    ap.add_argument(
        "-out", "--output_filename", type=str, required=True, help="Output zarr file"
    )
    ap.add_argument(
        "-clim",
        "--climatological_file",
        type=str,
        required=True,
        help="ec-land climatological filename",
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
        f"Opening climatological variables from {args['climatological_file']}..."
    )
    ds_clim = open_surfclim(args["climatological_file"])
    grid_idxs = ds_clim.x.values - 1

    logging.info("Opening fc and an grib files...")
    ds_fc_lst = [open_grib_fc(glob_x, grid_idxs) for glob_x in args["fc_glob_pattern"]]
    ds_an_lst = [open_grib_an(glob_x, grid_idxs) for glob_x in args["an_glob_pattern"]]
    ds_fc = xr.concat(ds_fc_lst, dim="time")
    ds_model = (
        xr.merge([ds_fc] + ds_an_lst).resample(time=args["model_timestep"]).mean()
    )

    logging.info(
        "Selecting requested climatological features and inflating time dimension..."
    )
    ds_climfeats = ds_clim.drop(["lat", "lon"])[CLIM_FEATS]
    ds_climfeats = ds_climfeats.rename(
        {x: f"clim_{x}" for x in ds_climfeats.data_vars}
    ).expand_dims(dim={"time": ds_model.time})

    logging.info(f"Merging Datasets and saving to Zarr {args['output_filename']}...")
    ds_model = xr.merge([ds_model, ds_climfeats])
    ds_model = ds_model[sorted(ds_model.variables)].chunk({"x": -1, "time": -1})
    ds_model.astype("float32").to_zarr(args["output_filename"], consolidated=True)
    logging.info("Zarr conversion complete!")
