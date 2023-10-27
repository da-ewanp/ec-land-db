#!/usr/bin/bash

#DATE="20200101"
DATE=$1
OUTDIR=$2
EXPVER=$3
GRID=$4
DATE_END=$(date -d "${DATE} + 1 month - 1 day" +%Y%m%d)
DAYS=$(date -d "${DATE_END}" +%d)
STEPS=$((DAYS * 24))
DATE_PREV_MONTH=$(date -d "${DATE} - 1 day" +%Y%m%d)
STEPS_PREV_MONTH=$(($(date -d "${DATE} - 1 day" +%d) * 24))

export MARS_MULTITARGET_STRICT_FORMAT=1

mars <<EOF
retrieve,
    class=rd,
    date=$(date -d "${DATE} - 1 month" +%Y%m%d),
    expver=${EXPVER},
    levtype=sfc,
    # param=8.128/9.128/66.128/67.128/80.228/81.228/82.228/146.128/147.128/167.128/168.128/182.128/205.128/243.128/240013/260038,
    # param=8.128/9.128/66.128/67.128/81.228/167.128/168.128/182.128/243.128/240013/260038,
    param=8.128/9.128/66.128/67.128/81.228/167.128/168.128/182.128/243.128/240013/260038,
    step=${STEPS_PREV_MONTH},
    stream=oper,
    time=00:00:00,
    type=fc,
    grid=${GRID},
    target="${OUTDIR}/${EXPVER}_${DATE_PREV_MONTH}_fc_[param].grb"

retrieve,
    class=rd,
    date=${DATE},
    expver=${EXPVER},
    levtype=sfc,
    # param=8.128/9.128/66.128/67.128/80.228/81.228/82.228/146.128/147.128/167.128/168.128/182.128/205.128/243.128/240013/260038,
    # param=8.128/9.128/66.128/67.128/81.228/167.128/168.128/182.128/243.128/240013/260038,
    param=8.128/9.128/66.128/67.128/81.228/167.128/168.128/182.128/243.128/240013/260038,
    step=1/to/$((STEPS -1))/by/1,
    stream=oper,
    time=00:00:00,
    type=fc,
    grid=${GRID},
    target="${OUTDIR}/${EXPVER}_${DATE}_fc_[param].grb"
EOF

mars  <<EOF
retrieve,
    class=rd,
    date=${DATE}/to/${DATE_END},
    expver=${EXPVER},
    levtype=sfc,
    # param=32.128/33.128/39.128/40.128/41.128/42.128/139.128/141.128/170.128/183.128/235.128/236.128/238.128,
    param=33.128/39.128/40.128/41.128/42.128/139.128/141.128/170.128/183.128/235.128/236.128/238.128/240015,
    stream=oper,
    time=00:00:00/to/23:00:00/by/1,
    type=an,
    grid=${GRID},
    target="${OUTDIR}/${EXPVER}_${DATE}_soil_[param].grb"
EOF

mars  <<EOF
retrieve,
    class=rd,
    date=${DATE}/to/${DATE_END},
    expver=${EXPVER},
    #levelist=1/2/3/4/5,
    levelist=1/2,
    levtype=sol,
    # param=33/238/228038/228141,
    param=33/238/228141,
    stream=oper,
    time=00:00:00/to/23:00:00/by/1,
    type=an,
    grid=${GRID},
    target="${OUTDIR}/${EXPVER}_${DATE}_snow_[param].grb"
EOF