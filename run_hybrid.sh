#!/bin/bash

pid_controller=0

#Config controller
team_size=$1
port=$2
rounds_to_shuffle=$3
target_mode=$4
extra_peers=$5

cat <<EOM >./scrambling_p2p_hybrid.conf
[DEFAULT]
team_size = $team_size
port = $port
rounds_to_shuffle = $rounds_to_shuffle
extra_peers = $extra_peers
EOM

# Run controller
ryu-manager scrambling_p2p_hybrid.py --config-file scrambling_p2p_hybrid.conf & 
pid_controller=$!
echo "Preparing the simulation..."
sleep 4

# Run mininet
sudo python net_hybrid.py $team_size $port $target_mode $extra_peers

# When finish, kill controller
kill -9 $pid_controller
