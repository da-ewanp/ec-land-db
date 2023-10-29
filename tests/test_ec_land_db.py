import pytest
import xarray as xr
import numpy as np
import pandas as pd
from ec_land_db.grib2zarr import preprocess_fc_grib, preprocess_an_grib
from ec_land_db.utils import update_longitude


@pytest.fixture
def mock_dataset():
    lon_values = np.arange(0, 360, 10)
    ds = xr.Dataset({"temperature": (["lon"], np.random.rand(len(lon_values)))})
    ds["lon"] = lon_values
    ds.lon.attrs["units"] = "deg_east"
    ds.lon.attrs["long_name"] = "lon"
    ds.lon.attrs["standard_name"] = "lon"
    return ds


@pytest.fixture
def mock_fc_dataset():
    ds = xr.Dataset(
        {
            "e": (
                ["step", "values"],
                [[4.122e-07, 8.002e-07], [None, None]],
            ),
        },
        coords={
            "step": [pd.Timedelta("1 hours"), pd.Timedelta("2 hours")],
            "values": [0, 1],
            "number": 0,
            "time": pd.to_datetime("2018-12-01"),
            "surface": 0.0,
            "latitude": [72.52, 72.52],
            "longitude": [72.44, 73.54],
            "valid_time": [
                pd.to_datetime("2018-12-01T01:00:00"),
                pd.to_datetime("2018-12-01T02:00:00"),
            ],
        },
    )
    return ds


@pytest.fixture
def mock_an_dataset():
    ds = xr.Dataset(
        {
            "tsn": (
                ["time", "snowLayer", "values"],
                [
                    [[235.6, 249.7], [None, 249.5]],
                    [[236.6, 249.8], [None, 249.6]],
                ],
            ),
        },
        coords={
            "time": [
                pd.to_datetime("2018-12-01"),
                pd.to_datetime("2018-12-01T01:00:00"),
            ],
            "step": pd.Timedelta("0 hours"),
            "snowLayer": [1.0, 2.0],
            "latitude": [72.52, 72.52],
            "longitude": [72.44, 73.54],
            "valid_time": [
                pd.to_datetime("2018-12-01"),
                pd.to_datetime("2018-12-01T01:00:00"),
            ],
        },
    )
    return ds


def test_update_longitude(mock_dataset):
    # Call the function with the mock dataset
    result = update_longitude(mock_dataset)

    # Check if the 'lon' coordinate values are in the range (-180, 180)
    assert np.all(result.sortby("lon").lon.values == np.arange(-180, 180, 10))

    # Check if the attributes have been updated
    assert result.lon.attrs["units"] == "degrees_east"
    assert result.lon.attrs["long_name"] == "longitude"
    assert result.lon.attrs["standard_name"] == "longitude"

    # Check that the data variables in the dataset are not affected
    assert "temperature" in result.variables


def test_preprocess_fc_grib(mock_fc_dataset):
    # Call the function with the mock fc dataset
    result = preprocess_fc_grib(mock_fc_dataset)

    # Check if the dimensions "latitude" and "longitude" have been dropped
    assert "latitude" not in result.dims
    assert "longitude" not in result.dims

    # Check if the dimensions "step" has been renamed to "time"
    assert "step" not in result.dims
    assert "time" in result.dims

    # Check if the "valid_time" attribute has been set to "time"
    assert np.all(result.time.values == mock_fc_dataset.valid_time.values)

    # Check that the "x" variable exists
    assert "x" in list(result.dims)

    # Check that the "lon" coordinate exists
    assert "lon" in result.coords

    # Check if the 'lon' coordinate values are in the range (-180, 180)
    assert np.all(result.lon >= -180)
    assert np.all(result.lon <= 180)


def test_preprocess_an_grib(mock_an_dataset):
    # Call the function with the mock an dataset
    result = preprocess_an_grib(mock_an_dataset)

    # Check if the dimensions "latitude", "longitude", and "time" have been dropped
    assert "latitude" not in result.dims
    assert "longitude" not in result.dims

    # Check if the dimensions "snowLayer" has been renamed to "x"
    assert "snowLayer" not in result.dims
    assert "x" in result.dims

    # Check if the data variables have been flattened into new variables with "_l{layer}" suffix
    assert "tsn_l1" in result.variables
    assert "tsn_l2" in result.variables

    # Check if the 'lon' coordinate exists
    assert "lon" in result.coords

    # Check if the 'lon' coordinate values are in the range (-180, 180)
    assert np.all(result.lon >= -180)
    assert np.all(result.lon <= 180)
