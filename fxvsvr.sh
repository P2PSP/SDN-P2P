#!/bin/bash

samples=30

for ((t=10; t <= 100; t=t+10))
do
    
    for (( i=0; i < $samples; ++i ))
    do
	./run.sh $t 12345 1 0 | grep -Eo 'MP detected in round [0-9]{1,}' | grep -Eo '[0-9]{1,}' >> fixed_$t.out
    done

    #cat fixed_$t.out | sort | uniq -c > fixed_count_$t.dat
    avg=$(awk '{ total += $1; count++ } END { print total/count }' fixed_$t.out)
    echo -e $t "\t" $avg >> fixed.dat

    for (( i=0; i < $samples; ++i ))
    do
	./run.sh $t 12345 1 1 | grep -Eo 'MP detected in round [0-9]{1,}' | grep -Eo '[0-9]{1,}' >> var_$t.out
    done

    #cat var_$t.out | sort | uniq -c > var_count_$t.dat
    avg=$(awk '{ total += $1; count++ } END { print total/count }' var_$t.out)
    echo -e $t "\t" $avg >> var.dat
done
