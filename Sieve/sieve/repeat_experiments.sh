#!/usr/bin/env bash

# Script to run N experimental repetitions over the three available interaction
# sequences

echo "Running $1 repetitions"
echo "Saving to $2"

for i in $(seq 1 $1)
do
	mkdir -p $2/$i/sl1024afr98_results
	./expmgmt.py --interaction-sequences sl1024afr98 \
		--output-dir-prefix $2/$i
	killall python3
	mkdir -p $2/$i/g1sl1024afr98_results
	./expmgmt.py --interaction-sequences g1sl1024afr98 \
		--output-dir-prefix $2/$i
	killall python3
	mkdir -p $2/$i/g4sl1024afr98_results
	./expmgmt.py --interaction-sequences g4sl1024afr98 \
		--output-dir-prefix $2/$i
	killall python3
done
