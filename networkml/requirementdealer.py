# -*- coding: utf-8 -*-

import re
import sys
from network import NetworkGenericWorld
from network import NetworkMethod
from generic import GenericValueHolder
from requirementparser import RequirementParser


class RequirementInterpreter:

    def __init__(self, method_owner):
        self._method_owner = method_owner
        self._parser = RequirementParser(method_owner)

    def check_syntax(self, script):
        return self._parser.check_syntax(script)

    def interpret(self, script_text):
        return self.call_impl(self._method_owner, [script_text])

    def __interpret(self, script_text):
        try:
            requirements = self._parser.parse_script(script_text)
            if type(requirements) is not list:
                return None
            for req in requirements:
                print("requirement:")
                print(req)
                print("")
            return requirements
        except Exception as ex:
            print("RequirementParserError:", ex)
        finally:
            pass

    def call_impl(self, caller, args, **kwargs):
        # caller = args[0]
        if len(args) == 0:
            print("no argument given")
        elif len(args) > 1:
            print("too many arguments. {} expected, but {} got.".format(1, 2))
        else:
            input_text = args[0]
            p = r"\s*(\-f\s+(?P<file>[a-zA-Z0-9_]+[a-zA-Z0-9_\-\.]*)|(?P<requirements>.*))\s*"
            m = re.match(p, input_text)
            if m is None:
                print("invalid input:{}".format(input_text))
            else:
                dic = m.groupdict()
                if dic['file'] is not None and dic['file'] != "":
                    with open(dic['file'], "r") as f:
                        input_text = f.read()
                elif dic['requirements'] != "":
                    input_text = dic['requirements']
                else:
                    print("error")
                    return None
                return self.__interpret(input_text)

    def args_impl(self, caller, args, **kwargs):
        new_args = []
        for a in args:
            if isinstance(a, GenericValueHolder):
                new_args.append(a.value)
            else:
                new_args.append(a)
        return new_args


class RequirementDealer:

    def __init__(self, owner, signature, super_class=None):
        self._interp = RequirementInterpreter(self)

    def interp(self) -> RequirementInterpreter:
        return self._interp

    def main_loop(self, caller, args):
        print("main_loop")
        quit_patter = r"\s*(quit|exit)\s*"
        while True:
            try:
                text = input("$mediator> ")
                m = re.match(quit_patter, text)
                if m is not None:
                    break
                R = self._interp.interpret(text)
            except Exception as ex:
                print(ex)
        print("exit main_loop")


def main(args):
    program = args[0]
    # parse args
    args = args[1:]
    ignore_option = False
    files = []
    tb = False
    aq = False
    es = True
    for arg in args:
        if len(arg) == 0:
            print("brank argument ignored")
            continue
        elif arg == "--":
            ignore_option = True
            continue
        elif "-" == arg[0]:
            if arg == "-tb":
                tb = True
            elif arg == "-aq":
                aq = True
            elif arg == "-es":
                es = True
            else:
                print("option {} ignored".format(arg))
        elif "--" == arg[0:2]:
            if arg == "--traceback":
                tb = True
            elif arg == "--autoquit":
                aq = True
            elif arg == "--enable-stack":
                es = True
            else:
                print("option {} ignored".format(arg))
        else:
            pass

    # construct initial network
    D = RequirementDealer(None, "NetworkML Requirement Dealer")

    # main loop
    print("NetworkML requirement Dealer Start!!!")
    D.main_loop(D, "-f")
    print("NetworkML requirement Dealer Finished!!!")


if __name__ == "__main__":
    main(sys.argv)
