#!/usr/bin/ksh
#SBATCH --job-name=process-forcing
#SBATCH --qos=nf
#SBATCH --time=00:15:00
#SBATCH --cpus-per-task=64
#SBATCH --mem=48GB
#SBATCH --output=logfiles/process-forcing.%j.out
#SBATCH --error=logfiles/process-forcing.%j.out
set -x

ml netcdf4
ml nco
ml cdo
ml openmpi
ml python3

DATELABEL=$1  # e.g. "20100200"
FNAME="forcing_ea_1_oper_1_${DATELABEL}.tar.gz"
INPUT="/ec/fwsm/lb/project/surface_forcing/era5"
OUTPUT=$2  # e.g. "/ec/res4/scratch/daep/ec_training_db_out"
CLIMFILE=$3
GRID=$4
WDIR="${OUTPUT}/${DATELABEL}"
CVARS0="Wind Wind_E Wind_N Tair Qair PSurf SWdown LWdown Rainf Snowf Ctpf"
FCFREQ=1

ZDTFORC=$(( FCFREQ * 3600 ))   # Forcing frequency in seconds 
LUSECtpf=${LUSECtpf:-true}     # extract/use convective precipitation fracton 

mkdir -p "${WDIR}"
cp "${INPUT}/${FNAME}" "${WDIR}/${FNAME}"
tar --transform="s/.grb$/_${DATELABEL}.grb/" -zxvf "${WDIR}"/"${FNAME}" -C "$WDIR"
rm -f "${WDIR}"/"${FNAME}"

for ff in ${CVARS0} lapseM
do
    if [[ ! -r ${WDIR}/${ff}_${DATELABEL}.grb ]]; then continue ; fi
    mars << EOF
    read,source="${WDIR}/${ff}_${DATELABEL}.grb",grid=${GRID},accuracy=16,
    target="${WDIR}/${ff}_${DATELABEL}_INTERP.grb"
EOF
    mv "${WDIR}/${ff}_${DATELABEL}_INTERP.grb" "${WDIR}/${ff}_${DATELABEL}.grb"
done

##========================================
## create netcdf files 
function create_cdl {

var=$1
long_name=$2
units=$3
ddate=$4

yyyy=$(echo "$ddate" | cut -c1-4)
mm=$(echo "$ddate" | cut -c5-6)
dd=$(echo "$ddate" | cut -c7-8)
if [[ $dd = '00' ]]; then
  # for LERA runs dd == 1
  dd='01'
fi

cat > "${var}_${DATELABEL}.cdl" << EOF

netcdf ${var} {
dimensions:
        time = UNLIMITED ; 
        x  = $NPOINTS ;
variables:
        int    x(x) ;
                x:long_name = "grid points" ;
                x:units="-" ;
        float  lat(x) ;
                lat:long_name = "latitude" ;
                lat:units = "degrees_north" ;
        float  lon(x) ;
                lon:long_name = "longidude" ;
                lon:units = "degrees_east" ;
        double time(time) ;
                time:long_name = "time" ;
                time:units = "seconds since $yyyy-$mm-$dd 00:00:00" ;
        float ${var}(time,x) ;
                ${var}:long_name = "${long_name}" ;
                ${var}:units = "${units}" ;

// global attributes:
                :SOURCE = "ECMWF" ;
                :GRID_POINTS = "gaussian grid " ;
                :CONVERTED = " from grib files with grib_api" ; 
}
EOF

rm -f "${var}_${DATELABEL}.nc"
ncgen -b "${var}_${DATELABEL}.cdl"
rm "${var}_${DATELABEL}.cdl"
}
##=================================================

## create empty nc forcing files 
NPOINTS=$(ncdump -h $CLIMFILE | grep "x = " | awk '{print $3}' )
## change into working dir
cd "${WDIR}/" || exit

##=================================================
## --- 3 --- convert grib to netcdf ! 
##===================================

CVARS=""
for ff in $CVARS0
do
  if [[ -r ${ff}_${DATELABEL}.grb ]]; then
    CVARS="$CVARS ${ff}"
    case $ff in
      Wind)     create_cdl 'Wind'   'Wind speed ' ' m/s' "$DATELABEL" ;;
      Wind_E)   create_cdl 'Wind_E' 'Wind speed u' 'u m/s' "$DATELABEL" ;;
      Wind_N)   create_cdl 'Wind_N' 'Wind speed v' 'v m/s' "$DATELABEL" ;;
      Tair)     create_cdl 'Tair'   'Temperature' 'K' "$DATELABEL" ;;
      Qair)     create_cdl 'Qair'   'Specific humidity' 'kg/kg' "$DATELABEL" ;;
      CO2air)   create_cdl 'CO2air' 'Atmospheric carbon dioxide' 'kg/kg' "$DATELABEL" ;;
      PSurf)    create_cdl 'PSurf'  'Pressure' 'Pa' "$DATELABEL" ;;
      SWdown)   create_cdl 'SWdown' 'Downward shortwave radiation' 'W/m2' "$DATELABEL" ;;
      LWdown)   create_cdl 'LWdown' 'Downward longwave radiation' 'W/m2' "$DATELABEL" ;;
      Rainf)    create_cdl 'Rainf'  'Rainfall rate (convective + stratiform)' 'kg/m2s' "$DATELABEL" ;;
      Snowf)    create_cdl 'Snowf'  'Snowfall (convective + stratiform)' 'kg/m2s' "$DATELABEL" ;;
      Ctpf)     create_cdl 'Ctpf'   'Convective total precipitation fraction (convective + stratiform)' '-' "$DATELABEL" ;;
    esac
  fi
done

for var in $CVARS 
do
  echo "$var" 
  ## 3.2 create input namelist 
if [[ $var == CO2air ]]; then
cat > input.nam <<EOF
&INPUT
  GRIB_FILE='${var}_${DATELABEL}.grb'
  NETCDF_FILE='${var}_${DATELABEL}.nc'
  VAR_NAME='${var}'
  INFO_FILE='$CLIMFILE'
  ZDTFORC=${CO2ZDTFORC}
/
EOF
else
cat > input.nam <<EOF
&INPUT
  GRIB_FILE='${var}_${DATELABEL}.grb'
  NETCDF_FILE='${var}_${DATELABEL}.nc'
  VAR_NAME='${var}'
  INFO_FILE='$CLIMFILE'
  ZDTFORC=${ZDTFORC}
/
EOF
fi

  ## 3.3 run conv_forcing 
  /home/daep/osm/src/CY48R1.perturb/osm/gnu-opt/build/bin/conv_forcing.exe
  if [ $? -ne 0 ]; then
    echo "some probelm in conv_forcing"
    exit 1
  fi 
  rm -f input.nam
  rm "${var}_${DATELABEL}.grb"
  done

## interpolate CO2 forcing in time (if FREQ is hourly)
# if [[ $LEAIRCO2COUP = true ]]; then
#   if [[ $CO2FCFREQ != "$FCFREQ" ]]; then
#     mv CO2air.nc CO2air_tmp.nc
#     cdo -intntime,3 CO2air_tmp.nc CO2air.nc
#     rm -f CO2air_tmp.nc
#   fi
# fi

if [[ $LUSECtpf = true ]]; then
  ncks -A -v Ctpf Ctpf_"${DATELABEL}".nc Rainf_"${DATELABEL}".nc 
fi 

python3 /home/daep/projects/ec_land_db/ec_land_db/nc2zarr.py \
        -nc "*.nc" \
        -out "${OUTPUT}/ecland_era5forcing_${DATELABEL}.zarr" \
        -tstep "6H"

rm ./*.nc
rm ./*.grb*
cd "$OUTPUT" || exit
rmdir "$WDIR"
