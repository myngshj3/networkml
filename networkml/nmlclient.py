# -*- coding:utf-8 -*-

import re
import socket
import sys
import networkml.genericutils as GU
from networkml.server import ForceQuit, SocketConnectionBrokenError
from networkml.client import AutonomousClient, SyncClient
from networkml.sentenceparser import SentenceSyntacticAnalyzer, SentenceParser
from networkml.sentenceparser import SentenceSyntacticError, SentenceParserError
import traceback
from networkml.generic import debug, set_debug


class NetworkMLClient(SyncClient):

    def __init__(self, config):
        self._config = config
        signature = config['nmlclient-signature']
        host = config['hostname']
        port = config['port']
        sock = None
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.connect((host, port))
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sock.settimeout(30)
        super().__init__(signature, None, sock=sock, hostname=host, port=port)

    def process_response(self, res):
        print(res)


class NetworkMLAsyncClient(AutonomousClient):

    def __init__(self, config):
        self._config = config
        signature = config['nmlclient-signature']
        host = config['hostname']
        port = config['port']
        if "timeout" in config.keys():
            timeout = config['timeout']
        else:
            timeout = None
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(timeout)
        super().__init__(signature, None, sock=sock, hostname=host, port=port)

    def process_response(self, res):
        print(res)


def main_loop(client, prompt, retry=5):
    started = False
    organized = False
    while not started and retry > 0:
        try:
            if not organized:
                client.organize()
                organized = True
            if isinstance(client, NetworkMLAsyncClient):
                client.start()
            started = True
            break
        except Exception as ex:
            print(ex)
            retry = retry - 1
    if not started:
        print("Connection failed. try 'connect' to connect.")
    q = False
    opt_pat = r"^\s*((?P<quit>(quit|exit))|debug\s+(?P<debug>(on|off))|(?P<connect>connect)|)\s*$"
    while not q:
        try:
            script = input(prompt)
            m = re.match(opt_pat, script)
            if m is None:
                client.push_queue(script)
            else:
                g = m.groupdict()
                if g['quit'] is not None:
                    q = True
                elif g['debug'] is not None:
                    if g['debug'] == "on":
                        set_debug(True)
                    else:
                        set_debug(False)
                elif g["connect"] is not None:
                    client.try_connect()
                else:
                    continue
        except Exception as ex:
            print(type(ex), ex)

    if isinstance(client, NetworkMLAsyncClient):
        client.push_queue(ForceQuit("quitting from console"))
        client.finalize()


def main(args):
    if len(args) == 3 and args[1] == "-f":
        config_file = args[2]
        config = GU.read_json(config_file)
    elif len(args) == 1:
        config = GU.read_json("nmlclient.conf")
        if "debug" in config.keys():
            set_debug(config['debug'])
    else:
        print(args, "ignored. using default config.")
        config = GU.read_json("nmlclient.conf")
    hostname = config['hostname']
    port = config['port']
    opt_pat = r"^\-(hostname=(?P<hostname>.+)|port=(?P<port>\d+))$"
    for a in args[1:]:
        m, g = GU.rematch(opt_pat, a)
        if m is None:
            print(a, "is ignored.")
        else:
            if g['hostname'] is not None:
                hostname = g['hostname']
            elif g["port"] is not None:
                port = int(g["port"])

    l = SentenceSyntacticAnalyzer()
    l.build()
    parser = SentenceParser(l)
    if config["async"]:
        C = NetworkMLAsyncClient(config)
    else:
        C = NetworkMLClient(config)
    print("NetworkMLClient Started!!!")
    if config["use-script"] and "initial-script" in config.keys():
        with open(config["initial-script"], "r") as f:
            C.push_queue(f.read())
    if not config["auto-quit"]:
        main_loop(C, config["prompt"])
    print("NetworkMLClient Finished!!!")


if __name__ == "__main__":
    main(sys.argv)
