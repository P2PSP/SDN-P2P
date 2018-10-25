#!/bin/bash

samples=30

for ((extra_peers=20; extra_peers <= 50; extra_peers=extra_peers+10))
do
    for ((t=100; t <= 100; t=t+10))
    do
	for (( i=0; i < $samples; ++i ))
	do
	    ./run_hybrid.sh $(($t-$extra_peers)) 12345 1 0 $extra_peers | grep -Eo 'MP detected in round [0-9]{1,}' | grep -Eo '[0-9]{1,}' >> fixed_hybrid_$t_$extra_peers.out
	done

	#cat fixed_$t.out | sort | uniq -c > fixed_count_$t.dat
	avg=$(awk '{ total += $1; count++ } END { print total/count }' fixed_hybrid_$t_$extra_peers.out)
	echo -e $t "\t" $extra_peers "\t" $avg >> fixed_hybrid.dat

	for (( i=0; i < $samples; ++i ))
	do
	    ./run_hybrid.sh $(($t-$extra_peers)) 12345 1 1 $extra_peers | grep -Eo 'MP detected in round [0-9]{1,}' | grep -Eo '[0-9]{1,}' >> var_hybrid_$t_$extra_peers.out
	done

	#cat var_$t.out | sort | uniq -c > var_count_$t.dat
	avg=$(awk '{ total += $1; count++ } END { print total/count }' var_hybrid_$t_$extra_peers.out)
	echo -e $t "\t" $extra_peers "\t" $avg >> var_hybrid.dat
    done
done
