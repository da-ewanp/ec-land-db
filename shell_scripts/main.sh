#!/usr/bin/bash

function parse_yaml {
   local prefix=$2
   local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
   sed -ne "s|^\($s\):|\1|" \
        -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  "$1" |
   awk -F"$fs" '{
      indent = length($1)/2;
      vname[indent] = $2;
      for (i in vname) {if (i > indent) {delete vname[i]}}
      if (length($3) > 0) {
         vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
         printf("%s%s%s=\"%s\"\n", "'"$prefix"'",vn, $2, $3);
      }
   }'
}

eval "$(parse_yaml ../config.yaml "conf_")"
printf "Loaded yaml config with:%s\n$(parse_yaml ../config.yaml)%s\n"

sbatch mars_stage_i6aj.sh "$conf_start_date" "$conf_end_date" "$conf_output_dir" "$conf_expver" "$conf_grid"

# Loop through and extract ec-land ERA5 forcing and convert to Zarr
i="$conf_start_date"
while [[ $(date +%s -d "$i") -le $(date +%s -d "$conf_end_date") ]];
    do
    echo "Running process_forcing for ${i}..."
    sbatch process_forcing.sh $(( i - 1 )) "$conf_output_dir" "$conf_climfile" "$conf_grid"
    i=$(date -d "$i + 1 month" +%Y%m%d)
done

# Loop through extract ec-land outputs from Mars and convert to Zarr
i="$conf_start_date"
while [[ $(date +%s -d "$i") -le $(date +%s -d "$conf_end_date") ]];
    do
    echo "Running Mars extraction and zarr conversion for ${i}..."
    ./mars_req_i6aj.sh "$i" "$conf_output_dir" "$conf_expver" "$conf_grid"
    sbatch grib2zarr.sh "$conf_output_dir" "$i" "$conf_expver" "$conf_climfile"
    i=$(date -d "$i + 1 month" +%Y%m%d)
done