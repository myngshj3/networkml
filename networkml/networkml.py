# -*- coding: utf-8 -*-

import re
import traceback
import inspect
import networkx as nx
import openpyxl
import os
import json
import sys
import importlib
import inspect
from networkml.network import get_armer, NetworkGenericWorld, ExtensibleWrappedAccessor
import networkml.genericutils as GU
from networkml.generic import debug, print_debug, print_info, print_fatal
from networkml.specnetwork import SpecValidator, SpecificationGraph
from networkml.diplomat import Diplomat
from networkml.admin import Administrator
from networkml import config


def init(conf):
    log_config = conf['log-config']
    config.set_log_config(log_config)


class SpecificationWorld(NetworkGenericWorld):

    def __init__(self, owner, config, super_class=None):
        sig = config['signature']
        super().__init__(owner, signature=sig, super_class=super_class, embedded=[(sig, sig)])
        self._nml_config = config
        self._N = None  # SpecificationGraph(G, self._nml_config['spec-graph-config'])
        self._options = {}
        self._worlds = {}
        self._config = None  # self.read_config(self._nml_config['config'])
        # debug(self._config)
        self._server = None
        self._plugin_interpreters = {}
        self._diplomat = None
        self._admin = None
        self._modules = {}

    def setup(self):
        self.log.info("setting up SpecificationGraph...")
        G = nx.MultiDiGraph()
        self._N = SpecificationGraph(G, self._nml_config['spec-graph-config'])
        self.log.info("done")
        self.log.info("setting up config...")
        self._config = GU.read_json(self._nml_config['config'])
        self.log.info("done")
        self.log.info("setting up manager object, generator objects and instance objects...")
        self.create_world()
        self.log.info("done")
        self.log.info("setting up language interpreters")
        plugin_config = self._nml_config["plugin-interpreters"]
        for interp in plugin_config.keys():
            self.plugin_load(interp)
            callee = plugin_config[interp]["callable"]
            textfile = plugin_config[interp]["test-file"]
            self.log.info("testing interpreter '{}' with text file '{}'...".format(interp, textfile))
            result = self.plugin_interpret(self, [interp, callee, (textfile, "-f")])
            self.log.info(result)
            self.log.info("done")
        self.log.info("setting up administrator...")
        self.create_admin()
        self.log.info("done")
        self.log.info("setting up diplomacy...")
        self.create_diplomat()
        self.log.info("done")

    # def read_config(self, filename):
    #     return GU.read_json(filename)

    @property
    def N(self):
        return self._N

    @property
    def worlds(self):
        return self._worlds

    def finished(self, worker):
        pass  # do nothing presently.

    def quit_diplomat(self):
        self._diplomat.finalize()

    def plugin_interpret(self, caller, args):
        try:
            self.log.info("arguments are below,")
            print(caller, args)
            mod = args[0]
            callee = args[1]
            args = args[2]
            if mod in self._plugin_interpreters.keys():
                mod = self._plugin_interpreters[mod]
                callee = mod["callable"]
            else:
                return "NG, no such named interpreter {}.{}".format(mod, callee)
            if len(args) == 1:
                script = args[0]
            elif len(args) == 2 and args[1] == "-f":
                with open(args[0], "r", encoding="utf-8") as f:
                    script = f.read()
            else:
                self.log.debug("argument error:", args)
                return None
            return callee(script)
        except Exception as ex:
            self.log.error(ex)
            return ex

    def plugin_load(self, interp):
        self.log.info("loading interpreter {}...".format(interp))
        plugin_interpreters = self._nml_config["plugin-interpreters"]
        mod_info = plugin_interpreters[interp]
        self.log.info("loading module {}...".format(mod_info))
        mod = importlib.import_module(mod_info["module"])
        callee = mod_info["callable"]
        config = mod_info["config"]
        self.log.info("loading callable {} from {}...".format(callee, mod))
        callee = getattr(mod, callee)
        callee = callee(config_file=config)
        self._plugin_interpreters[interp] = {}
        self._plugin_interpreters[interp]["module"] = mod
        self._plugin_interpreters[interp]["callable"] = callee
        self.log.info("plugin successfully loaded.")

    def plugin_reload(self, interp):
        self.log.info("reloading '{}'".format(interp))
        if interp in self._nml_config["plugin-interpreters"].keys():
            self.plugin_load(interp)
        else:
            self.log.info("'{}' not found.".format(interp))

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
        obj = clazz(clazz, (sig, [('specgraph', self.N)], initializer_args))  # initializer has no args.
        validator = SpecValidator(obj)
        obj.set_validator(validator)
        # install necessary methods
        instance_config = self._config["instance-methods"]
        self.install_wrapped_accessor(obj, self, instance_config)
        # SpecificationGraph methods
        specworld_config = self._config["specgraph-methods"]
        self.install_wrapped_accessor(obj, self, specworld_config)
        return obj

    def create_generator(self):
        i = 0
        for i in range(len(self.classes.keys())):
            sig = "{}[{}]".format(self._nml_config['signature'], i)
            if sig not in self.classes.keys():
                break
        if i == len(self.classes.keys()):
            i = i+1
        clazz_sig = "{}[{}]".format(self._nml_config['signature'], i)
        self_sig = self._nml_config['signature']
        embedded = ((self_sig, self_sig), ("SpecGraph", self.N))
        args = ()
        clazz = self(self, (clazz_sig, embedded, args))  # initializer has embedded attrib and no args.
        self.classes[clazz_sig] = clazz
        validator = SpecValidator(clazz)
        clazz.set_validator(validator)
        # install necessary methods
        config = self._config["generator-methods"]
        self.install_wrapped_accessor(clazz, self, config)

    def create_world(self):
        # construct self
        validator = SpecValidator(self)
        self.N.set_validator(validator)
        config = self._config["manager-methods"]
        self.install_wrapped_accessor(self, self, config)
        # SpecificationGraph methods
        config = self._config["specgraph-methods"]
        self.install_wrapped_accessor(self, self, config)
        # construct generator
        self.create_generator()

    def create_admin(self):
        if len(self.classes.keys()) == 0:
            return
        name = sorted(self.classes.keys())[0]
        obj = self.create_object(self.classes[name])
        admin = Administrator(obj, self, self._nml_config['hostname'], self._nml_config['port'])
        self._admin = admin

    def admin_command(self, command):
        self._admin.interpret(None, [command])

    def create_diplomat(self):
        if len(self.classes.keys()) == 0:
            return
        name = sorted(self.classes.keys())[0]
        obj = self.create_object(self.classes[name])
        diplomat = Diplomat(obj, self, self._nml_config['hostname'], self._nml_config['port'])
        interpreter = ExtensibleWrappedAccessor(obj, "interpret", diplomat, lambda ao, c, eo, ca, ea: eo.interpret(c, ca),
                                                globally=True)
        obj.register_method(obj, interpreter.signature, interpreter, depth=0, overwrite=None)
        interpreter = obj.get_method(obj, "interpret")
        print("interpreter of", obj, "is", interpreter)
        interpreter(obj, ["help"])
        print("test interpretation of", obj, "is")
        obj.flush_print_buf()
        self._diplomat = diplomat

    def start_server(self):
        self._diplomat.organize()
        self._diplomat.start()

    def finalize(self):
        self._diplomat.finalize()

    def install_wrapped_accessor(self, accessor_owner, entity_owner, config: dict):
        # FIXME dynamic method implementation is integrated to MethodArmer class.
        armer = get_armer()
        for sig in config.keys():
            method_config = config[sig]
            armer.arm_method(sig, accessor_owner, accessor_owner.generator, entity_owner, method_config)
        # # Acccessor to Specification Graph.
        # m = ExtensibleWrappedAccessor(accessor_owner, "specgraph", entity_owner,
        #                               lambda ao, c, eo, ca, ea: eo.N,
        #                               help_text="Hello, Specification World!",
        #                               globally=True)
        # accessor_owner.register_method(accessor_owner, m.signature, m, depth=0, overwrite=None)
        # # construct self
        # sv = "strict-verification"
        # av = "args-validator"
        # ht = "help-text-file"
        # for k in config.keys():
        #     method_config = config[k]
        #     if ht in method_config.keys():
        #         help_text = self.N.read_text_file(self, method_config[ht])
        #     else:
        #         help_text = None
        #     if sv in method_config.keys() and method_config[sv] and av in method_config.keys():
        #         args_validator = method_config[av]
        #         valid_eq = eval(args_validator)
        #     else:
        #         valid_eq = None
        #     globally = True
        #     interpreter = accessor_owner.get_method(accessor_owner, "interpret")
        #     if "equation" in method_config.keys():
        #         eqn = method_config["equation"]
        #         eqn = eval(eqn)
        #         globally = method_config["globally"]
        #         if valid_eq is None:
        #             m = ExtensibleWrappedAccessor(accessor_owner, k, entity_owner, eqn,
        #                                           help_text=help_text,
        #                                           globally=globally)
        #         else:
        #             m = ExtensibleWrappedAccessor(accessor_owner, k, entity_owner, eqn,
        #                                           args_validator=valid_eq,
        #                                           help_text=help_text,
        #                                           globally=globally)
        #     elif "script" in method_config.keys():
        #         script = method_config["script"]
        #         m = interpreter(self, [script])
        #     elif "script-file" in method_config.keys():
        #         script = self.read_text_file(method_config["script-file"])
        #         m = interpreter(self, [script])
        #     else:
        #         m = None
        #         debug("Invalid configuration description for method {}".format(k))
        #     if m is not None:
        #         accessor_owner.register_method(accessor_owner, m.signature, m, depth=0, overwrite=None)

    def interpret_en(self, caller, args):
        if len(args) == 0:
            return None
        text = args[0]
        if len(args) >= 2:
            safe = args[1]
        else:
            safe = True
        parser_name = "enparser"
        if parser_name not in self._modules.keys():
            enparser = importlib.import_module("enparser")
            self._modules["enparser"] = enparser
        else:
            enparser = self._modules[parser_name]
        if safe:
            tree = enparser.try_parse(text)
        else:
            tree = enparser.parse(text)
        return tree

    def external_functions(self, name):
        return self._modules[name]

    def get_external_function_accessor(self, caller, args):
        if len(args) >= 4:
            mod = args[0]
            pkg = args[1]
            print("importlib.import(", mod, ",", pkg, ")")
            self._modules[mod] = importlib.import_module(mod, pkg)
            sig = args[2]
            eq = eval(args[3])
            # if len(args) >= 4:
            #     reload = args[3]
            m = ExtensibleWrappedAccessor(caller, sig, self, eq)
            return m

    def get_bound_method_accessor(self, caller, args):
        if len(args) >= 2:
            sig = args[0]
            eq = eval(args[1])
            m = ExtensibleWrappedAccessor(caller, sig, self, eq)
            return m

    def available_methods(self, caller, who):
        if len(who) == 0:
            who = [caller]
        for w in who:
            caller.print("{}'s methods:".format(w))
            deepest = caller.deepest_stack_id(caller)
            for i in range(deepest):
                detail = []
                caller.print("Stack[{}]".format(i))
                stack = caller.get_stack(caller, i)
                for m in stack[caller.METHODS].keys():
                    detail.append(m)
                for d in sorted(detail):
                    caller.print(d)
                caller.print("")

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
                debug("ignored {}".format(a))
        return report

    def read_from_console(self, caller, prompt):
        script = input(prompt)
        null_pattern = r"^\s*$"
        m = re.match(null_pattern, script)
        if m is None:
            return script
        else:
            return ""

    def read_text_file(self, file):
        return self.N.read_text_file(None, file)

    def get_managed_classes(self):
        return self.classes

    def get_managed_objects(self):
        return self.worlds

    def contact_objects(self, caller, args):
        return self.get_managed_objects()

    def create_managed_object(self, class_sig, name):
        debug("Creating {} object named '{}'.".format(class_sig, name))
        if name in self.worlds.keys():
            debug("Name '{}' already used. pass another name".format(name))
            return
        if class_sig in self.classes.keys():
            clazz = self.classes[class_sig]
            obj = self.create_object(clazz)
            self.worlds[name] = obj
            debug("done.")
            return
        debug("Class '{}' is not managed.".format(class_sig))

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
        caller.print(text)
        if func is not None:
            caller.print(func(caller))
            # func(caller)


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
