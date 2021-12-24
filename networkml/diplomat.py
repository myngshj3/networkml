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
from networkml.generic import debug


class Diplomat(WorkerDispacher):

    def __init__(self, obj, manager, hostname, port):
        super().__init__(obj.signature, obj, manager, hostname, port)

    def close_conns(self):

        pass

    def interpret(self, caller, args):
        msg = args[0]
        rtn = "NG"
        try:
            pat = r"^\s*(?P<command>(help|contact|contactees|bye))(|\s+(?P<avator>.+))\s*$"
            m = re.match(pat, msg)
            if m is None:
                rtn = "NG, type 'help'."
            else:
                g = m.groupdict()
                command = g['command']
                if command == "help":
                    rtn = "OK,"
                    rtn = "{}\n{}".format(rtn, "type 'contact <avator>'.")
                    rtn = "{}\n{}".format(rtn, "type 'contactees'.")
                    rtn = "{}\n{}".format(rtn, "type 'bye'.")
                elif command == "contactees":
                    objs = [_ for _ in self._manager.get_managed_objects().keys()]
                    rtn = "OK, {}".format(tuple(objs))
                elif command == "contact":
                    avator = g['avator']
                    if avator is None:
                        rtn = "NG, avator name not specified."
                    else:
                        objects = self._manager.get_managed_objects()
                        if avator in objects.keys():
                            if avator is self._workers.keys():
                                rtn = "NG, already in use."
                            else:
                                self.fork(avator, objects[avator])  # socket called
                                rtn = "OK, '{}' connected with you. type 'help'.".format(avator)
                        else:
                            rtn = "NG, avator '{}' not exists.".format(avator)
                elif command == "bye":
                    rtn = "OK, bye is not supported now."
                else:
                    rtn = "NG, invalid command '{}'".format(command)
            debug(rtn)
        except SentenceSyntacticError as ex:
            rtn = "{} {}".format(rtn, ex.message)
        except SentenceParserError as ex:
            debug(ex.message)
            ex.detail()
            rtn = "{} {}\n{}".format(rtn, ex.message, ex.detail())
        except Exception as ex:
            rtn = "{} {}".format(rtn, ex)
        finally:
            caller.print_buf.append(rtn)
