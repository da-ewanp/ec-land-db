#!/usr/bin/python3
import argparse
import logging
from typing import Union

import numpy as np
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


def open_surfclim(clim_path: str) -> xr.Dataset:
    """Opens a ec-land climatological file using decode_times=False as times stored as "month"

    :param clim_path: path to ec-land climatological fields file
    :return: dataset of climatological fields
    """
    ds_clim = update_longitude(xr.open_dataset(clim_path, decode_times=False))
    return ds_clim


def preprocess_fc_grib(ds: xr.Dataset) -> xr.Dataset:
    """preprocess 'fc' type dataset, dropping unused dimensions and formatting time dimension

    :param ds: fc-type dataset
    :return: processed dataset
    """
    drop_lst = list(ds.coords)
    for dim in ["latitude", "longitude", "step"]:
        if dim in drop_lst:
            drop_lst.remove(dim)
    time_arr = ds.valid_time.values
    ds = ds.drop_vars(drop_lst).rename({"step": "time", "values": "x"})
    ds["time"] = time_arr
    if "time" not in list(ds.dims.keys()):
        ds = ds.expand_dims({"time": [ds.time.values]})
    return update_longitude(ds)


def preprocess_an_grib(ds: xr.Dataset) -> xr.Dataset:
    """preprocess 'fc' type dataset, dropping unused dimensions, formatting time dimension
    and flattening any additional dimensions outside of 'time' and 'x'.

    :param ds: an-type dataset
    :return: processed dataset
    """
    drop_lst = list(ds.drop_vars(["latitude", "longitude", "time"]).coords)
    dims_lst = list(ds.dims.keys())
    dim_layer_idx = np.where(["layer" in x.lower() for x in dims_lst])[0]
    if len(dim_layer_idx) == 1:
        datavars_lst = list(ds.data_vars)
        layer_dim = dims_lst[dim_layer_idx[0]]
        for layer in ds[layer_dim].values:
            for var in datavars_lst:
                ds[f"{var}_l{int(layer)}"] = ds[var].sel({layer_dim: int(layer)})
        ds = ds.drop_vars(datavars_lst)
    return update_longitude(ds.drop_vars(drop_lst).rename({"values": "x"}))


def open_grib_fc(fc_glob: str, idx_arr: Union[np.ndarray, None] = None) -> xr.Dataset:
    """Opens multiple fc-type grib files for a given glob pattern and creates a processed N-d labelled
    xarray dataset

    :param fc_glob: glob pattern for fc-type grib files to open
    :param idx_arr: index array to select subset of points in space, defaults to None
    :return: processed dataset
    """
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
    """Opens multiple an-type grib files for a given glob pattern and creates a processed N-d labelled
    xarray dataset

    :param an_glob: glob pattern for an-type grib files to open
    :param idx_arr: index array to select subset of points in space, defaults to None
    :return: processed dataset
    """
    ds_an = xr.open_mfdataset(
        an_glob,  # "/ec/res4/scratch/daep/ec_training_db_out/i6aj_20200101_soil_*.grb",
        engine="cfgrib",
        combine="nested",
        compat="override",
        preprocess=preprocess_an_grib,
        parallel=True,
    )
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
