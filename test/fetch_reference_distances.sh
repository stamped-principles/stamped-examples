#!/bin/sh
# Fetch GSP-Phot reference distances for the exact stars we computed
set -eu

ids=$(tail -n +2 output/distances.csv | cut -d, -f1 | paste -sd,)

curl -s -o test/reference_distances.csv \
  --data-urlencode "REQUEST=doQuery" \
  --data-urlencode "LANG=ADQL" \
  --data-urlencode "FORMAT=csv" \
  --data-urlencode "QUERY=SELECT source_id, distance_gspphot FROM gaiadr3.gaia_source WHERE source_id IN ($ids) AND distance_gspphot IS NOT NULL" \
  "https://gea.esac.esa.int/tap-server/tap/sync"

echo "Fetched $(tail -n +2 test/reference_distances.csv | wc -l) reference distances"
