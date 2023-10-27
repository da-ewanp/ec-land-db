#!/usr/bin/bash

OUTDIR="/ec/res4/scratch/daep/ec_training_db_out"
START_DATE="20220201"
END_DATE="20221201"
EXPVER="i6aj"
CLIMFILE="/home/daep/projects/ec_land_db/ec_land_db/scratch/surfclim_399_l4"
GRID="O400"

sbatch mars_stage_i6aj.sh $START_DATE $END_DATE $OUTDIR $EXPVER $GRID

# Loop through and extract ec-land ERA5 forcing and convert to Zarr
i="$START_DATE"
while [[ $(date +%s -d "$i") -le $(date +%s -d $END_DATE) ]];
    do
    echo "Running process_forcing for ${i}..."
    sbatch process_forcing.sh $(( i - 1 )) $OUTDIR $CLIMFILE $GRID
    i=$(date -d "$i + 1 month" +%Y%m%d)
done

# Loop through extract ec-land outputs from Mars and convert to Zarr
i="$START_DATE"
while [[ $(date +%s -d "$i") -le $(date +%s -d $END_DATE) ]];
    do
    echo "Running Mars extraction and zarr conversion for ${i}..."
    ./mars_req_i6aj.sh "$i" $OUTDIR $EXPVER $GRID
    sbatch grib2zarr.sh $OUTDIR "$i" $EXPVER $CLIMFILE
    i=$(date -d "$i + 1 month" +%Y%m%d)
done