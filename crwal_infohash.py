#!/usr/bin/env python
# encoding: utf-8

import os
import time
import socket
import codecs
from struct import unpack
from socket import inet_ntoa
from threading import Thread
from collections import deque

# pip install bencode.py
from bencode import bencode, bdecode


def get_rand_id(length=20):
    """
    生成随机的节点id, 默认长度20
    """
    return os.urandom(length)


def get_neighbor(target, nid, end=10):
    """
    随机生成target周边节点id
    在Kademlia网络中, 距离是通过异或(XOR)计算的
    """
    return target[:end] + nid[end:]

def get_nodes_info(nodes):
    """
    解析node节点的信息
    每个节点单位长度为26 [node_id(20位)+node_ip(4位)+node_port(2位)]
    """
    ret = []
    nlen = len(nodes)
    if (nlen % 26) != 0:
        return ret
    for i in range(0, nlen, 26):
        nid = nodes[i:i + 20]
        ip = inet_ntoa(nodes[i + 20:i + 24])
        # 解包返回节点端口
        port = unpack("!H", nodes[i + 24:i + 26])[0]
        ret.append((nid, ip, port))
    return ret


class DHTNode(object):
    """
    DHT 网络节点
    """
    def __init__(self, nid, ip, port):
        self.nid = nid
        self.ip = ip
        self.port = port


class DHTServer(object):
    """
    DHT Server
    """
    def __init__(self, bind_ip, bind_port, process_id=0, bootstrap_nodes=[], node_length=5000):
        """
        初始化
        """
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.process_id = process_id
        self.nid = get_rand_id()
        self.recall_frq_nodes = {}
        # bootstrap nodes
        self.bootstrap_nodes = [
            ("router.bittorrent.com", 6881),
            ("dht.transmissionbt.com", 6881),
            ("router.utorrent.com", 6881)
        ] + bootstrap_nodes
        # 双端队列
        self.nodes = deque(maxlen=node_length)
        # KRPC 协议是由 bencode 编码组成的一个简单的 RPC 结构，使用 UDP 报文发送
        self.udp_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # UDP 地址绑定
        self.udp_fd.bind((self.bind_ip, self.bind_port))


    def send_krpc(self, msg, address): 
        """
        发送krpc协议
        rpc消息规范: http://www.bittorrent.org/beps/bep_0005.html
        """
        try:
            self.udp_fd.sendto(bencode(msg), address)
        except Exception as e:
            pass


    def send_error(self, tid, address):
        """
        发送错误回复
        """
        self.send_krpc({
            't': tid,
            'v': 'e',
            'e': [
                202,
                'Server Error'
            ]
        }, address)


    def send_find_node(self, address, nid=None): 
        """
        发出查找节点的请求
        """
        nid = get_neighbor(nid, self.nid) if nid else self.nid
        self.send_krpc({
            "t": get_rand_id(),
            "y": "q",
            "q": "find_node",
            "a": {
                "id": nid,
                "target": get_rand_id()
            }
        }, address)


    def join_DHT(self):
        """
        加入DHT网络
        """
        for node in self.bootstrap_nodes:
            self.send_find_node(node)


    def on_find_node_response(self, msg):
        """
        解码nodes节点信息 并存储队列
        """
        # 查找邻居节点
        # [
        #     (b'AyS\x04\xac\xf93\x15}\x98?3x\xc6dL\x94\xda\xcb\xc7', '203.254.74.93', 15712), 
        #     (b'&4q\x9c$V\x02>\xe7\x99\xeb\xd2A\xc6\xf6\xe1Os\xb5\x85', '177.193.253.142', 30761), 
        #     (b'&4q\x9c$V\x02>\xe7\x99\xeb\xd2B{S\xc8\x96<\xdb\x8e', '99.245.111.158', 41653), 
        #     (b'&4q\x9c$V\x02>\xe7\x99\xeb\xd2C1\xeci\xb9\xe7\x94\x9e', '2.162.45.31', 23370), 
        #     (b'&4q\x9c$V\x02>\xe7\x99\xeb\xd2D:\xa4\xd6\x1a\xceO\xd3', '194.112.255.104', 34851), 
        #     (b'&4q\x9c$V\x02>\xe7\x99\xeb\xd2E\x9c\xa9\x82\xa7kf\n', '37.34.194.35', 13012), 
        #     (b'&4q\x9c$V\x02>\xe7\x99\xeb\xd2Fz\x01\x8f\xed\xd4\xc3-', '179.178.227.176', 25486), 
        #     (b'&4q\x9c$V\x02>\xe7\x99\xeb\xd2G\x13\xe5+\xde\x9c|\x8e', '184.38.168.161', 30835)
        # ]
        nodes = get_nodes_info(msg[b'r'][b'nodes'])
        for node in nodes:
            nid, ip, port = node
            if len(nid) != 20: continue
            if ip == self.bind_ip: continue
            if port < 1 or port > 65535: continue
            node_key = "{}:{}".format(ip, port)
            if node_key not in self.recall_frq_nodes:
                self.recall_frq_nodes[node_key] = 0
                self.nodes.append(DHTNode(nid, ip, port))
            else:
                if self.recall_frq_nodes[node_key] > 500:
                    del self.recall_frq_nodes[node_key]
                self.recall_frq_nodes[node_key] += 1


    def on_get_peers_request(self, msg, address):
        """
        get_peers与torrent文件的info_hash有关
        get_peers请求包含2个参数 
        第一个参数是id 包含了请求节点的ID
        第二个参数是info_hash 它代表torrent文件的info_hash
        """
        # OrderedDict([
        #     (b'a', OrderedDict([
        #         (b'id', b'\x0b\xb0\xde\x8b\xee~\x1e\xf0\x0c\xc2\xc4\x95\xd2\xdfE\x91\xc7\x82B\xe2'), 
        #         (b'info_hash', b'\x0b\xb0\xde\x8b\xee~\x1e\xf0\x0c\xc2\xc6\xb9;\xfc\xa4,\xa5\x973\xa2')
        #     ])), 
        #     (b'q', b'get_peers'), 
        #     (b't', b'0R'), 
        #     (b'v', b'LT\x01\x00'), 
        #     (b'y', b'q')
        # ])
        try:
            tid = msg[b't']
            nid = msg[b'a'][b'id']
            info_hash = msg[b'a'][b'info_hash']
            self.send_krpc({
                't': tid,
                'y': 'r',
                'r': {
                    'id': get_neighbor(nid, self.nid),
                    'nodes': '',
                    'token': info_hash[:2]
                }
            }, address)

            self.save_magent(info_hash)
        except KeyError:
            self.send_error(tid, address)


    def on_announce_peer_request(self, msg, address):
        """
        announce_peer表明请求的节点正在某个端口下载torrent文件
        announce_peer包含4个参数
        第一个参数是id 包含了请求节点的ID
        第二个参数是info_hash 包含了torrent文件的info_hash
        第三个参数是port 表明peer在哪个端口下载
        第四个参数是token 是在之前的get_peers请求中收到的回复中包含
        开发者可自行完善这部分内容
        """
        try:
            tid = msg[b't']
            nid = msg[b'a'][b'id']
            token = msg[b'a'][b'token']
            info_hash = msg[b'a'][b'info_hash']
            port = msg[b'a'][b'port'] if 'implied_port' not in msg[b'a'] or msg[b'a'][b'implied_port'] == 0 else address[1] 
            if info_hash[:2] != token or port < 1 or port > 65535:
                return
            self.send_krpc({
                't': tid,
                'y': 'r',
                'r': {
                    'id': get_neighbor(nid, self.nid),
                }
            }, address)

            self.save_magent(info_hash)
        except KeyError:
            self.send_error(tid, address)


    def on_message(self, msg, address):
        """
        负责返回信息的处理
        """
        try:
            if msg[b'y'] == b'r':
                # 响应消息
                if msg[b'r'][b'nodes']:
                    self.on_find_node_response(msg)
            elif msg[b'y'] == b'q':
                # 请求消息
                if msg[b'q'] == b'get_peers':
                    self.on_get_peers_request(msg, address)
                elif msg[b'q'] == b'announce_peer':
                    self.on_announce_peer_request(msg, address)
                else:
                    pass
            else:
                pass
        except KeyError:
            pass


    def receive_response(self, blen=65536):
        """
        接收udp数据
        """
        try:
            # 接受返回报文
            data, address = self.udp_fd.recvfrom(blen)
            # 使用 bdecode 解码返回数据
            msg = bdecode(data)
            # 处理返回信息
            self.on_message(msg, address)
        except Exception as e:
            pass


    def run_traverse_forever(self):
        """
        消费队列数据
        """
        while True:
            try:
                # 如果队列为空, 会抛出异常
                node = self.nodes.popleft()
                self.send_find_node((node.ip, node.port), node.nid)
                time.sleep(1e-5)
            except IndexError:
                self.join_DHT()
                pass


    def run_receive_forever(self):
        """
        线程入口
        """
        while True:
            self.receive_response()
            time.sleep(1e-5)


    def save_magent(self, info_hash):
        """
        保存magent
        使用 codecs 解码 info_hash
        """
        # b'0y\xf0\xc2\xd6>C\x10P\x14X\x90\xa9\xd1\xa8fM\xbdAS'
        magnet = "magnet:?xt=urn:btih:{}".format(codecs.getencoder('hex')(info_hash)[0].decode())
        print (magnet)
        pass


if __name__ == "__main__":
    dht = DHTServer('0.0.0.0', 9090)
    threads = [
        Thread(target=dht.run_traverse_forever),
        Thread(target=dht.run_receive_forever),
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()
