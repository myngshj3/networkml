# -*- coding:utf-8 -*-

import socket
import pickle
import threading
import sys
import queue
import re
import enum
from networkml.consensus import Consensus, ConsensusError, ConsensusReset, ConsensusConfused
from networkml.server import ServerHandler, SocketConnectionBrokenError, WorkerDispacher
from networkml.sentenceparser import SentenceSyntacticAnalyzer, SentenceParser, SentenceParserError, SentenceSyntacticError
from networkml.consensus import Consensus, ConsensusError, ConsensusReset, ConsensusConfused


class Diplomat(WorkerDispacher):

    def __init__(self, manager, hostname, port):
        super().__init__(None, self, manager, hostname, port)

    def interpret(self, msg):
        rtn = "NG"
        try:
            pat = r"^\s*(?P<command>(help|contact|contactees|bye))(|\s+(?P<avator>.+))\s*$"
            m = re.match(pat, msg)
            if m is None:
                rtn = "NG, type 'help'."
                return rtn
            else:
                g = m.groupdict()
                if g['command'] == "help":
                    rtn = "OK,"
                    rtn = "{}\n{}".format(rtn, "type 'contact <avator>'.")
                    rtn = "{}\n{}".format(rtn, "type 'contactees'.")
                    rtn = "{}\n{}".format(rtn, "type 'bye'.")
                    return rtn
                elif g['command'] == "contactees":
                    objs = [_ for _ in self._manager.get_managed_objects(None, None)]
                    return "OK, {}".format(tuple(objs))
                elif g['command'] == "contact":
                    avator = g['avator']
                    if avator is None:
                        return "NG, avator name not specified."
                    else:
                        objects = self._manager.get_managed_objects()
                        if avator in objects.keys():
                            self.fork(avator, objects[avator])  # socket called
                            self.reset_client()
                            return "OK, type 'help'."
                        else:
                            return "NG, avator '{}' not exists.".format(avator)
                elif g['command'] == "bye":
                    return "OK, bye is not supported now."
                return "NG"
        except SentenceSyntacticError as ex:
            rtn = "{} {}".format(rtn, ex.message)
        except SentenceParserError as ex:
            print(ex.message)
            ex.detail()
            rtn = "{} {}\n{}".format(rtn, ex.message, ex.detail())
        except Exception as ex:
            rtn = "{} {}".format(rtn, ex)
        finally:
            return rtn
