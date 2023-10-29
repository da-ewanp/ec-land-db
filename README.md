# ai-land data processing and model training

This project is setup to create a Machine Learning database for the land surface, with data coming from the ec-land model. We deal with grabbing data from Mars as GRIB files, converting these GRIB files to Zarr and then finally concatenating these into a single Zarr-Store with a predefined chunking strategy.

## Grabbing data from Mars

Some more info here...

## Converting GRIB to Zarr

The `src/grib2zarr.py` file converts GRIB files to Zarr using the `config.yaml` file as a config for the different model streams. Wethen concatenate these into a single Zarr-store.

## Converting netCDF to Zarr

The `src/nc2zarr.py` file converts netcdf files to Zarr using the `config.yaml` file as a config for the different model streams. Here we are extracting preprocessed ec-land model forcing from the `/ec/fwsm/lb` drive.

## Example data processing workflow

```mermaid
  graph TD;
      H[shell_scripts/main.sh];
      H--> A1;
      H--> A2;
      H--> A3;
      A1[mars_req.sh: download of ec-land\n model data month 1 to GRIB];
      A2[...]; 
      A3[mars_req.sh: download of ec-land\n model data month N to GRIB];
      A1-- grib -->C[grib2zarr.py:\n Process file month 1 to Zarr];
      A2-- grib -->D[...];
      A3-- grib -->E[grib2zarr.py:\n Process file month N to Zarr];
      C-- zarr -->F[create_zarr_store.ipynb: Create single Zarr-Store];
      D-- zarr -->F;
      E-- zarr -->F;
```