.POSIX:
SIF = env.sif

all: total.txt

total.txt: raw-data/prices.csv sum-prices.sh $(SIF)
	singularity exec --cleanenv $(SIF) ./sum-prices.sh

clean:
	rm -f total.txt

.PHONY: all clean
