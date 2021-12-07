# -*- coding: utf-8 -*-

import re
import ply.lex as lex
import ply.yacc as yacc
import sys
import traceback
import networkx as nx
import openpyxl
import os
import json
import sys
import inspect
from enum import Enum


class NetworkError(Exception):

    FORMAT_STRING = ""

    def __init__(self, message, cause: Exception = None):
        self._message = message
        self._causes = []
        self._causes.append(cause)

    @property
    def message(self) -> str:
        return self._message

    @property
    def cause(self):
        return self._causes[len(self._causes)-1]

    @property
    def causes(self):
        return self._causes

    def analyze_causes(self):
        pass


class NetworkReferenceError(NetworkError):

    def __init__(self, msg, ex=None):
        super().__init__(msg, ex)


class NetworkNotImplementationError(NetworkError):

    FORMAT_STRING = "{} not implemented."

    def __init__(self, method_signature, cause: Exception = None):
        message = self.FORMAT_STRING.format(method_signature)
        super().__init__(message, cause)


class NetworkMethodError(NetworkError):

    FORMAT_STRING = "{} call failed."

    def __init__(self, method_signature, cause: Exception = None):
        message = self.FORMAT_STRING.format(method_signature)
        super().__init__(message, cause)


class NetworkUnknownMethodError(NetworkMethodError):

    FORMAT_STRING = "{} couldn't detect method {}:."

    def __init__(self, detector, method_signature, cause: Exception = None):
        message = self.FORMAT_STRING.format(detector, method_signature)
        super().__init__(message, cause)


class NetworkMethodRequirementError(NetworkMethodError):

    FORMAT_STRING = "Requirement for {} not satisfied:{}."

    def __init__(self, method_signature, reason, cause: Exception = None):
        message = self.FORMAT_STRING.format(method_signature, reason)
        super().__init__(message, cause)


class NetworkMethodFailedError(NetworkMethodError):

    FORMAT_STRING = "Requirement for {} not satisfied:{}."

    def __init__(self, method_signature, reason, cause: Exception = None):
        message = self.FORMAT_STRING.format(method_signature, reason)
        super().__init__(message, cause)


class NetworkLexerError(NetworkError):
    def __init__(self, parser):
        self._parser = parser
        message = "Lexer error: Syntax error: line={}, pos={}, value='{}'.".format(self.lineno, self.lexpos, self.value)
        message = "{}{}{}".format(message, "\n", self.detail())
        super().__init__(message)

    @property
    def lineno(self):
        return self._parser.lineno

    @property
    def lexpos(self):
        return self._parser.lexpos

    @property
    def value(self):
        return self._parser.value

    @property
    def type(self):
        return self._parser.type

    def detail(self):
        lexdata = self._parser.lexer.lexdata
        print(lexdata)
        e = ""
        for _ in range(self.lexpos):
            e = "{}{}".format(e, " ")
        for _ in range(len(self.value)):
            "{}{}".format(e, "^")
        e = "{} <-- '{}':{}".format(e, self.value, self.type)
        print(e)


class NetworkParseError(NetworkError):
    def __init__(self, parser, ex=None):
        super().__init__("Parser error: parser".format(parser))
        self._parser = parser

    # @property
    # def data(self):
    #     return self._lexdata
    #
    # @property
    # def pos(self):
    #     return self._lexpos
    #
    # @property
    # def match(self):
    #     return self._lexmatch


class NetworkParserError(NetworkParseError):
    def __init__(self, parser):
        super().__init__(parser)
