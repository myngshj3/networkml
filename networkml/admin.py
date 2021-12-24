# -*- coding:utf-8 -*-

import sys
from server import ServerHandler, SocketConnectionBrokenError, WorkerDispacher
from generic import debug
import genericutils as GU
from armer import Armer


def parse_command(script):
    # print("parser command:", script)
    if script is None or script == "":
        return ()
    tokens = []
    null = r"^\s*(//.*|)$"
    token = r"\s*(?P<token>(\"([^\"]|\"\")*\")|[a-zA-Z0-9_!#$%&;:=\.\-\(\)\{\}\[\]\+\*]+)"
    while True:
        m, g = GU.rematch(null, script)
        if m is not None:
            break
        m, g = GU.rematch(token, script)
        if m is None:
            # print(script)
            raise Exception("command parser error.")
        tokens.append(g['token'])
        # print(g["token"])
        # script = script[len(g['token']):]
        script = script[m.span()[1]:]
    return tuple(tokens)


class Administrator(WorkerDispacher):

    def __init__(self, obj, manager, hostname, port):
        super().__init__("admin", obj, manager, hostname, port)
        super().__init__("admin", obj, manager, hostname, port)
        self._armer = Armer()

    # def organize(self):
    #     self._armer.arm_method(self._obj, "interpret", self._obj, self,
    #                            eqution=lambda ao, c, eo, ca, ea: eo.interpret(c, ca),
    #                            globally=True,
    #                            help_text="Hello",
    #                            args_validator=None)

    def interpret(self, caller, args):
        # FIXME caller should be identified.
        try:
            if len(args) >= 1:
                args = parse_command(args[0])
                command = "self._manager.{}(".format(args[0])
                for i, a in enumerate(args[1:]):
                    if i == 0:
                        command = "{}{}".format(command, a)
                    else:
                        command = "{},{}".format(command, a)
                command = "{})".format(command)
                # print(command)
                eval(command)
        except Exception as ex:
            raise ex


if __name__ == "__main__":
    args = " ".join(sys.argv[1:])
    print(parse_command(args))
