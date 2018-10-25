import argparse
from random import sample
from collections import OrderedDict


def create_team(team_size):
    peer_list = []
    for i in range(0, team_size):
        peer_list.append(i)
    return peer_list


def scramble(peer_list):
    peer_list_random = sample(peer_list, len(peer_list))
    return OrderedDict(zip(peer_list, peer_list_random))


def is_detected(peer_list_random, target, tp):
    if peer_list_random[target] == tp:
        return True
    else:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-z", "--size", type=int,
                        help="Team size (without splitter)")
    parser.add_argument("-e", "--extra_peers", default=0, type=int,
                        help="Peers out of the SDN")
    parser.add_argument("-t", "--target", default=0, type=int,
                        help="Target")
    parser.add_argument("-p", "--period", default=1, type=int,
                        help="Scrambling Period")
    args = parser.parse_args()

    peer_list = create_team(args.size)
    number_of_round = 0
    tp = len(peer_list) - 2
    print("TP is {}".format(tp))
    detected = False
    while not detected:
        if number_of_round % args.period == 0:
            peer_list_random = scramble(peer_list)
        print("peer_list_random", peer_list_random)
        number_of_round += 1
        if args.target == 0:
            target = sample(peer_list[0:len(peer_list)-1], 1)[0]
        else:
            target = args.target
        print("Target is {}".format(target))
        detected = is_detected(peer_list_random, target, tp)
    print("Detected in round {}".format(number_of_round))
