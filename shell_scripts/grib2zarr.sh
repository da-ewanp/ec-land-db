#!/usr/bin/bash
#SBATCH --job-name=slurm-grib2zarr
#SBATCH --qos=nf
#SBATCH --time=00:15:00
#SBATCH --cpus-per-task=64
#SBATCH --mem=48GB
#SBATCH --output=logfiles/slurm-grib2zarr.%j.out
#SBATCH --error=logfiles/slurm-grib2zarr.%j.out

module load ecmwf-toolbox
module load python3
set -x

OUTDIR=$1
DATE=$2
EXPVER=$3
CLIMFILE=$4
DATE_PREV_MONTH=$(date -d "${DATE} - 1 day" +%Y%m%d)

python3 ../ec_land_db/grib2zarr.py \
        -fc "${OUTDIR}/${EXPVER}_${DATE}_fc_*.grb" "${OUTDIR}/${EXPVER}_${DATE_PREV_MONTH}_fc_*.grb" \
        -an "${OUTDIR}/${EXPVER}_${DATE}_soil_*.grb" "${OUTDIR}/${EXPVER}_${DATE}_snow_*.grb" \
        -out "${OUTDIR}/${EXPVER}_${DATE}.zarr" \
        -clim "$CLIMFILE" \
        -tstep "6H"

rm "${OUTDIR}"/"${EXPVER}"_"${DATE}"_fc_*.grb* "${OUTDIR}"/"${EXPVER}"_"${DATE_PREV_MONTH}"_fc_*.grb* "${OUTDIR}"/"${EXPVER}"_"${DATE}"_soil_*.grb* "${OUTDIR}"/"${EXPVER}"_"${DATE}"_snow_*.grb*
