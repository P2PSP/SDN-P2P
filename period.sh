#!/bin/bash

samples=100

for (( period=1; period <= 16; period*=2))
do
    for (( i=1; i <= $samples; ++i ))
    do
	python3 fast_sim.py -z 100 -t 3 -p $period | grep -Eo "Detected in round [0-9]{1,}" | grep -Eo "[0-9]{1,}" >> period_$period.out
done
    sort -n period_$period.out | uniq -c | tr -s ' ' | awk '{s+=$1; print $2, $1, s}' > period_$period.dat
done
