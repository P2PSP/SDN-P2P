#!/bin/bash

samples=100

for (( t=10; t<=100; t+=10))
do
    for (( i=1; i <= $samples; ++i ))
    do
	python3 fast_sim.py -z $t -t 3 -p 1 | grep -Eo "Detected in round [0-9]{1,}" | grep -Eo "[0-9]{1,}" >> fixed_$t.out
    done

    for (( i=1; i <= $samples; ++i ))
    do
	python3 fast_sim.py -z $t -t 0 -p 1 | grep -Eo "Detected in round [0-9]{1,}" | grep -Eo "[0-9]{1,}" >> var_$t.out
    done
done
