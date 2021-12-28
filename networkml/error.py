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


class NetworkScriptInterruptionException(NetworkError):

    def __init__(self, message=None):
        super().__init__(message)


class NetworkLexerError(NetworkError):
    def __init__(self, lexer, ex=None):
        super().__init__("Lexer error", ex)
        self._lexer = lexer
        # self._lexdata = lexer.lexdata
        # self._lexpos = lexer.lexpos
        # self._lexmatch = lexer.lexmatch

    # @property
    # def lineno(self):
    #     return 0
    #
    # @property
    # def value(self):
    #     return self._lexer.value
    #
    # @property
    # def type(self):
    #     return self._lexer.type

    def detail(self):
        print(self._lexer)


class NetworkParseError(NetworkError):
    def __init__(self, parser, ex=None):
        super().__init__("Parser error", ex)
        self._parser = parser
        if parser is None:
            self._pos = None
            self._lineno = None
            self._type = None
            self._value = None
            self._lexdata = None
            self._lexpos = None
            self._lexmatch = None
        else:
            self._parser = parser
            self._pos = parser.lexpos
            self._lineno = parser.lineno
            self._type = parser.type
            self._value = parser.value
            self._lexdata = parser.lexer.lexdata
            self._lexpos = parser.lexer.lexpos
            self._lexmatch = parser.lexer.lexmatch
        # print('Syntax error: %d: %d: %r' % (parser.lineno, parser.lexpos, parser.value))

    @property
    def pos(self):
        return self._pos

    @property
    def lineno(self):
        return self._lineno

    @property
    def type(self):
        return self._type

    @property
    def value(self):
        return self._value

    @property
    def lexdata(self):
        return self._lexdata

    @property
    def lexpos(self):
        return self._lexpos

    @property
    def lexmatch(self):
        return self._lexmatch

    def detail(self):
        # print("Syntax error: pos={}, value='{}':{}, lexdata={}".format(self.pos, self.value, self.type, self.lexdata))
        print("Syntax error: pos={}, value='{}':{}".format(self.pos, self.value, self.type))
        if self._parser is None or self._parser.lexer is None:
            return
        preerr = self.lexdata[:self.pos]
        i = len(preerr) - 1
        for i in sorted(range(len(preerr)), reverse=True):
            if preerr[i] == "\n":
                break
        if preerr[i] == "\n":
            i = i + 1
        posterr = ""
        for j, c in enumerate(self.lexdata[i:]):
            if c == "\n":
                break
            else:
                posterr = "{}{}".format(posterr, c)
        posterr = "{}".format(posterr)
        e = ""
        for c in preerr[i:]:
            if c != "\t":
                c = " "
            e = "{}{}".format(e, c)
        for _ in range(len(self.value)):
            e = "{}{}".format(e, "^")
        e = "{} <-- unexpected token:'{}':{}".format(e, self.value, self.type)
        e = "{}{}\n{}".format(preerr[:i], posterr, e)
        print(e)
        return e


class NetworkParserError(NetworkParseError):
    def __init__(self, parser):
        super().__init__(parser)
