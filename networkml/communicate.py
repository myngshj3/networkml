# -*- coding:utf-8 -*-

import socket
import pickle
import threading
import sys
import queue
import re
import traceback
import enum
from networkml.generic import debug, is_debug_mode
from networkml.consensus import Consensus, ConsensusError, ConsensusConfused, ConsensusReset
from networkml.server import AutonomousWorker
from networkml.server import ForceQuit, SocketConnectionBrokenError
from networkml.server import ControlNotify, QuitNotify, ResetNotify, ReaderResetNotify, WriterResetNotify
from networkml.server import ConsensusBuildNotify, AlgorithmUpdateNotify, PreConsensusTroubleNotify


class SimpleComunicator:

    def __init__(self, host, port, timeuot, listens, wait_start=False):
        self._consensus = Consensus()
        self._wait_start = wait_start
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._host = host
        self._port = port
        self._timeout = timeuot
        self._listens = listens
        self._bound = False
        self._i = 0
        self._j = 0

    @property
    def read_sock(self):
        if self._wait_start:
            return self._sock
        else:
            return None

    @property
    def write_sock(self):
        if self._wait_start:
            return None
        else:
            return self._sock

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

    def accept(self, sock):
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not self._bound:
            sock.bind((self._host, self._port))
            self._bound = True
        sock.listen(self._listens)
        sock.settimeout(self._timeout)
        _sock, _address = self._sock.accept()
        debug(f"Connection from {_address} has been established!")
        return _sock, _address

    def attach(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._host, self._port))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(self._timeout)
        return sock

    def encode_and_send(self, sock, data, keyword):
        msg = self._consensus.encode_sending_data(data, keyword)
        debug(self._i, "sending", keyword)
        msg = self._consensus.decode_received_data(msg, keyword)
        self.send_msg(sock, msg)
        debug("done")
        self._i = self._i + 1

    def receive_and_decode(self, sock, keyword, length, once=True):
        debug(self._j, "waiting for", keyword)
        req = self.receive(sock, length, once=once)
        req_msg = self._consensus.decode_received_data(req, keyword)
        debug("done")
        self._j = self._j + 1
        return req_msg


class BidirectionalCommunicator(SimpleComunicator):

    def __init__(self, host, port, timeout, listens, wait_start, req_queue, res_queue):
        super().__init__(host, port, timeout, listens, wait_start=wait_start)
        self._res_queue = res_queue
        self._req_queue = req_queue
        self._queue = queue.Queue()
        self._consensus = Consensus()
        self._reader_thread = None
        self._writer_thread = None
        self._read_sock = None
        self._read_address = None
        self._reader_running = False
        self._write_sock = None
        self._write_address = None
        self._writer_running = False

    def pre_conditional_consensus(self, consensus_config):
        config = {
            "quit": [ForceQuit],
            "read-reset": [ForceQuit],
        }
        pass

    def push_request(self, item):
        self._req_queue.put(item)

    def pull_response(self):
        item = self._res_queue.get()
        return item

    def finalize(self):
        # FIXME deal with untreated messages.
        if self._writer_running:
            self._req_queue.put(QuitNotify("finalize", "finish!"))
        if self._wait_start:
            if self._sock is not None:  # dialogue with client.
                self._sock.close()

    def try_handshake(self):
        if self._wait_start:
            step = 0
            try:
                print("*** HAND SHAKING ***")
                step = step + 1
                if self._sock is None:
                    print("Socket creating...")
                    self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                step = step + 1
                if self._write_sock is None:
                    print("Acceping connection for writing...")
                    self._write_sock, self._write_address = self.accept(self._sock)
                step = step + 1
                if self._writer_thread is None:
                    print("Starting writer thread...")
                    self._writer_thread = threading.Thread(target=self._send_reuest_loop)
                    self._writer_thread.start()
                step = step + 1
                if self._read_sock is None:
                    print("Acceping connection for reading...")
                    self._read_sock, self._read_address = self.accept(self._sock)
                step = step + 1
                if self._reader_thread is None:
                    print("Starting reader thread...")
                    self._reader_thread = threading.Thread(target=self._receive_reuest_loop)
                    self._reader_thread.start()
                step = step + 1
                print("Handshake done...")
                return True
            except Exception as ex:
                print(ex)
                desc = "when wait_start is {}, trouble occured between {} and {}.".format(self._wait_start, step, step+1)
                print(desc)
                self._res_queue.put(PreConsensusTroubleNotify(str(ex), desc))
        else:
            step = 0
            try:
                print("*** HAND SHAKING ***")
                step = step + 1
                if self._read_sock is None:
                    print("Atacching socket for reading...")
                    self._read_sock = self.attach()
                step = step + 1
                if self._reader_thread is None:
                    print("Starting reader thread...")
                    self._reader_thread = threading.Thread(target=self._receive_reuest_loop)
                    self._reader_thread.start()
                step = step + 1
                if self._write_sock is None:
                    print("Atacching socket for writing...")
                    self._write_sock = self.attach()
                step = step + 1
                if self._writer_thread is None:
                    print("Starting writer thread...")
                    self._writer_thread = threading.Thread(target=self._send_reuest_loop)
                    self._writer_thread.start()
                step = step + 1
                print("Done...")
                return True
            except Exception as ex:
                print(ex)
                desc = "when wait_start is {}, trouble occured between {} and {}.".format(self._wait_start, step, step+1)
                print(desc)
                self._res_queue.put(PreConsensusTroubleNotify(str(ex), desc))

    def _feedback(self, item):
        print(item)

    def _send_reuest_loop(self):
        print("WRITER THREAD START!!!")
        self._writer_running = True
        q = QuitNotify("quit", "force quit")
        while True:
            self._i = 1
            ret = self._send_request(q)
            if isinstance(ret, Exception):
                print("**** ", type(ret), ret)
                break
        self._writer_running = False
        print("WRITER THREAD END!!!")

    def _send_request(self, q):
        try:
            sock = self._write_sock
            if sock is None:
                return q
            print("###  reading from user  ###")
            item = self._req_queue.get()
            if isinstance(item, Exception):
                if type(item) is QuitNotify:
                    self.encode_and_send(self._write_sock, "", self._consensus.ConsensusKeywords.Reset)
                return item
            req_msg = self._consensus.encode_sending_data(item, self._consensus.ConsensusKeywords.SendData)
            self.encode_and_send(sock, len(req_msg), self._consensus.ConsensusKeywords.BeginSendData)
            _ = self.receive_and_decode(sock, self._consensus.ConsensusKeywords.AcceptBeginSendData, length=128, once=True)
            self.encode_and_send(sock, req_msg, self._consensus.ConsensusKeywords.SendData)
            _ = self.receive_and_decode(sock, self._consensus.ConsensusKeywords.AcceptSendData, length=128, once=True)
            return
        except ConsensusError as ex:
            print(ex)
            # self.encode_and_send(self._write_sock, "", self._consensus.ConsensusKeywords.Reset)
            return
        except ForceQuit as ex:
            return q
        except SocketConnectionBrokenError as ex:
            self._write_sock = None
            return ex
        except Exception as ex:
            print(ex)

    def _receive_reuest_loop(self):
        print("READER THREAD START!!!")
        self._reader_running = True
        q = QuitNotify("quit", "reset requested")
        while True:
            self._j = 1
            ret = self._receive_request(q)
            if isinstance(ret, Exception):
                print("**** ", type(ret), ret)
                break
        self._reader_running = False
        print("READER THREAD END!!!")

    def _receive_request(self, q):
        try:
            sock = self._read_sock
            if sock is None:
                return q
            print("###  reading from network  ###")
            length = self.receive_and_decode(sock, self._consensus.ConsensusKeywords.BeginSendData, length=128, once=True)
            self.encode_and_send(sock, "", self._consensus.ConsensusKeywords.AcceptBeginSendData)
            req = self.receive_and_decode(sock, self._consensus.ConsensusKeywords.SendData, length=length)
            self.encode_and_send(sock, "", self._consensus.ConsensusKeywords.AcceptSendData)
            _ = self.receive_and_decode(sock, self._consensus.ConsensusKeywords.EndSendData, length=128, once=True)
            self.encode_and_send(sock, "", self._consensus.ConsensusKeywords.AcceptSendData)
            self._feedback(req)
            print("**** RESPONSE ", req)
            return
        except ConsensusError as ex:
            print(ex)
            # self.encode_and_send(self._write_sock, "", self._consensus.ConsensusKeywords.Reset)
            return
        except ForceQuit as ex:
            return q
        except SocketConnectionBrokenError as ex:
            self._read_sock = None
            return ex
        except Exception as ex:
            print(ex)


function = print


def main_loop(comm, prompt):
    from admin import parse_command
    exp = []
    global function
    while True:
        try:
            script = input(prompt)
            cmd = parse_command(script)
            if len(cmd) == 0:
                continue
            args = cmd[1:]
            cmd = cmd[0]
            if cmd == "quit" or cmd == "exit":
                comm.finalize()
                # comm.push_request(QuitNotify("quit", "stop receiving and send quiting."))
                break
            elif cmd == "put" or cmd == "push":
                comm.push_request(" ".join(args))
            #elif cmd == "get":
            #    res = comm.pull_response()
            #    print(res)
            elif cmd == "start":
                comm.try_handshake()
            elif cmd == "cmd":
                # native call
                method = args[0]
                args = args[1:]
                callee = "{}({})".format(method, ",".join(args))
                print(callee)
                eval(callee)
            elif cmd == "eval":
                callee = " ".join(args)
                print(callee)
                eval(callee)
        except QuitNotify as ex:
            traceback.format_exc()
            exp.append(ex)
            print(ex.desc)
            print(type(ex), ex)
            function(ex.desc)
            break
        except ControlNotify as ex:
            traceback.format_exc()
            exp.append(ex)
            print(ex.desc)
            print(type(ex), ex)
            function(ex.desc)
        except Exception as ex:
            traceback.format_exc()
            exp.append(ex)
            print(type(ex), ex)


def main():
    host = "localhost"
    port = 1234
    timeout = 60
    listens = 5
    req_queue = queue.Queue()
    res_queue = queue.Queue()
    args = sys.argv[1:]
    if len(args) == 0:
        print("option -S or -s for server, -C or -c for client.")
        return
    elif args[0] == "-s" or args[0] == "-S":
        prompt = "$server> "
        wait_start = True  # server mode
    elif args[0] == "-c" or args[0] == "-C":
        prompt = "$client> "
        wait_start = False  # clent mode
    else:
        print("option -S or -s for server, -C or -c for client.")
        return
    comm = BidirectionalCommunicator(host, port, timeout, listens, wait_start=wait_start, req_queue=req_queue, res_queue=res_queue)
    main_loop(comm, prompt)


if __name__ == "__main__":
    main()
