.POSIX:

all: output/distances.csv

raw/gaia_nearby.csv:
	python3 code/fetch_data.py raw/gaia_nearby.csv

output/distances.csv: raw/gaia_nearby.csv code/compute_distances.py
	python3 code/compute_distances.py raw/gaia_nearby.csv output/distances.csv

clean:
	rm -f output/distances.csv

.PHONY: all clean
