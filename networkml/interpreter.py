# -*- coding: utf-8 -*-

import re
import traceback
import inspect
import networkx as nx
import openpyxl
import os
import json
import sys
import inspect
from enum import Enum
from networkml.error import NetworkError, NetworkLexerError, NetworkParserError
from networkml.network import NetworkVariable, SimpleVariable, NetworkResolver, WrappedAccessor, StrictWrappedAccessor
from networkml.network import NetworkGenericWorld
from networkml.network import NetworkCallable, CommandOption, NetworkReturnValue
from networkml.network import NetworkClassInstance, NetworkInstance, NetworkMethod, NetworkMethodCaller, NetworkTextSerializer
from networkml.generic import GenericValueHolder
from networkml.specnetwork import SpecValidator, SpecificationGraph
from networkml.lexer import NetworkParser


class NetworkInterpreter(NetworkMethod):

    def __init__(self, method_owner):
        super().__init__(method_owner, "interpret", ["script", "parser"], [])
        self._parser = NetworkParser(method_owner)
        self._options = []

    def call_impl(self, caller, args, **kwargs):
        script = args[0]
        return self.interpret_impl(caller, script, self._parser)

    def args_impl(self, caller, args, **kwargs):
        if len(args) == 0:
            return NetworkReturnValue(args, False, "Too few argument.")
        new_args = []
        if isinstance(args[0], GenericValueHolder):
            new_args.append(args[0].value)
        else:
            new_args.append(args[0])
        for i, a in enumerate(args[1:]):
            if isinstance(a, CommandOption):
                self._options.append(a)
            else:
                print("args[{}] ignored.".format(i))
        return new_args

    def interpret_impl(self, caller, script, parser):
        safe = True
        for opt in self._options:
            if opt.name == "safe" and opt.has_assignee and not opt.value:
                safe = False
        if safe:
            try:
                return self.actual_interpret(caller, script, parser)
            except NetworkLexerError as ex:
                print("LexerError:", ex.message)
                # ex.detail()
            except NetworkParserError as ex:
                print("ParserError: ", ex.message)
            except NetworkError as ex:
                print("Network error:()".format(script))
                while ex is not None and isinstance(ex, NetworkError):
                    print("NetworkError: ", ex.message)
                    ex = ex.cause
                if ex is not None:
                    print(type(ex), ex)
            except Exception as ex:
                print(type(ex), ex)

        else:
            return self.actual_interpret(caller, script, parser)

    def actual_interpret(self, caller, script, parser):
        result = parser.parse_script(script)
        rtn = None
        if type(result) is not list:
            return None
        for obj in result:
            if isinstance(obj, NetworkClassInstance):
                rtn = obj
            elif isinstance(obj, NetworkMethod):
                rtn = obj
            elif isinstance(obj, NetworkCallable):
                rtn = obj(caller)
        return rtn