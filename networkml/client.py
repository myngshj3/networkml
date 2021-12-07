# -*- coding:utf-8 -*-

import socket
import sys
import re
import enum
import queue
from networkml.consensus import Consensus, ConsensusError, ConsensusReset, ConsensusConfused
from networkml.server import AutonomousWorker, ForceQuit


class SocketConnectionBrokenError(RuntimeError):

    def __init__(self, msg):
        super().__init__(msg)


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
        print("pushing '{}'".format(item))
        self._queue.put(item)
        print("done")

    def pull_queue(self):
        print("pulling")
        item = self._queue.get()
        print("done '{}'".format(item))
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
        self.debug(i, "sending to", sock, self._consensus.ConsensusKeywords.EndRequest.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.EndRequest)
        self.send_msg(sock, req)
        self.debug("done")
        i = i+1
        self.debug(i, "waiting for", sock, self._consensus.ConsensusKeywords.AcceptEndRequest.value)
        req = self.receive(sock, 128, once=True)
        self.debug("done")
        _ = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.AcceptEndRequest)

        # begin response
        i = i+1
        self.debug(i, "waiting for", sock, self._consensus.ConsensusKeywords.BeginResponse.value)
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
        print("Returned Content is", content)
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
        print(res)


# class SimpleClient(socket.socket):
#
#     class ConsensusKeywords(enum.Enum):
#
#         OK = "OK"
#         NG = "NG"
#         Timeout = "Timeout"
#         Error = "Error"
#         ConnectionBroken = "ConnectionBroken"
#
#     MSGLEN = 8192
#
#     def __init__(self, owner, sock=None):
#         super().__init__(socket.AF_INET, socket.SOCK_STREAM)
#         self._owner = owner
#         self._consensus = Consensus()
#         self._debug = True
#
#     def organize(self):
#         self.connect(("localhost", 1234))
#         self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.settimeout(60)
#
#     def send_msg(self, msg):
#         totalsent = 0
#         while totalsent < len(msg):
#             sent = self.send(msg[totalsent:])
#             if sent == 0:
#                 raise SocketConnectionBrokenError("socket connection broken observed. zero byte sent.")
#             totalsent = totalsent + sent
#
#     def receive(self, length, once=False):
#         if once:
#             chunk = self.recv(length)
#             if chunk == b'':
#                 raise SocketConnectionBrokenError("socket connection broken observed. b'' received.")
#             return chunk
#         chunks = []
#         bytes_recd = 0
#         while bytes_recd < length:
#             chunk = self.recv(min(self.MSGLEN - bytes_recd, 2048))
#             if chunk == b'':
#                 raise SocketConnectionBrokenError("socket connection broken observed. b'' received.")
#             chunks.append(chunk)
#             if len(chunk) == 0:
#                 break
#             bytes_recd = bytes_recd + len(chunk)
#         return b''.join(chunks)
#
#     def analyze_response(self, res):
#         data = res.decode("utf-8")
#         return True
#
#     def set_debug(self, flag):
#         self._debug = flag
#
#     def debug(self, *args):
#         if self._debug:
#             msg = args[0]
#             for a in args[1:]:
#                 msg = "{} {}".format(msg, a)
#             print(msg)
#
#     def process_request(self, script):
#         try:
#             req = self._consensus.encode_sending_data(script, self._consensus.ConsensusKeywords.SendRequest)
#             # begin request
#             i = 1
#             self.debug(i, "sending ", self._consensus.ConsensusKeywords.BeginRequest.value)
#             msg = self._consensus.encode_sending_data(len(req), self._consensus.ConsensusKeywords.BeginRequest)
#             self.send_msg(msg)
#             self.debug("done")
#             i = i+1
#             self.debug(i, "waiting for ", self._consensus.ConsensusKeywords.Ack.value)
#             res = self.receive(128, once=True)
#             self.debug("done")
#             _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.Ack)
#             # send request
#             i = i+1
#             self.debug(i, "sending ", self._consensus.ConsensusKeywords.SendRequest.value)
#             self.send_msg(req)
#             self.debug("done")
#             i = i+1
#             self.debug(i, "waiting for ", self._consensus.ConsensusKeywords.Ack.value)
#             res = self.receive(128, once=True)
#             self.debug("done")
#             _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.Ack)
#             # end request
#             i = i+1
#             self.debug(i, "sending ", self._consensus.ConsensusKeywords.EndRequest.value)
#             msg = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.EndRequest)
#             self.send_msg(msg)
#             self.debug("done")
#             i = i+1
#             self.debug(i, "waiting for ", self._consensus.ConsensusKeywords.Ack.value)
#             res = self.receive(128, once=True)
#             self.debug("done")
#             _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.Ack)
#
#             # begin response
#             i = i+1
#             self.debug(i, "waiting for", self._consensus.ConsensusKeywords.BeginResponse.value)
#             res = self.receive(128, once=True)
#             self.debug("done")
#             length = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.BeginResponse)
#             res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.Ack)
#             i = i+1
#             self.debug(i, "sending", self._consensus.ConsensusKeywords.Ack.value)
#             self.send_msg(res)
#             self.debug("done")
#             # receive response
#             i = i+1
#             self.debug(i, "waiting for", self._consensus.ConsensusKeywords.SendResponse.value)
#             res = self.receive(length)
#             self.debug("done")
#             context = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.SendResponse)
#             res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.Ack)
#             i = i+1
#             self.debug(i, "sending", self._consensus.ConsensusKeywords.Ack.value)
#             self.send_msg(res)
#             self.debug("done")
#             # end response
#             i = i+1
#             self.debug(i, "waiting for", self._consensus.ConsensusKeywords.EndResponse.value)
#             res = self.receive(128, once=True)
#             self.debug("done")
#             _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.EndResponse)
#             i = i+1
#             self.debug(i, "sending", self._consensus.ConsensusKeywords.Ack.value)
#             res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.Ack)
#             self.send_msg(res)
#             self.debug("done")
#
#             # process response
#             print("Returned Content is", context)
#             return True
#
#         except ConsensusReset as ex:
#             print(ex)
#             ack = self._consensus.encode_sending_data("your reset request was accepted.",
#                                                       self._consensus.ConsensusKeywords.Ack)
#             self.send(ack)
#             print("Reset request from server has properly proceeded.")
#             return True
#         except ConsensusError as ex:
#             print("confusion brought by", ex)
#             confused = self._consensus.encode_sending_data("got confused.",
#                                                            self._consensus.ConsensusKeywords.Confused)
#             self.send(confused)
#             return True
#         except socket.timeout as ex:
#             print(ex)
#             return True
#         except SocketConnectionBrokenError as ex:
#             print(ex)
#             return self.ConsensusKeywords.ConnectionBroken
#         except Exception as ex:
#             print(ex)
#             return self.ConsensusKeywords.Error
#
#     def main_loop(self):
#         q = False
#         opt_pat = r"^\s*((?P<quit>(quit|exit))|debug\s*=\s*(?P<debug>(on|off))|)\s*$"
#         while not q:
#             script = input("$client ")
#             m = re.match(opt_pat, script)
#             if m is None:
#                 rtn = self.process_request(script)
#                 if type(rtn) is bool:
#                     print("Success ? ", rtn)
#                 else:
#                     print("Error:", rtn)
#                     q = True
#             else:
#                 g = m.groupdict()
#                 if g['quit'] is not None:
#                     q = True
#                 elif g['debug'] is not None:
#                     if g['debug'] == "on":
#                         self.set_debug(True)
#                     else:
#                         self.set_debug(False)
#                 else:
#                     continue
#         pass
#
#     def main(self, args):
#         self.main_loop()
#
#
# if __name__ == "__main__":
#     client = AutoClient(None)
#     client.organize()
#     client.main(sys.argv)

