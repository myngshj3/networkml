# -*- coding:utf-8 -*-

import socket
import pickle
import threading
import sys
import queue
import re
import enum
from networkml.consensus import Consensus, ConsensusError, ConsensusConfused, ConsensusReset


class ForceQuit(Exception):

    def __init__(self, msg):
        super().__init__(msg)


class SocketConnectionBrokenError(RuntimeError):

    def __init__(self, msg):
        super().__init__(msg)


class UnexpectedResponseError(Exception):

    def __init__(self, msg):
        super().__init__(msg)


class UnexpectedResponseInPreConsensusError(UnexpectedResponseError):

    def __init__(self, msg):
        super().__init__(msg)


class AutonomousWorker(threading.Thread):

    def __init__(self, name, obj, manager, sock):
        super().__init__(target=self.process_request_loop)
        self._name = name
        self._obj = obj
        self._manager = manager
        self._sock = sock
        self._consensus = Consensus()
        self._quit = False
        self._debug = True
        self._consensus_err_quits = ()
        self._consensus_err_deals = ()
        self._consensus_err_ignores = ()

    def organize(self):
        self.set_init_exception_handlers()

    def finalize(self):
        # FIXME deal with untreated messages.
        self._quit = True
        if self._sock is not None:  # dialogue with client.
            self._sock.close()

    @property
    def rw_sock(self):
        return self._sock

    def set_init_exception_handlers(self):
        deals = (
            (ConsensusReset, self._consensus.ConsensusKeywords.AcceptReset, "your reset request was accepted."),
            (ConsensusConfused, self._consensus.ConsensusKeywords.AcceptConfused, "your confusion observed."),
            (ConsensusError, self._consensus.ConsensusKeywords.Reset, "protocol procedure is illegal."),
            (socket.timeout, self._consensus.ConsensusKeywords.Reset, "your request time out. reset your procedure."))
        quits = (
            (ForceQuit, None),
            (SocketConnectionBrokenError, None))
        ignores = ((Exception, None),)
        self.set_consensus_err_handlers(quits, deals, ignores)

    @property
    def consensus_err_quits(self):
        return self._consensus_err_quits

    @property
    def consensus_err_deals(self):
        return self._consensus_err_deals

    @property
    def consensus_err_ignores(self):
        return self._consensus_err_ignores

    def set_consensus_err_handlers(self, quits=(), deals=(), ignores=()):
        if quits is not None:
            self._consensus_err_quits = quits
        if deals is not None:
            self._consensus_err_deals = deals
        if ignores is not None:
            self._consensus_err_ignores = ignores

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
            self.debug("began receiving.")
            chunk = sock.recv(length)
            self.debug("done.")
            if chunk == b'':
                raise SocketConnectionBrokenError("socket connection broken observed. b'' received.")
            self.debug("message receive completed. {} bytes read".format(len(chunk)))
            return chunk
        self.debug("began receiving.")
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
            self.debug(bytes_recd, "has read.")
        self.debug("message receive completed. {} bytes read".format(bytes_recd))
        msg = b''.join(chunks)
        return msg

    def set_debug(self, flag):
        self._debug = flag

    def debug(self, *args):
        if self._debug:
            msg = args[0]
            for a in args[1:]:
                msg = "{} {}".format(msg, a)
            print(msg)

    def process_request(self):
        sock = self.rw_sock
        # if self.is_post_reset:  # wait for Ack, if just after Reset.
        #     self.debug(0, "waiting for", self._consensus.ConsensusKeywords.Ack.value)
        #     res = self.receive(sock, 128, once=True)
        #     self.debug("done")
        #     _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.Ack)
        #     self._is_post_reset = False
        # waiting for ack for reset
        i = 1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.BeginRequest.value)
        req = self.receive(sock, 128, once=True)
        self.debug("done")
        length = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.BeginRequest)
        i = i+1
        self.debug(i, "sending", self._consensus.ConsensusKeywords.AcceptBeginRequest.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptBeginRequest)
        self.send_msg(sock, req)
        self.debug("done")
        # receive request
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.SendRequest.value)
        req = self.receive(sock, length)
        self.debug("done")
        req_msg = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.SendRequest)
        i = i+1
        self.debug(i, "sending ", self._consensus.ConsensusKeywords.AcceptSendRequest.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptSendRequest)
        self.send_msg(sock, req)
        self.debug("done")
        # end request
        i = i+1
        self.debug(i, "waiting for", sock, self._consensus.ConsensusKeywords.EndRequest.value)
        req = self.receive(sock, 128, once=True)
        self.debug("done")
        _ = self._consensus.encode_sending_data(req, self._consensus.ConsensusKeywords.EndRequest)
        i = i+1
        self.debug(i, "sending", sock, self._consensus.ConsensusKeywords.AcceptEndRequest.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptEndRequest)
        self.send_msg(sock, req)

        # process request
        res_msg = req_msg  # self._obj.interpret(msg)
        print(req_msg, res_msg)

        # begin response
        i = i+1
        res_msg = self._consensus.encode_sending_data(res_msg, self._consensus.ConsensusKeywords.SendResponse)
        res = self._consensus.encode_sending_data(len(res_msg), self._consensus.ConsensusKeywords.BeginResponse)
        self.debug(i, "sending", "with", len(res_msg), res_msg, self._consensus.ConsensusKeywords.BeginResponse.value)
        self.send_msg(sock, res)
        # sock.send(res)
        self.debug("done")
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptBeginResponse.value)
        res = self.receive(sock, 128, once=True)
        self.debug("done")
        _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.AcceptBeginResponse)
        # send response. content is already encoded preliminarily.
        i = i+1
        self.debug(i, "sending", self._consensus.ConsensusKeywords.SendResponse.value)
        self.send_msg(sock, res_msg)
        self.debug("done")
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptSendResponse.value)
        res = self.receive(sock, 128, once=True)
        self.debug("done")
        _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.AcceptSendResponse)
        # end response
        i = i+1
        self.debug(i, "sending", self._consensus.ConsensusKeywords.EndResponse.value)
        res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.EndResponse)
        self.send_msg(sock, res)
        self.debug("done")
        i = i+1
        self.debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptEndResponse.value)
        res = self.receive(sock, 128, once=True)
        self.debug("done")
        _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.AcceptEndResponse)

        # process response
        self.debug("Request successfully proceeded")

    def process_request_loop(self):
        while not self._quit:
            try:

                self.process_request()

            except Exception as ex:
                repeat = False
                for q in self._consensus_err_quits:
                    if isinstance(ex, q[0]):
                        print("quit,", ex)
                        self._quit = True
                        repeat = True
                        break
                if repeat:
                    continue
                for deal in self._consensus_err_deals:
                    if isinstance(ex, deal[0]):
                        print("deals,", ex, deal[1])
                        ack = self._consensus.encode_sending_data(deal[2], deal[1])
                        self.send_msg(self.rw_sock, ack)
                        repeat = True
                        break
                if repeat:
                    continue
                for ignore in self._consensus_err_ignores:
                    if isinstance(ex, ignore[0]):
                        print("ignored,", ex)
                        # ignore
                        repeat = True
                        break
                if repeat:
                    continue
                print(ex)
                continue

            # except ConsensusReset as ex:
            #     print(ex)
            #     ack = self._consensus.encode_sending_data("your reset request was accepted.",
            #                                               self._consensus.ConsensusKeywords.AcceptReset)
            #     self.send_msg(self.rw_sock, ack)
            #     print("Reset request was properly proceeded.")
            # except ConsensusConfused as ex:
            #     print("confusion observed.", ex)
            #     ack = self._consensus.encode_sending_data("your confutsion observed.",
            #                                               self._consensus.ConsensusKeywords.AcceptConfused)
            #     self.send_msg(self.rw_sock, ack)
            # except ConsensusError as ex:
            #     print("protocol procedural violation observed.", ex, "sending reset.")
            #     reset = self._consensus.encode_sending_data("your protocol procedure is illegal.",
            #                                                 self._consensus.ConsensusKeywords.Reset)
            #     self.send_msg(self.rw_sock, reset)
            # except socket.timeout as ex:
            #     print(ex)
            #     reset = self._consensus.encode_sending_data("your request process time out. reset your procedure.",
            #                                                 self._consensus.ConsensusKeywords.Reset)
            #     self.send_msg(self.rw_sock, reset)
            # except SocketConnectionBrokenError as ex:
            #     print(ex)
            #     self._quit = False
            # except ForceQuit as ex:
            #     self._quit = True
            #     raise ex
            # except Exception as ex:
            #     print(ex)
        # requests release of self
        if self._manager is not None:
            self._manager.release(self)


class DiplomacyWorker(AutonomousWorker):

    def __init__(self, name, obj, manager, sock):
        super().__init__(name, obj, manager, sock)


class WorkerDispacher(AutonomousWorker):

    class ConsensusKeywords(enum.Enum):

        OK = "OK"
        NG = "NG"
        Timeout = "Timeout"
        Error = "Error"
        ConnectionBroken = "ConnectionBroken"

    MSGLEN = 4096

    def __init__(self, name, obj, manager, hostname, port=1234, listens=5):
        super().__init__(name, obj, manager, sock=None)
        self._hostname = hostname
        self._port = port
        self._listens = listens
        self._consensus = Consensus()
        self._workers = {}
        self._client = None
        self._client_address = None

    def organize(self):
        # super().organize()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((self._hostname, self._port))
        self._sock.listen(self._listens)
        self._sock.settimeout(30)

    def finalize(self):
        # FIXME deal with untreated messages.
        super().finalize()
        if self.client is not None:  # dialogue with client.
            self.client.close()

    @property
    def rw_sock(self):
        return self._client

    def set_init_exception_handlers(self):
        deals = (
            (ConsensusConfused, self._consensus.ConsensusKeywords.AcceptConfused, "your confutsion observed."),
            (ConsensusError, self._consensus.ConsensusKeywords.Reset, "protocol procedure is illegal."),
            (socket.timeout, self._consensus.ConsensusKeywords.Reset, "your request time out. reset your procedure."))
        quits = (
            (ForceQuit, None),
            (SocketConnectionBrokenError, None))
        ignores = (
            (ConsensusReset, "your reset request was accepted."),
            (Exception, None),)
        self.set_consensus_err_handlers(quits, deals, ignores)

    def accept_connection(self):
        print("waiting for client connection.")
        sock, address = self._sock.accept()
        print(f"Connection from {address} has been established!")
        self._client = sock
        self._client_address = address

    @property
    def client(self):
        return self._client

    def reset_client(self):
        self._client = None
        self._client_address = None

    def info(self):
        return self._hostname, self._port, self._listens

    def fork(self, worker_name, worker):
        worker = AutonomousWorker(worker_name, worker, self, self.client)
        self._workers[worker_name] = worker
        worker.start()

    def release(self, worker):
        a = None
        for a in self._workers.keys():
            if self._workers[a] == worker:
                break
        if a is not None:
            self._workers.pop(a)
            worker.finalize()

    def process_request_loop(self):
        while not self._quit:
            try:

                self.accept_connection()

                super().process_request_loop()

            except ForceQuit as ex:
                if self._quit:
                    print(ex)
                else:
                    raise ex
            except Exception as ex:
                print(ex)


class ServerHandler(WorkerDispacher):

    def __init__(self):
        super().__init__("NetworkML Server Test", self, self, "localhost", 1234)

    def release(self, worker):
        # managing noting due to test.
        pass

    def interpret(self, msg):
        print("interpreting:", msg)
        return "OK on interpreting {}".format(msg)


def main_loop(server, args=()):
    q = False
    opt_pat = r"^\s*((?P<quit>(quit|exit))|)\s*$"
    while not q:
        script = input("$server ")
        m = re.match(opt_pat, script)
        if m is None:
            print("ignored:", script)
            continue
        else:
            g = m.groupdict()
            if g['quit'] is None:
                continue
            else:
                server.finalize()
                q = True


if __name__ == "__main__":
    server = ServerHandler()
    main_loop(server, sys.argv)
