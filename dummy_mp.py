import socket
import argparse
from random import randint
from dummy_hp import DummyHP


class DummyMP(DummyHP):

    def __init__(self, port, splitter, peer_list, targets, split):
        super().__init__(port, splitter, peer_list)
        self.targets = targets
        self.port = port
        self.split = split
        print("I'm a DummyMP")

    def run(self):
        while True:
            data, address = self.receive()
            print("{} received from {}".format(data, address))
            if data == "-9":
                exit()
            if address[0] == self.splitter:
                if len(self.targets) == 0:
                    p = randint(1, len(peer_list))
                    if args.split:
                        if p <= hosts//2:
                            target = ("10.0.0."+str(p), self.port)
                        else:
                            target = ("11.0.0."+str(p), self.port)
                    else:
                        target = ("10.0.0."+str(p), self.port)
                    targets = [target]
                    print("New Target: {}".format(targets[0]))
                else:
                    targets = self.targets[:]
                for p in self.peer_list:
                    if p in targets:
                        self.send(0, p)
                        print("\t{} sent to {} Attack!".
                              format(str(0), p))
                    else:
                        self.send(data, p)
                        print("\t{} sent to {}".format(data, p))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int,
                        help="UDP port used by peers")
    parser.add_argument("-s", "--splitter", type=str,
                        help="Splitter address")
    parser.add_argument("-z", "--size", type=int,
                        help="Team size (without splitter)")
    parser.add_argument("-t", "--targets", type=int, nargs='+',
                        help="List of peer to attack (ex. 1 2 4)")
    parser.add_argument("-e", "--extra_peers", default=0, type=int,
                        help="Peers out of the SDN")
    parser.add_argument("--split", default=False,
                        action='store_true',
                        help="Distribute the team in 2 switches")
    args = parser.parse_args()

    peer_list = []
    hosts = args.size+1
    if args.split:
        for p in range(0, hosts//2):
            peer_list.append(("10.0.0."+str(p+1), args.port))
        for p in range(hosts//2, hosts-1):
            peer_list.append(("11.0.0."+str(p+1), args.port))
        for p in range(hosts, hosts + args.extra_peers):
            peer_list.append(("172.31.31."+str(p+1), args.port))
    else:
        for p in range(0, hosts-1):
            peer_list.append(("10.0.0."+str(p+1), args.port))

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((args.splitter, 1))
    local_ip_address = s.getsockname()[0]

    print("Local IP {}".format(local_ip_address))
    peer_list.remove((local_ip_address, args.port))
    print("Peers List:{}".format(peer_list))

    targets = []
    for p in args.targets:
        if p != 0:
            if args.split:
                if p <= hosts//2:
                    targets.append(("10.0.0."+str(p), args.port))
                elif p > hosts//2 and p < hosts:
                    targets.append(("11.0.0."+str(p), args.port))
                else:
                    targets.append(("172.31.31."+str(p), args.port))
            else:
                targets.append(("10.0.0."+str(p), args.port))

    print("Targets List:{}".format(targets))

    peer = DummyMP(args.port, args.splitter, peer_list, targets, args.split)
    peer.run()
