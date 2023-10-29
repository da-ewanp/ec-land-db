from setuptools import setup, find_packages

setup(
    name="ec_land_db",
    version="0.0.1",
    author="Ewan Pinnington",
    author_email="ewan.pinnington@ecmwf.int",
    description="Experimental processing for land surface data",
    packages=find_packages(),
    install_requires=["pyyaml",
                      "black", 
                      "isort",
                      "flake8",
                      "pytest",
                      "dask-jobqueue==0.8.1",
                      "dask-mpi==2022.4.0",
                      "distributed==2023.1.1",
                      "bokeh==2.4.3",
                      "xarray==2023.1.0",
                      "py-xgboost==1.7.6",
                      "zarr==2.13.6"],
)
