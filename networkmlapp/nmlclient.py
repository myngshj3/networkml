# -*- coding:utf-8 -*-

import os
import re
import socket
import sys
import traceback
import networkml.genericutils as GU
from networkml.server import ForceQuit
from networkml.client import AutonomousClient
from networkml.sentenceparser import SentenceSyntacticAnalyzer, SentenceParser
from networkml.sentenceparser import SentenceSyntacticError, SentenceParserError


class NetworkMLClient(AutonomousClient):

    def __init__(self, config):
        self._config = config
        signature = config['nmlclient-signature']
        host = config['hostname']
        port = config['port']
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(30)
        super().__init__(signature, None, sock=sock, hostname=host, port=port)

    def process_response(self, res):
        print(res)


def main_loop(client):
    q = False
    client.start()
    opt_pat = r"^\s*((?P<quit>(quit|exit))|debug\s*=\s*(?P<debug>(on|off))|)\s*$"
    while not q:
        script = input("$client ")
        m = re.match(opt_pat, script)
        if m is None:
            client.push_queue(script)
        else:
            g = m.groupdict()
            if g['quit'] is not None:
                q = True
            elif g['debug'] is not None:
                if g['debug'] == "on":
                    client.set_debug(True)
                else:
                    client.set_debug(False)
            else:
                continue
    client.push_queue(ForceQuit("quitting from console"))
    client.finalize()


def main():
    home_dir = os.getenv("NMLCLIENT_HOME")
    if home_dir is None:
        config_file = "nmlclient.conf"
    else:
        config_file = home_dir + "/" + "nmlclient.conf"
    config = GU.read_json(config_file)
    l = SentenceSyntacticAnalyzer()
    l.build()
    parser = SentenceParser(l)
    C = NetworkMLClient(config)
    C.organize()
    print("NetworkMLClient Started!!!")
    main_loop(C)
    print("NetworkMLClient Finished!!!")


if __name__ == "__main__":
    main()
