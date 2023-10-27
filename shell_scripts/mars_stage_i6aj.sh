#!/usr/bin/bash
#SBATCH --job-name=stage-mars
#SBATCH --qos=nf
#SBATCH --time=00:55:00
#SBATCH --cpus-per-task=12
#SBATCH --mem=24GB
#SBATCH --output=logfiles/stage-mars.%j.out
#SBATCH --error=logfiles/stage-mars.%j.out

DATE=$1
DATE_END=$2
OUTDIR=$3
EXPVER=$4
GRID=$5
# DATE="20200101"
# DATE_END="20201231"


mars <<EOF
stage,
    class=rd,
    date=${DATE}/to/${DATE_END},
    expver=${EXPVER},
    levtype=sfc,
    # param=8.128/9.128/66.128/67.128/80.228/81.228/82.228/146.128/147.128/167.128/168.128/182.128/205.128/243.128/240013/260038,
    param=8.128/9.128/66.128/67.128/81.228/167.128/168.128/182.128/243.128/240013/260038,
    # step=1/to/744/by/1,
    stream=oper,
    grid=${GRID},
    time=00:00:00,
    type=fc,
    target="${OUTDIR}/${EXPVER}_${DATE}_fc_[param].grb"

stage,
    class=rd,
    date=${DATE}/to/${DATE_END},
    expver=${EXPVER},
    levtype=sfc,
    # param=32.128/33.128/39.128/40.128/41.128/42.128/139.128/141.128/170.128/183.128/235.128/236.128/238.128,
    param=33.128/39.128/40.128/41.128/42.128/139.128/141.128/170.128/183.128/235.128/236.128/238.128/240015,
    stream=oper,
    time=00:00:00/to/23:00:00/by/1,
    grid=${GRID},
    type=an,
    target="${OUTDIR}/${EXPVER}_${DATE}_soil_[param].grb"

stage,
    class=rd,
    date=${DATE}/to/${DATE_END},
    expver=${EXPVER},
    levelist=1/2/3/4/5,
    levtype=sol,
    # param=33/238/228038/228141,
    param=33/238/228141,
    stream=oper,
    time=00:00:00/to/23:00:00/by/1,
    grid=${GRID},
    type=an,
    target="${OUTDIR}/${EXPVER}_${DATE}_snow_[param].grb"
EOF