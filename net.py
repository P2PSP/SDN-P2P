#!/usr/bin/python

import sys
from random import randint
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch


class MinimalTopo(Topo):
    "Minimal topology with a single switch and two hosts"

    def build(self, hosts=9):
        # Create a switch
        s1 = self.addSwitch('s1')

        # Create two hosts.
        for h in range(0, hosts):
            self.addLink(s1, self.addHost('h%s' % (h + 1)))


def runMinimalTopo(team_size, port, target_mode):
    "Bootstrap a Mininet network using the Minimal Topology"

    # Create an instance of our topology
    hosts = team_size + 1
    topo = MinimalTopo(hosts)

    # Create a network based on the topology using OVS and controlled by
    # a remote controller.
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(name, ip='127.0.0.1'),
        switch=OVSSwitch,
        autoSetMacs=True)

    # Actually start the network
    net.start()

    id_host = 0
    for host in net.hosts[:-3]:
        id_host += 1
        do_log = " &"
        if __debug__:
            do_log = " > " + str(id_host) + ".log &"
        run_hp = "python3 -u dummy_hp.py -p " + str(port) + " -s 10.0.0." \
                 + str(hosts) + " -z " + str(team_size) + str(do_log)
        host.cmd(run_hp)
        print(run_hp)
    print("HPs running")

    if __debug__:
        do_log = " > " + str(id_host+1) + ".log &"
    run_tp = "python3 -u dummy_tp.py -p " + str(port) + " -s 10.0.0." \
             + str(hosts) + " -z " + str(team_size) + str(do_log)
    net.hosts[-3].cmd(run_tp)
    print(run_tp)
    print("TP running")

    if __debug__:
        do_log = " > " + str(id_host+2) + ".log &"
    if target_mode == 0:
        target = randint(1, team_size-1)
    else:
        target = 0
    run_mp = "python3 -u dummy_mp.py -p " + str(port) + " -s 10.0.0." \
             + str(hosts) + " -z " + str(team_size) + " -t " + str(target) \
             + str(do_log)
    net.hosts[-2].cmd(run_mp)
    print(run_mp)
    print("MP running with traget = {}".format(target))

    print("Running splitter...")
    run_s = "python3 dummy_s.py -p " + str(port) + " -z " + str(team_size)
    results = net.hosts[-1].cmd(run_s)
    print(results)
    # Drop the user in to a CLI so user can run commands.
    # CLI(net)

    # After the user exits the CLI, shutdown the network.
    net.stop()


if __name__ == '__main__':
    # This runs if this file is executed directly
    setLogLevel('info')
    team_size = int(sys.argv[1])
    port = int(sys.argv[2])
    target_mode = int(sys.argv[3])
    runMinimalTopo(team_size, port, target_mode)

# Allows the file to be imported using `mn --custom <filename> --topo minimal`
topos = {
    'min': MinimalTopo
}
