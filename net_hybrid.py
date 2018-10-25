#!/usr/bin/python

import sys
from random import randint
from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
from mininet.node import Node
from mininet.cli import CLI


class LinuxRouter(Node):
    "A Node with IP forwarding enabled."

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):

    def build(self, hosts=9, extra_peers=0):

        # Create Router
        defaultIP = '172.31.31.254/24'  # IP address for r0-eth1
        router = self.addNode('r0', cls=LinuxRouter, ip=defaultIP)

        # Create a switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Create router links
        self.addLink(s1, router, intfName2='r0-eth1',
                     params2={'ip': defaultIP})
        self.addLink(s2, router, intfName2='r0-eth2',
                     params2={'ip': '10.0.0.254/8'})
        self.addLink(s3, router, intfName2='r0-eth3',
                     params2={'ip': '11.0.0.254/8'})
        
        # Create and link hosts.
        for h in range(0, hosts//2):
            self.addLink(self.addHost('h%s' % (h+1),
                                      ip='10.0.0.%s/24' % (h+1),
                                      defaultRoute='via 10.0.0.254'), s2)

        for h in range(hosts//2, hosts-1):
            self.addLink(self.addHost('h%s' % (h+1),
                                      ip='11.0.0.%s/24' % (h+1),
                                      defaultRoute='via 11.0.0.254'), s3)

        self.addLink(self.addHost('h%s' % (hosts),
                                  ip='172.31.31.%s/24' % (hosts),
                                  defaultRoute='via 172.31.31.254'), s1)

        for h in range(hosts, hosts+extra_peers):
            self.addLink(self.addHost('h%s' % (h+1),
                                      ip='172.31.31.%s/24' % (h+1),
                                      defaultRoute='via 172.31.31.254'), s1)


def runNetworkTopo(team_size, port, target_mode, extra_peers):
    "Bootstrap a Mininet network using the Minimal Topology"

    # Create an instance of our topology
    hosts = team_size + 1
    topo = NetworkTopo(hosts, extra_peers)

    # Create a network based on the topology using OVS and controlled by
    # a remote controller.
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(name, ip='127.0.0.1'),
        switch=OVSSwitch,
        autoSetMacs=True)

    # Actually start the network
    net.start()
    print("IP splitter", net.hosts[hosts-1].IP())
    print(net.hosts[hosts-1].cmd("echo -n a | nc -u -w 1 10.0.0.1 12345"))
    print(net.hosts[hosts-1].cmd("echo -n a | nc -u -w 1 11.0.0.{} 12345".format(hosts-1)))

    id_host = 0
    for host in net.hosts[0:- (4 + extra_peers)]:
        id_host += 1
        do_log = " &"
        if __debug__:
            do_log = " > " + str(id_host) + ".log &"
        run_hp = "python3 -u dummy_hp.py -p " + str(port) + \
                 " -s 172.31.31." + str(hosts) + " -z " \
                 + str(team_size) + " -e " + str(extra_peers) \
                 + " --split" + str(do_log)
        host.cmd(run_hp)
        print(host, ":", run_hp)
    print("HPs running")

    if __debug__:
        id_host += 1
        do_log = " > " + str(id_host) + ".log &"
    run_tp = "python3 -u dummy_tp.py -p " + str(port) + " -s 172.31.31." \
             + str(hosts) + " -z " + str(team_size) + " -e " \
             + str(extra_peers) + " --split" + str(do_log)
    net.hosts[- (4 + extra_peers)].cmd(run_tp)
    print(net.hosts[- (4 + extra_peers)], ":", run_tp)
    print("TP running")

    if __debug__:
        id_host += 1
        do_log = " > " + str(id_host) + ".log &"
    if target_mode == 0:
        target = randint(1, team_size-1)
    else:
        target = 0
    run_mp = "python3 -u dummy_mp.py -p " + str(port) + " -s 172.31.31." \
             + str(hosts) + " -z " + str(team_size) + " -t " + str(target) \
             + " -e " + str(extra_peers) + " -e " + str(extra_peers) \
             + " --split" + str(do_log)
    net.hosts[- (3 + extra_peers)].cmd(run_mp)
    print(net.hosts[- (3 + extra_peers)], ":", run_mp)
    print("MP running with traget = {}".format(target))

    # Extra peers (peers out of the SDN)
    id_host += 1  # splitter id
    for host in net.hosts[- (1 + extra_peers): (hosts + extra_peers)]:
        id_host += 1
        do_log = " &"
        if __debug__:
            do_log = " > " + str(id_host) + ".log &"
        run_hp = "python3 -u dummy_hp.py -p " + str(port) + \
                 " -s 172.31.31." + str(hosts) + " -z " \
                 + str(team_size) + " -e " + str(extra_peers) \
                 + " --split" + str(do_log)
        host.cmd(run_hp)
        print(host, ":", run_hp)
    print("HPs running in extra peers")

    print("Running splitter...")
    run_s = "python3 -u dummy_s.py -p " + str(port) + " -z " + str(team_size) \
            + " -e " + str(extra_peers) + " --split"
    print(net.hosts[- (2 + extra_peers)], ":", run_s)

    results = net.hosts[- (2 + extra_peers)].cmd(run_s)
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
    extra_peers = int(sys.argv[4])
    runNetworkTopo(team_size, port, target_mode, extra_peers)

# Allows the file to be imported using `mn --custom <filename> --topo minimal`
topos = {
    'min': NetworkTopo
}
