# -*- coding:utf-8 -*-

import socket
import pickle
import threading
import sys
import queue
import re
import traceback
from networkml.genericutils import *
from networkml.networkml import SpecificationWorld
from networkml.generic import debug, set_debug
from networkml import admin
import log4p


_actor = None
log = None


_command_help_text = """
available commands:
    $console> quit
    $console> exit
    $console> help
    $console> contact <contactee>
    $console> managed-objects
    $console> join <join-name> <generator-class>
    $console> plugin-reload <plugin-name>
    $console> debug True|False
"""


def interpret(S, script_sequence):
    global _actor
    global log
    if script_sequence is None or len(script_sequence) == 0:
        return True
    script_sequence = script_sequence.split("\n")
    for script in script_sequence:
        try:
            tokens = admin.parse_command(script)
        except Exception as ex:
            return ex
        if isinstance(tokens, Exception):
            print(tokens)
            continue
        # print("command:", tokens)
        if len(tokens) == 0:
            continue

        cmd = tokens[0]
        args = tokens[1:]

        if cmd in ("quit", "exit"):
            print("Good bye!")
            return Exception("Good bye")
        elif cmd == "help":
            print(_command_help_text)
            continue
        elif cmd == "managed-objects":
            print("\nManaged classes:")
            for c in S.get_managed_classes().keys():
                print("  {}".format(c))
            print("\nManaged objects:")
            for o in S.get_managed_objects().keys():
                print("  {}".format(o))
            print("\n")
            continue
        elif cmd == "nml":
            _actor = S
            continue
        elif cmd == "contact":
            if len(args) >= 1:
                member = args[0]
                if member in S.worlds.keys():
                    _actor = S.worlds[member]
                else:
                    print("Invalid contactee. See managed-objects.")
            else:
                print("Invalid contactee. See managed-objects.")
            continue
        elif cmd == "eval":
            if len(args) >= 1:
                eq = "_actor.{}({})".format(args[0], ",".join(args[1:]))
                print(eq)
                eval(eq)
            else:
                print("too few argument")
            continue
        elif cmd == 'debug':
            if len(args) >= 1:
                set_debug(bool(args[0]))
            else:
                print("Wrong argument.")
                print("See help.")
                print("")
            continue
        elif cmd == 'join':
            if len(args) >= 2:
                S.create_managed_object(args[0], args[1])
            else:
                print("Wrong argument.")
                print("See help.")
                print("")
            continue
        elif cmd == "plugin-reload":
            if len(args) == 0:
                print("select arg jumanpp|benepar")
            else:
                if args[0] == "jumanpp":
                    S.plugin_reload(args[0])
                elif args[0] == "benepar":
                    S.plugin_reload(args[0])
                else:
                    print(args[0], "is not supported.")
            continue

        S.admin_command(script)

        # callee = "S.{}(".format(cmd)
        # if len(args) > 0:
        #     callee = "{}{}".format(callee, args[0])
        #     for a in args[1:]:
        #         callee = "{}, {}".format(callee, a)
        # callee = "{})".format(callee)
        # print(callee)
        # eval(callee)

    return True


_help_text = """
usage:
    $console> python nmlserver.py [-config config_file]
"""


def main(args):
    if len(args) == 1:
        config = read_json("nmlserver.conf")
    elif len(args) == 1 and args[1] == "-help":
        global _help_text
        print(_help_text)
        return
    elif len(args) == 3 and args[1] == "-config":
        config = read_json(args[2])
    else:
        print("args", args[1:], "ignored.")
        config = read_json("nmlserver.conf")

    # construct initial network
    networkml_config = config['networkml-config']
    server_config = config['nmlserver-config']
    global log
    logger = log4p.GetLogger(logger_name=__name__, config=server_config['log-config'])
    log = logger.logger
    # apply config to environment.
    if "debug" in server_config.keys():
        set_debug(server_config['debug'])

    S = SpecificationWorld(None, networkml_config)
    S.setup()
    if "default-model" in server_config.keys():
        S.N.load(S, server_config['default-model'])
    S.start_server()  # async=server_config["async"])

    # main loop
    print("NetworkML Start!!!")
    print("")
    if server_config["use-script"] and "initial-script" in server_config.keys():
        with open(server_config["initial-script"], "r") as f:
            try:
                rtn = interpret(S, f.read())
                if isinstance(rtn, Exception):
                    print(rtn)
                    S.finalize()

            except Exception as ex:
                if server_config["traceback"]:
                    traceback.format_exc()
                else:
                    print(ex)

    if not server_config["auto-quit"]:
        while True:
            try:
                # if not null_input:
                #     S.help(S, ())
                script = input(server_config["console-prompt"])
                rtn = interpret(S, script)
                if isinstance(rtn, Exception):
                    print(rtn)
                    S.finalize()
                    break
                continue
            except Exception as ex:
                if server_config["traceback"]:
                    traceback.format_exc()
                else:
                    print(ex)
    print("NetworkML Finished!!!")


if __name__ == "__main__":
    main(sys.argv)
    exit()
