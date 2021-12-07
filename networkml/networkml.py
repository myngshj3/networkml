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
from networkml.network import NetworkGenericWorld, ExtensibleWrappedAccessor
from networkml.network import NetworkCallable
from networkml.network import NetworkClassInstance, NetworkInstance, NetworkMethod, NetworkMethodCaller, NetworkTextSerializer
from networkml.generic import GenericValueHolder
import networkml.genericutils as GU
from networkml.specnetwork import SpecValidator, SpecificationGraph
from networkml.interpreter import NetworkInterpreter
from networkml.diplomat import Diplomat
from networkml.sentenceparser import SentenceSyntacticAnalyzer, SentenceParser


class SpecificationWorld(NetworkGenericWorld):

    def __init__(self, owner, config, super_class=None):
        self._nml_config = config
        print("***", self._nml_config['config'])
        super().__init__(owner, self._nml_config['signature'], super_class)
        G = nx.MultiDiGraph()
        self._N = SpecificationGraph(G, self._nml_config['spec-graph-config'])
        self._options = {}
        self._worlds = {}
        self._config = self.read_config(self._nml_config['config'])
        print(self._config)
        self.create_world()
        self._server = None
        self._diplomat = None

    def read_config(self, filename):
        return GU.read_json(filename)

    @property
    def N(self):
        return self._N

    @property
    def worlds(self):
        return self._worlds

    def quit_diplomat(self):
        self._diplomat.finalize()

    def diplomatically_interpret(self, script):
        try:
            return "I am not available now."
        except Exception as ex:
            return "Couldn't interpret your message in anyway."

    def help_text(self, kind):
        text_file_tag = kind  # "{}-file".format(text_tag)
        if text_file_tag in self._config.keys():
            filename = self._config[text_file_tag]
            with open(filename, "r") as f:
                return f.read()
        return ""

    def create_object(self, clazz):
        initializer_args = ()
        sig = "{}.{}".format(clazz.signature, clazz.next_instance_id)
        obj = clazz(clazz, sig, initializer_args)  # initializer has no args.
        validator = SpecValidator(obj)
        obj.set_validator(validator)
        # install necessary methods
        interpreter = NetworkInterpreter(obj)
        obj.declare_method(interpreter, globally=True)
        manager_config = self._config["instance-methods"]
        self.install_wrapped_accessor(obj, self, manager_config, interpreter)
        return obj

    def create_generator(self):
        initializer_args = ()
        sig = "{}.{}".format(self.signature, 1)
        clazz = self(self, sig, initializer_args)  # initializer has no args.
        validator = SpecValidator(clazz)
        clazz.set_validator(validator)
        # install necessary methods
        interpreter = NetworkInterpreter(clazz)
        clazz.declare_method(interpreter, globally=True)
        manager_config = self._config["generator-methods"]
        self.install_wrapped_accessor(clazz, self, manager_config, interpreter)

    def create_world(self):
        # construct self
        validator = SpecValidator(self)
        self.N.set_validator(validator)
        interpreter = NetworkInterpreter(self)
        self.declare_method(interpreter, globally=True)
        manager_config = self._config["manager-methods"]
        self.install_wrapped_accessor(self, self, manager_config, interpreter)
        # SpecificationGraph methods
        manager_config = self._config["specgraph-methods"]
        self.install_wrapped_accessor(self, self, manager_config, interpreter)
        # construct generator
        self.create_generator()

    def start_server(self):
        self._diplomat = Diplomat(self, self._nml_config['hostname'], self._nml_config['port'])
        self._diplomat.organize()
        self._diplomat.start()

    def finalize(self):
        self._diplomat.finalize()

    def install_wrapped_accessor(self, accessor_owner, entity_owner, dic: dict, interpreter):
        # construct self
        sv = "strict-verification"
        av = "args-validator"
        ht = "help-text-file"
        manager_config = dic
        for k in manager_config.keys():
            method_config = manager_config[k]
            if ht in method_config.keys():
                help_text = self.N.read_text_file(self, method_config[ht])
            else:
                help_text = None
            if sv in method_config.keys() and method_config[sv] and av in method_config.keys():
                args_validator = method_config[av]
                valid_eq = eval(args_validator)
            else:
                valid_eq = None
            globally = True
            if "equation" in method_config.keys():
                eqn = method_config["equation"]
                eqn = eval(eqn)
                globally = method_config["globally"]
                if valid_eq is None:
                    m = ExtensibleWrappedAccessor(accessor_owner, k, entity_owner, eqn,
                                                  help_text=help_text,
                                                  globally=globally)
                else:
                    m = ExtensibleWrappedAccessor(accessor_owner, k, entity_owner, eqn,
                                                  args_validator=valid_eq,
                                                  help_text=help_text,
                                                  globally=globally)
            elif "script" in method_config.keys():
                script = method_config["script"]
                m = interpreter(self, [script])
            elif "script-file" in method_config.keys():
                script = self.read_text_file(method_config["script-file"])
                m = interpreter(self, [script])
            else:
                m = None
                print("Invalid configuration description for method {}".format(k))
            if m is not None:
                accessor_owner.declare_method(m, globally=globally)

    def available_methods(self, caller):
        for m in caller._context[0]["methods"].keys():
            print(m)

    def return_val(self, caller, args):
        rtn = args[0]
        report = []
        for a in args[1:]:
            if a == "value":
                report.append(a)
            elif a == "fail":
                report.append(rtn.fail)
            elif a == "success":
                report.append(rtn.success)
            elif a == "reasons":
                report.append(rtn.reasons)
            elif a == "cancel":
                report.append(rtn.cancel)
            else:
                print("ignored {}".format(a))
        return report

    def parse_command(self, command_line_text):
        pat = r"(?P<command>[a-z]+[a-z_\-]*)\s*"
        m = re.match(pat, command_line_text)
        if m is None:
            return None
        dic = m.groupdict()
        cmd = dic['command']
        options = command_line_text[m.span()[1]:]
        argpat = r"(?P<arg>(\"([^\"]|\"\")*\"|[a-zA-Z0-9_\.]+|\-{1,2}[a-z]+))\s*"
        args = [cmd]
        while True:
            if options == "":
                break
            m = re.match(argpat, options)
            if m is None and options != "":
                return None
            else:
                dic = m.groupdict()
                args.append(dic['arg'])
                options = options[m.span()[1]::]
        return args

    def read_from_console(self, caller, prompt):
        script = input(prompt)
        null_pattern = r"^\s*$"
        m = re.match(null_pattern, script)
        if m is None:
            return script
        else:
            return ""

    def get_callable_method(self, method_owner, method_signature):
        m = method_owner.get_method(self, method_signature)
        return m

    def get_method_doc(self, method_owner, method_signature):
        method_group = method_owner._context[0]["methods"]
        if method_signature in method_group.keys():
            return method_group[method_signature].document
        return None

    def invoke_callable_method(self, caller, sig, args):
        m = self.get_method(caller, sig)
        if m is not None:
            return m(caller, args)
        return None

    def read_text_file(self, file):
        return self.N.read_text_file(None, file)

    def get_managed_classes(self):
        return self.classes

    def get_managed_objects(self):
        return self.worlds

    def contact_objects(self, caller, args):
        return self.get_managed_objects()

    def create_managed_object(self, class_sig, name):
        if name in self.worlds.keys():
            print("Name '{}' already used. pass another name".format(name))
            return
        for sig in self.classes.keys():
            if sig == class_sig:
                clazz = self.classes[sig]
                obj = self.create_object(clazz)
                obj.set_private_attribute(self, "$self", obj)
                obj.set_private_attribute(self, "$manager", self)
                obj.set_private_attribute(self, "$generator", clazz)
                # obj.set_var(var, globally=True)
                self.worlds[name] = obj
                # main_loop = self.get_callable_method(obj, "main_loop")
                # if main_loop is None:
                #     print("main loop method is not implemented for you.")
                #     print("Ask your administrator.")
                # else:
                #     try:
                #         # print("\nAt first, type help();\n")
                #         rtn = main_loop(obj)
                #         print("main_loop exited with:{}".format(rtn))
                #     except Exception as ex:
                #         print(ex)
                # self.worlds.pop(name)
                return
        print("Class '{}' is not managed.".format(class_sig))

    def help(self, caller, args):
        if caller == self:
            text = self.help_text("manager-introduction-text-file").format(caller)
            func = lambda x: self.get_managed_classes()
        elif caller in self.classes.values():
            text = self.help_text("manager-introduction-text-file").format(caller)
            func = None
        else:
            func = None
            text = ""
            for world in self.worlds.values():
                if caller == world:
                    text = self.help_text("instance-introduction-text-file").format(caller)
                    break
        print("help")
        print(text)
        if func is not None:
            func(caller)


def main(args):
    if len(args) == 1:
        config = GU.read_json("nmlserver.conf")
    elif len(args) == 1 and args[1] == "-help":
        global _help_text
        print(_help_text)
        return
    elif len(args) == 3 and args[1] == "-config":
        config = GU.read_json(args[2])
    else:
        print("args", args[1:], "ignored.")
        config = GU.read_json("nmlserver.conf")

    # construct initial network
    networkml_config = config['networkml-config']
    server_config = config['nmlserver-config']
    S = SpecificationWorld(None, networkml_config)
    if "default-model" in server_config.keys():
        S.N.load(S, server_config['default-model'])
    S.start_server()

    # main loop
    print("NetworkML Start!!!")
    S.help(S, ())
    while True:
        try:
            # if not null_input:
            #     S.help(S, ())
            script = input("input request: ")
            if not S.interpret(script):
                S.finalize()
                break

            continue
        except Exception as ex:
            if config["traceback"]:
                print(traceback.format_exc())
            else:
                print(ex)
    print("NetworkML Finished!!!")


if __name__ == "__main__":
    main(sys.argv)
