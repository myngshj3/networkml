# -*- coding:utf-8 -*-

import os
import socket
import sys
import re
import json
import enum


class ConsensusError(Exception):

    def __init__(self, msg):
        print("ConsensusError with {}".format(msg))
        super().__init__(msg)


class ConsensusReset(ConsensusError):

    def __init__(self, msg=""):
        super().__init__(msg)


class ConsensusConfused(ConsensusError):

    def __init__(self, msg=""):
        super().__init__(msg)


class Consensus:

    class ConsensusKeywords(enum.Enum):

        Reset = "ConsensusKeywords.Reset"
        AcceptReset = "ConsensusKeywords.AcceptReset"
        Confused = "ConsensusKeywords.Confused"
        AcceptConfused = "ConsensusKeywords.AcceptConfused"
        BeginRequest = "ConsensusKeywords.BeginRequest"
        AcceptBeginRequest = "ConsensusKeywords.AcceptBeginRequest"
        SendRequest = "ConsensusKeywords.SendRequest"
        AcceptSendRequest = "ConsensusKeywords.AcceptSendRequest"
        EndRequest = "ConsensusKeywords.EndRequest"
        AcceptEndRequest = "ConsensusKeywords.AcceptEndRequest"
        BeginResponse = "ConsensusKeywords.BeginResponse"
        AcceptBeginResponse = "ConsensusKeywords.AcceptBeginResponse"
        SendResponse = "ConsensusKeywords.SendResponse"
        AcceptSendResponse = "ConsensusKeywords.AcceptSendResponse"
        EndResponse = "ConsensusKeywords.EndResponse"
        AcceptEndResponse = "ConsensusKeywords.AcceptEndResponse"
        Ack = "ConsensusKeywords.Ack"
        OK = "ConsensusKeywords.OK"
        NG = "ConsensusKeywords.NG"

    Successor = "successor"
    Int = "int"
    Str = "str"

    def __init__(self, config=None):
        if config is None:
            home_dir = os.getenv("NETWORKML_HOME")
            if home_dir is None:
                config = "consensus.conf"
            else:
                config = home_dir + "/" + "consensus.conf"
        with open(config, "r") as f:
            self._config = json.load(f)

    def encode_sending_data(self, data, start):
        config = self._config
        if start.value in config.keys():
            sending_data = "{} {}".format(start, data)
            return sending_data.encode("utf-8")
        expect = "expected {}, but {} got.".format(start, data)
        raise ConsensusError(expect)

    def decode_received_data(self, data, expected):
        if type(expected) is not list and type(expected) is not tuple:
            expected = [expected]
        config = self._config
        msg = data.decode("utf-8")
        for e in expected:
            if e.value in config.keys():
                succ = config[e.value][self.Successor]
                if len(e.value) <= len(msg) and e.value == self.ConsensusKeywords.Reset.value:
                    predicates = msg[len(e.value):]
                    raise ConsensusReset(predicates)
                elif len(e.value) <= len(msg) and e.value == self.ConsensusKeywords.Confused.value:
                    predicates = msg[len(e.value):]
                    msg = "{} {}".format(e.value, predicates)
                    raise ConsensusConfused(msg)
                elif len(e.value) <= len(msg) and e.value == msg[:len(e.value)]:
                    predicates = msg[len(e.value):]
                    if succ == "" and predicates == "":
                        return predicates
                    elif succ == self.Int:
                        return int(predicates)
                    elif succ == self.Str:
                        return predicates
        expect = "expected ({}".format(expected[0])
        for e in expected[1:]:
            expect = "{},{}".format(expect, e.value)
        expect = "{}), but {} got.".format(expect, msg)
        raise ConsensusError(expect)
