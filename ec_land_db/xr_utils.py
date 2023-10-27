#!/usr/bin/python3
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
