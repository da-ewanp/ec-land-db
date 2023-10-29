#!/usr/bin/python3
import numpy as np
import xarray as xr


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


def find_nearest_idx(
    arr1: np.ndarray,
    arr2: np.ndarray,
    val1: float,
    val2: float,
) -> int:
    """Find first nearest index for a given tolerance for two arrays and 2 values

    :param arr1: first array
    :param arr2: second arrat
    :param val1: value to find in first array
    :param val2: value to find in second array
    :return: index as int
    """
    return (np.abs(arr1 - val1) + np.abs(arr2 - val2)).argmin()
