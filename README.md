# Scrambling P2PSP in a SDN architecture

This repository is a part of the [sdn-lab](https://github.com/cristobalmedinalopez/sdn-lab) repository

Running an experiment with HPs, a S, an MP and a TP

## Run a set of experiments
```
./fxvsvr.sh
```
OR
```
./fxvsvr_hybrid.sh
```
It runs a set of `samples` for a network from 10 to 100 peers (step of 10) where a MP attacks the same target during all simulation vs a MP changing the target each round. For a totally SDN topology or for a mixed one. 

## Automatic Test

```
./run.sh [team_size] [port] [rounds_to_shuffle] [target_type]
```
OR
```
./run_hybrid.sh [team_size] [port] [rounds_to_shuffle] [target_type] [extra_peers]
```
Where `target_type` can be `0` for a fixed target during all session, or `1` for changing target in each round. Both of them are chosen by random. `extra_peers` is the number of peers which are not running in a managed network.

## Manual Test
### Run Mininet
Run a network with one switch and 9 hosts:
```
$ sudo mn --topo single,9 --mac --switch ovsk --controller remote
```
### Run Ryu App
```
$ ryu-manager scrambling_p2p.py --config-file scrambling_p2p.conf
```

The configuration for this experiment is in the config file `scrambling_p2p.conf`
Example:
- team_size = 8
- port = 12345 
- rounds_to_shuffle = 1

### Testing that it works properly

In mininet console run a HP for peers 1 to 6:
```
mininet> h[n] python3 dummy_hp.py -p 12345 -s 10.0.0.9 -z 8&
```
Where [n] is a number from 1 to 6.

Now run a TP in host 7:
```
mininet> h7 python3 dummy_tp.py -p 12345 -s 10.0.0.9 -z 8&
```
Now a MP in host 8 choosing as a target of the attack host 5:
```
mininet> h8 python3 dummy_mp.py -p 12345 -s 10.0.0.9 -z 8 -t 5&
```
Finally, run a S in host 9:
```
mininet> h9 python3 dummy_s.py -p 12345 -z 8
```
Is the attack detected? Who was being attacked when the TP detected it?
