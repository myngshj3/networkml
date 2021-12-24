# -*- coding:utf-8 -*-

import socket
import sys
import re
import enum
import queue
from networkml.generic import debug, is_debug_mode
from networkml.consensus import Consensus, ConsensusError, ConsensusReset, ConsensusConfused
from networkml.server import AutonomousWorker, ForceQuit


class SocketConnectionBrokenError(RuntimeError):

    def __init__(self, msg):
        super().__init__(msg)


class SyncClient:

    def __init__(self, name, manager, sock, hostname, port):
        self._name = name
        self._manager = manager
        self._sock = sock
        self._host = hostname
        self._port = port
        self._consensus = Consensus()
        self._queue = queue.Queue()

    def try_connect(self, host_port=None):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if host_port is None:
            self._sock.connect((self._host, self._port))
        else:
            self._sock.connect(host_port)
            self._host = host_port[0]
            self._port = host_port[1]
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.settimeout(30)

    def organize(self):
        if self._sock is None:
            self.try_connect()
            # self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self._sock.connect((self._host, self._port))
            # self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # self._sock.settimeout(30)

    def push_queue(self, item):
        self._queue.put(item)
        self.process_request()

    def pull_queue(self):
        item = self._queue.get()
        return item

    def send_msg(self, sock, msg):
        # self.debug(sock, len(msg), msg)
        totalsent = 0
        while totalsent < len(msg):
            sent = sock.send(msg[totalsent:])
            if sent == 0:
                raise SocketConnectionBrokenError("socket connection broken observed. zero byte sent.")
            totalsent = totalsent + sent

    def receive(self, sock, length, once=False):
        # self.debug(sock, length, once)
        if once:
            debug("began receiving.")
            chunk = sock.recv(length)
            debug("done.")
            if chunk == b'':
                raise SocketConnectionBrokenError("socket connection broken observed. b'' received.")
            debug("message receive completed. {} bytes read".format(len(chunk)))
            return chunk
        debug("began receiving.")
        chunks = []
        bytes_recd = 0
        while bytes_recd < length:
            chunk = sock.recv(min(length - bytes_recd, 2048))
            if chunk == b'':
                return chunk
            chunks.append(chunk)
            if len(chunk) == 0:
                break
            bytes_recd = bytes_recd + len(chunk)
            debug(bytes_recd, "has read.")
        debug("message receive completed. {} bytes read".format(bytes_recd))
        msg = b''.join(chunks)
        return msg

    def process_request(self):
        # try:
        item = self.pull_queue()
        if isinstance(item, ForceQuit):
            raise item
        sock = self._sock
        item = self._consensus.encode_sending_data(item, self._consensus.ConsensusKeywords.SendRequest)
        # begin request
        i = 1
        debug(i, "sending", self._consensus.ConsensusKeywords.BeginRequest.value)
        req = self._consensus.encode_sending_data(len(item), self._consensus.ConsensusKeywords.BeginRequest)
        self.send_msg(sock, req)
        debug("done")
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptBeginRequest.value)
        req = self.receive(sock, 128, once=True)
        debug("done")
        _ = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.AcceptBeginRequest)
        # send request
        i = i+1
        debug(i, "sending", self._consensus.ConsensusKeywords.SendRequest.value)
        self.send_msg(sock, item)
        debug("done")
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptSendRequest.value)
        req = self.receive(sock, 128, once=True)
        debug("done")
        _ = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.AcceptSendRequest)
        # end request
        i = i+1
        debug(i, "sending to", self._consensus.ConsensusKeywords.EndRequest.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.EndRequest)
        self.send_msg(sock, req)
        debug("done")
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptEndRequest.value)
        req = self.receive(sock, 128, once=True)
        debug("done")
        _ = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.AcceptEndRequest)

        # begin response
        i = i+1
        debug(i, "sending to", self._consensus.ConsensusKeywords.WaitResponse.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.WaitResponse)
        self.send_msg(sock, req)
        debug("done")
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.BeginResponse.value)
        res = self.receive(sock, 128, once=True)
        debug("done")
        length = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.BeginResponse)
        res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptBeginResponse)
        i = i+1
        debug(i, "sending", self._consensus.ConsensusKeywords.AcceptBeginResponse.value)
        self.send_msg(sock, res)
        debug("done")
        # receive response
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.SendResponse.value)
        res = self.receive(sock, length)
        debug("done")
        content = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.SendResponse)
        res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptSendResponse)
        i = i+1
        debug(i, "sending", self._consensus.ConsensusKeywords.AcceptSendResponse.value)
        self.send_msg(sock, res)
        debug("done")
        # end response
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.EndResponse.value)
        res = self.receive(sock, 128, once=True)
        debug("done")
        _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.EndResponse)
        i = i+1
        debug(i, "sending", self._consensus.ConsensusKeywords.AcceptEndResponse.value)
        res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptEndResponse)
        self.send_msg(sock, res)
        debug("done")

        # process response
        debug("Returned Content is", content)
        self.process_response(content)

    def process_response(self, res):
        debug(res)


class AutonomousClient(AutonomousWorker):

    def __init__(self, name, manager, sock, hostname, port):
        super().__init__(name, self, manager, sock=sock)
        self._hostname = hostname
        self._port = port
        self._queue = queue.Queue()

    def organize(self):
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self._hostname, self._port))
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.settimeout(30)
        super().organize()

    def push_queue(self, item):
        self.debug("pushing '{}'".format(item))
        self._queue.put(item)
        self.debug("done")

    def pull_queue(self):
        self.debug("pulling")
        item = self._queue.get()
        self.debug("done '{}'".format(item))
        return item

    def process_request(self):
        # try:
        item = self.pull_queue()
        if isinstance(item, ForceQuit):
            raise item
        sock = self.rw_sock
        item = self._consensus.encode_sending_data(item, self._consensus.ConsensusKeywords.SendRequest)
        # begin request
        i = 1
        self.debug(i, "sending", self._consensus.ConsensusKeywords.BeginRequest.value)
        req = self._consensus.encode_sending_data(len(item), self._consensus.ConsensusKeywords.BeginRequest)
        self.send_msg(sock, req)
        self.debug("done")
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptBeginRequest.value)
        req = self.receive(sock, 128, once=True)
        self.debug("done")
        _ = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.AcceptBeginRequest)
        # send request
        i = i+1
        self.debug(i, "sending", self._consensus.ConsensusKeywords.SendRequest.value)
        self.send_msg(sock, item)
        self.debug("done")
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptSendRequest.value)
        req = self.receive(sock, 128, once=True)
        self.debug("done")
        _ = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.AcceptSendRequest)
        # end request
        i = i+1
        self.debug(i, "sending to", self._consensus.ConsensusKeywords.EndRequest.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.EndRequest)
        self.send_msg(sock, req)
        self.debug("done")
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptEndRequest.value)
        req = self.receive(sock, 128, once=True)
        self.debug("done")
        _ = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.AcceptEndRequest)

        # begin response
        i = i+1
        self.debug(i, "sending to", self._consensus.ConsensusKeywords.WaitResponse.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.WaitResponse)
        self.send_msg(sock, req)
        self.debug("done")
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.BeginResponse.value)
        res = self.receive(sock, 128, once=True)
        self.debug("done")
        length = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.BeginResponse)
        res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptBeginResponse)
        i = i+1
        self.debug(i, "sending", self._consensus.ConsensusKeywords.AcceptBeginResponse.value)
        self.send_msg(sock, res)
        self.debug("done")
        # receive response
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.SendResponse.value)
        res = self.receive(sock, length)
        self.debug("done")
        content = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.SendResponse)
        res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptSendResponse)
        i = i+1
        self.debug(i, "sending", self._consensus.ConsensusKeywords.AcceptSendResponse.value)
        self.send_msg(sock, res)
        self.debug("done")
        # end response
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.EndResponse.value)
        res = self.receive(sock, 128, once=True)
        self.debug("done")
        _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.EndResponse)
        i = i+1
        self.debug(i, "sending", self._consensus.ConsensusKeywords.AcceptEndResponse.value)
        res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptEndResponse)
        self.send_msg(sock, res)
        self.debug("done")

        # process response
        self.debug("Returned Content is", content)
        self.process_response(content)

        # except ConsensusReset as ex:
        #     print(ex)
        #     ack = self._consensus.encode_sending_data("your reset request was accepted.",
        #                                               self._consensus.ConsensusKeywords.Ack)
        #     self.send_msg(self._sock, ack)
        #     print("Reset request from server has properly proceeded.")
        #     return ex
        # except ConsensusError as ex:
        #     print("confusion brought by", ex)
        #     confused = self._consensus.encode_sending_data("got confused.",
        #                                                    self._consensus.ConsensusKeywords.Confused)
        #     self.send_msg(self._sock, confused)
        #     return ex
        # except socket.timeout as ex:
        #     print(ex)
        #     return ex
        # except SocketConnectionBrokenError as ex:
        #     print(ex)
        #     return ex  # self._consensus.ConsensusKeywords.ConnectionBroken
        # except Exception as ex:
        #     print(ex)
        #     return ex  # self._consensus.ConsensusKeywords.Error

    def process_response(self, res):
        self.debug(res)

