# -*- coding:utf-8 -*-

import os
import socket
import pickle
import threading
import sys
import queue
import re
import traceback
import networkml.genericutils as GU
from networkml.networkml import SpecificationWorld


_command_help_text = """
available commands:
    $console> quit
    $console> exit
    $console> help
    $console> managed-objects
    $console> join <join-name> <generator-class>
    $console> reload
"""


def interpret(S, script):
    if script is None or len(script) == 0:
        return True
    p = r"^\s*(?P<command>[a-zA-Z0-9_\-]+)(|\s+(?P<arg1>[a-zA-Z]+[a-zA-Z0-9\.\-\_]*))(|\s+(?P<arg2>[a-zA-Z]+[a-zA-Z0-9\.\-\_]*))\s*$"
    m, g = GU.rematch(p, script)
    if m is None:
        return True
    elif g['command'] in ("quit", "exit"):
        print("Good bye!")
        return False
    elif g['command'] == "help":
        print(_command_help_text)
        return True
    elif g['command'] == "managed-objects":
        print("\nManaged classes:")
        for c in S.get_managed_classes().keys():
            print("  ", c)
        print("\nManaged objects:")
        for o in S.get_managed_objects().keys():
            print("  ", o)
        print("\n")
        return True
    elif g['command'] == 'join':
        if g['arg1'] == "" or g['arg2'] == "":
            print("Wrong argument.")
            print("See help.")
            print("")
        else:
            S.create_managed_object(g['arg2'], g['arg1'])
    elif g['command'] == "reload":
        S.N.reload_settings()
    else:
        print("command not found.", g['command'])
    return True


_help_text = """
usage:
    $console> python nmlserver.py [-config config_file]
"""


def main():
    home_dir = os.getenv("NMLSERVER_HOME")
    if home_dir is None:
        config_file = "nmlserver.conf"
    else:
        config_file = home_dir + "/" + "nmlserver.conf"
    config = GU.read_json(config_file)

    # construct initial network
    networkml_config = config['networkml-config']
    server_config = config['nmlserver-config']
    S = SpecificationWorld(None, networkml_config)
    if "default-model" in server_config.keys():
        S.N.load(S, server_config['default-model'])
    S.start_server()

    # main loop
    print("NetworkML Start!!!")
    print("")
    while True:
        try:
            # if not null_input:
            #     S.help(S, ())
            script = input(server_config["console-prompt"])
            if not interpret(S, script):
                S.finalize()
                break

            continue
        except Exception as ex:
            if server_config["traceback"]:
                print(traceback.format_exc())
            else:
                print(ex)
    print("NetworkML Finished!!!")


if __name__ == "__main__":
    main()
