from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto.ofproto_v1_2 import OFPG_ANY
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import udp
from ryu import cfg
from random import sample
from collections import OrderedDict


class ScramblingP2P(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ScramblingP2P, self).__init__(*args, **kwargs)

        self.peers_list = []
        self.ip_to_mac = {}
        self.mac_to_port = {}
        self.rounds_shuffle_counter = 0

        cfg.CONF.register_opts([
            cfg.IntOpt('team_size', default=8,
                       help=('Size of the team')),
            cfg.IntOpt('port', default=12345,
                       help=('UDP port for all')),
            cfg.IntOpt('rounds_to_shuffle', default=1,
                       help=('Rounds to shuffle'))
        ])
        self.rounds_to_shuffle = cfg.CONF.rounds_to_shuffle
        self.splitter = "10.0.0."+str(cfg.CONF.team_size+1)
        for h in range(0, cfg.CONF.team_size):
            self.peers_list.append(("10.0.0."+str(h+1), cfg.CONF.port))
        self.logger.info("List of the team:\n{}".format(self.peers_list))
        self.scrambling_list = self.scramble(self.peers_list)
        self.logger.info("Scrambling List:\n{}".format(self.scrambling_list))

    def scramble(self, peers_list):
        peer_list_random = sample(peers_list, len(peers_list))
        return OrderedDict(zip(peers_list, peer_list_random))

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.clean_flows(datapath)
        # install the table-miss flow entry. (OF 1.3+)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def clean_flows(self, dp):
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        match = parser.OFPMatch()
        # Delete all flows
        instructions = []
        flow_mod = parser.OFPFlowMod(
            dp, 0, 0, 0,
            ofp.OFPFC_DELETE, 0, 0,
            1, ofp.OFPCML_NO_BUFFER,
            ofp.OFPP_ANY, OFPG_ANY, 0,
            match, instructions)
        dp.send_msg(flow_mod)
        # Install the table-miss flow entry
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER,
                                          ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        pkt = packet.Packet(msg.data)
        in_port = msg.match['in_port']
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        udp_pkt = pkt.get_protocol(udp.udp)

        if udp_pkt:
            dst_peer = (ip_pkt.dst, udp_pkt.dst_port)

            if ip_pkt.src == self.splitter:
                if dst_peer == next(iter(self.scrambling_list)):
                    self.rounds_shuffle_counter += 1
                    if self.rounds_shuffle_counter \
                       == self.rounds_to_shuffle:
                        self.rounds_shuffle_counter = 0
                        self.clean_flows(dp)
                        self.scrambling_list = self.scramble(self.peers_list)
                        self.logger.info("Scrambling List Updated:\n{}"
                                         .format(self.scrambling_list))
                actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]

            elif dst_peer in self.scrambling_list:
                self.ip_to_mac[ip_pkt.src] = eth_pkt.src
                self.mac_to_port[eth_pkt.src] = in_port

                myself = (ip_pkt.src, udp_pkt.dst_port)
                if self.scrambling_list[dst_peer] == myself:
                    dst_peer = myself

                if self.scrambling_list[dst_peer][0] in self.ip_to_mac:
                    dst_ip = self.scrambling_list[dst_peer][0]
                    dst_mac = self.ip_to_mac[dst_ip]
                    dst_port = self.mac_to_port[dst_mac]
                else:
                    dst_ip = self.scrambling_list[dst_peer][0]
                    dst_mac = 'ff:ff:ff:ff:ff:ff'
                    dst_port = ofp.OFPP_FLOOD

                match = dp.ofproto_parser.OFPMatch(
                    in_port=in_port, eth_type=0x800, ipv4_dst=dst_peer[0])
                # 0x800 => IPv4 type.
                # See more in https://en.wikipedia.org/wiki/EtherType
                actions = []
                actions.append(ofp_parser.OFPActionSetField(eth_dst=dst_mac))
                actions.append(ofp_parser.OFPActionSetField(ipv4_dst=dst_ip))
                actions.append(ofp_parser.OFPActionOutput(port=dst_port))
                if msg.buffer_id != ofp.OFP_NO_BUFFER:
                    self.add_flow(dp, 1, match, actions, msg.buffer_id)
                    return
                else:
                    self.add_flow(dp, 1, match, actions)
            else:
                actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]
        else:
            actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]
        out = ofp_parser.OFPPacketOut(
            datapath=dp, buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions, data=msg.data)
        dp.send_msg(out)
