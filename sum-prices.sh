#!/bin/sh
set -eu
export LC_ALL=C
awk -F, 'NR>1 {sum+=$2} END {printf "%.2f\n", sum}' raw-data/prices.csv > total.txt
