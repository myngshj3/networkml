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
from enum import Enum
from networkml.network import ExtensibleWrappedAccessor
from networkml.generic import debug, is_debug_mode
import networkml.genericutils as GU
from networkml import config as LOG
import log4p
log = None  # logger.logger


_armer = None


def get_armer():
    global _armer
    if _armer is None:
        _armer = Armer()
    return _armer


class Armer:

    log = None  # logger.logger

    def __init__(self):
        logger = log4p.GetLogger(logger_name=__name__, config=LOG.get_log_config())
        self._log = logger.logger
        self._modules = {}
        self._conf = GU.read_json("arm.conf")

    def arm_method(self, instance, generator, manager, config):
        # construct self
        interpreter = instance.get_method("interpret")
        for k in config.keys():
            method_config = config[k]
            globally = method_config["globally"]
            if "equation" in method_config.keys():
                eqn = method_config["equation"]
                eqn = eval(eqn)
                help_text = method_config["help-text"]
                m = ExtensibleWrappedAccessor(instance, k, manager, eqn,
                                              help_text=help_text,
                                              globally=globally)
            elif "script" in method_config.keys():
                script = method_config["script"]
                m = interpreter(self, [script])
            elif "script-file" in method_config.keys():
                with open(method_config["script-file"]) as f:
                    script = f.read()
                m = interpreter(self, [script])
            else:
                m = None
                debug("Invalid configuration description for method {}".format(k))
            if m is not None:
                instance.declare_method(m, globally=globally)

    def arm_methods(self, instance, generator, manager):
        for p in self._conf.keys():
            m, g = GU.rematch(p, instance.signature)
            if m is not None:
                conf = self._conf[p]
                self.arm_method(instance, generator, manager, conf)
                return

    def plugin_load(self, mod_name):
        self.log("loading module {}...".format(mod_name))
        try:
            mod = importlib.import_module(mod_name)
            self._modules[mod] = {}
            self._modules[mod]["module"] = mod
            self._modules[mod]["functions"] = {}
            self._modules[mod]["classes"] = {}
            self.log.info("plugin successfully loaded.")
        except Exception as ex:
            self.log.error(str(ex))


def main(args):
    pass


if __name__ == "__main__":
    main(sys.argv)
