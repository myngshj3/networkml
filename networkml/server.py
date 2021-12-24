# -*- coding:utf-8 -*-

import socket
import pickle
import threading
import sys
import queue
import re
import enum
from networkml.generic import debug, is_debug_mode
from networkml.consensus import Consensus, ConsensusError, ConsensusConfused, ConsensusReset


class ForceQuit(Exception):

    def __init__(self, msg):
        super().__init__(msg)


class ControlNotify(Exception):

    def __init__(self, msg, desc):
        super().__init__(msg)
        self._desc = desc

    @property
    def desc(self):
        return self._desc


class PreConsensusTroubleNotify(ControlNotify):

    def __init__(self, msg, desc):
        super().__init__(msg, desc)


class QuitNotify(ControlNotify):

    def __init__(self, msg, desc):
        super().__init__(msg, desc)


class ResetNotify(ControlNotify):

    def __init__(self, msg, desc):
        super().__init__(msg, desc)


class ReaderResetNotify(ControlNotify):

    def __init__(self, msg, desc):
        super().__init__(msg, desc)


class WriterResetNotify(ControlNotify):

    def __init__(self, msg, desc):
        super().__init__(msg, desc)


class ConsensusBuildNotify(ControlNotify):

    def __init__(self, msg, desc):
        super().__init__(msg, desc)


class AlgorithmUpdateNotify(ControlNotify):

    def __init__(self, msg, desc):
        super().__init__(msg, desc)


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
        self._consensus_err_breaks = ()
        self._consensus_err_ignores = ()

    def get_method(self, caller, sig):
        return self._obj.get_method(caller, sig)

    def organize(self):
        debug("Organizing...")
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
        breaks = ((SocketConnectionBrokenError(""), "break"), (ForceQuit(""), None))
        deals = (
            (ConsensusReset(""), self._consensus.ConsensusKeywords.AcceptReset, "your reset request was accepted."),
            (ConsensusConfused(""), self._consensus.ConsensusKeywords.AcceptConfused, "your confusion observed."),
            (ConsensusError(""), self._consensus.ConsensusKeywords.Reset, "protocol procedure is illegal."),
            (socket.timeout(), self._consensus.ConsensusKeywords.Reset, "your request time out. reset your procedure."))
        quits = ()
        ignores = ((Exception(""), None),)
        self.set_consensus_err_handlers(quits, deals, breaks, ignores)

    @property
    def consensus_err_quits(self):
        return self._consensus_err_quits

    @property
    def consensus_err_deals(self):
        return self._consensus_err_deals

    @property
    def consensus_err_breaks(self):
        return self._consensus_err_breaks

    @property
    def consensus_err_ignores(self):
        return self._consensus_err_ignores

    def set_consensus_err_handlers(self, quits=(), deals=(), breaks=(), ignores=()):
        if quits is not None:
            self._consensus_err_quits = quits
        if deals is not None:
            self._consensus_err_deals = deals
        if breaks is not None:
            self._consensus_err_breaks = breaks
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

    def set_debug(self, flag):
        self._debug = flag

    def debug(self, *args):
        if self._debug:
            msg = args[0]
            for a in args[1:]:
                msg = "{} {}".format(msg, a)
            print(msg)

    def pre_process_request(self):
        pass

    def post_process_request(self):
        pass

    def process_request(self):
        self.pre_process_request()
        sock = self.rw_sock
        i = 1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.BeginRequest.value)
        req = self.receive(sock, 128, once=True)
        debug("done")
        length = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.BeginRequest)
        i = i+1
        debug(i, "sending", self._consensus.ConsensusKeywords.AcceptBeginRequest.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptBeginRequest)
        self.send_msg(sock, req)
        debug("done")
        # receive request
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.SendRequest.value)
        req = self.receive(sock, length)
        debug("done")
        req_msg = self._consensus.decode_received_data(req, self._consensus.ConsensusKeywords.SendRequest)
        i = i+1
        debug(i, "sending ", self._consensus.ConsensusKeywords.AcceptSendRequest.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptSendRequest)
        self.send_msg(sock, req)
        debug("done")
        # end request
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.EndRequest.value)
        req = self.receive(sock, 128, once=True)
        debug("done")
        _ = self._consensus.encode_sending_data(req, self._consensus.ConsensusKeywords.EndRequest)
        i = i+1
        debug(i, "sending", self._consensus.ConsensusKeywords.AcceptEndRequest.value)
        req = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.AcceptEndRequest)
        self.send_msg(sock, req)

        # process request
        try:
            interpreter = self._obj.get_method(self._obj, "interpret")
            if interpreter is None:
                res_msg = "NG, {} has no interpreter.".format(self._name)
            else:
                # res_msg = interpreter(self._obj, [req_msg])
                interpreter(self._obj, [req_msg])
                res_msg = self._obj.flush_print_buf()
        except Exception as ex:
            res_msg = "NG,{}".format(ex)

        # begin response
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.WaitResponse.value)
        res = self.receive(sock, 128, once=True)
        _ = self._consensus.encode_sending_data(res, self._consensus.ConsensusKeywords.WaitResponse)
        debug("done")
        i = i+1
        res_msg = self._consensus.encode_sending_data(res_msg, self._consensus.ConsensusKeywords.SendResponse)
        res = self._consensus.encode_sending_data(len(res_msg), self._consensus.ConsensusKeywords.BeginResponse)
        debug(i, "sending", "with", len(res_msg), res_msg, self._consensus.ConsensusKeywords.BeginResponse.value)
        self.send_msg(sock, res)
        # sock.send(res)
        debug("done")
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptBeginResponse.value)
        res = self.receive(sock, 128, once=True)
        debug("done")
        _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.AcceptBeginResponse)
        # send response. content is already encoded preliminarily.
        i = i+1
        debug(i, "sending", self._consensus.ConsensusKeywords.SendResponse.value)
        self.send_msg(sock, res_msg)
        debug("done")
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptSendResponse.value)
        res = self.receive(sock, 128, once=True)
        debug("done")
        _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.AcceptSendResponse)
        # end response
        i = i+1
        debug(i, "sending", self._consensus.ConsensusKeywords.EndResponse.value)
        res = self._consensus.encode_sending_data("", self._consensus.ConsensusKeywords.EndResponse)
        self.send_msg(sock, res)
        debug("done")
        i = i+1
        debug(i, "waiting for", self._consensus.ConsensusKeywords.AcceptEndResponse.value)
        res = self.receive(sock, 128, once=True)
        debug("done")
        _ = self._consensus.decode_received_data(res, self._consensus.ConsensusKeywords.AcceptEndResponse)

        rtn = self.post_process_request()
        # process response
        debug("Request successfully proceeded with '{}'".format(rtn))
        return rtn

    def process_request_loop(self):
        while not self._quit:
            try:

                rtn = self.process_request()
                # analyzes purpose of Exception return not raise.
                debug("returned type", type(rtn))
                if isinstance(rtn, Exception):
                    debug("analyzing exception")
                    for r in self._consensus_err_breaks:
                        debug(r)
                        if isinstance(rtn, type(r[0])):
                            if r[1] == "return":
                                return rtn
                            elif r[1] == "raise":
                                raise rtn
                            else:
                                debug("Breaking reason:", rtn)
                                break

            except Exception as ex:
                breaking = False
                continuing = False
                for r in self._consensus_err_breaks:
                    debug(r)
                    if isinstance(ex, type(r[0])):
                        if r[1] == "return":
                            return ex
                        elif r[1] == "raise":
                            raise ex
                        else:
                            breaking = True
                            debug("Breaking reason:", ex)
                            break
                if breaking:
                    break
                if continuing:
                    continue
                exit("Unexpected reach")
                for q in self._consensus_err_quits:
                    if isinstance(ex, type(q[0])):
                        debug("quit,", ex)
                        self._quit = True
                        repeat = True
                        if q[1] == "raise":
                            raise ex
                        elif q[1] == "break":
                            breaking = True
                            break
                        else:
                            continuing = True
                            break
                if breaking:
                    break
                if continuing:
                    continue
                for deal in self._consensus_err_deals:
                    if isinstance(ex, type(deal[0])):
                        debug("deals,", ex)
                        ack = self._consensus.encode_sending_data(deal[2], deal[1])
                        self.send_msg(self.rw_sock, ack)
                        continuing = True
                        break
                if breaking:
                    break
                if continuing:
                    continue
                for ignore in self._consensus_err_ignores:
                    if isinstance(ex, type(ignore[0])):
                        debug("ignored,", ex)
                        # ignore
                        continuing = True
                        break
                if breaking:
                    break
                if continuing:
                    continue
                debug(ex)
                continue

        # requests release of self
        if self._manager is not None:
            self._manager.finished(self)


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
        self._forked = None

    def organize(self):
        super().organize()
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

    class TopLevelLoop(Exception):

        def __init__(self, msg):
            super().__init__(msg)

    def set_init_exception_handlers(self):
        breaks = ((self.TopLevelLoop("return to toplevel loop"), "return"),
                  (SocketConnectionBrokenError("connection reset and return to toplevel."), "return"))
        deals = (
            (ConsensusConfused(), self._consensus.ConsensusKeywords.AcceptConfused, "your confutsion observed."),
            (ConsensusError("protocol procedure is illegal."), self._consensus.ConsensusKeywords.Reset, "protocol procedure is illegal."),
            (socket.timeout(), self._consensus.ConsensusKeywords.Reset, "your request time out. reset your procedure."))
        quits = ((ForceQuit("force quit"), None),)
        ignores = (
            (ConsensusReset("reset"), "your reset request was accepted."),
            (Exception(""), None),)
        self.set_consensus_err_handlers(quits, deals, breaks, ignores)

    def accept_connection(self):
        if self.client_sock is None:
            debug("waiting for client connection.")
            sock, address = self._sock.accept()
            debug(f"Connection from {address} has been established!")
            self._client = sock
            self._client_address = address

    @property
    def client(self):
        return self._client

    @property
    def client_sock(self):
        return self._client

    @property
    def client_address(self):
        return self._client_address

    def reset_client(self):
        self._client = None
        self._client_address = None

    def info(self):
        return self._hostname, self._port, self._listens

    def fork(self, worker_name, worker):
        debug("forking...", worker_name, ":", worker)
        worker = AutonomousWorker(worker_name, worker, self, self.client_sock)
        self._workers[worker_name] = worker
        self._forked = worker
        debug("forked", worker_name, ":", worker)

    def release(self, worker):
        a = None
        for a in self._workers.keys():
            if self._workers[a] == worker:
                break
        if a is not None:
            self._workers.pop(a)
            worker.finalize()

    def finished(self, worker):
        self.release(worker)

    def pre_process_request(self):
        if self.client_sock is None:
            debug("Bug!!! unexpeced reachability to here.")
            t = input("$ what do you do? abort? or continue? ")
            if t == "abort":
                raise ForceQuit("Unreachable state")
            else:
                self.accept_connection()

    def post_process_request(self):
        debug("**** post_process_request entered.")
        if self._forked is not None:
            debug("**** activating forked thread.")
            self.reset_client()
            self._forked.start()
            self._forked = None
            return self.TopLevelLoop("for accepting new client access.")

    def process_request_loop(self):
        while not self._quit:
            try:

                self.accept_connection()

                debug("begin request process loop")
                rtn = super().process_request_loop()
                debug("done")
                if isinstance(rtn, Exception):
                    if isinstance(rtn, self.TopLevelLoop):
                        debug(rtn)
                        self.reset_client()
                        continue
                    elif isinstance(rtn, SocketConnectionBrokenError):
                        debug(rtn)
                        self.reset_client()
                        continue
                    else:
                        debug("Unexpected exception", rtn)
                        raise rtn

            except self.TopLevelLoop as ex:
                debug("Reason why?", ex)
                continue
            except SocketConnectionBrokenError as ex:
                self.reset_client()
                continue
            except ForceQuit as ex:
                if self._quit:
                    debug(ex)
                else:
                    raise ex
            except Exception as ex:
                debug(ex)
        self._manager.finished(self)


class ServerHandler(WorkerDispacher):

    def __init__(self):
        super().__init__("NetworkML Server Test", self, self, "localhost", 1234)

    def release(self, worker):
        # managing noting due to test.
        pass

    def interpret(self, msg):
        debug("interpreting:", msg)
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
