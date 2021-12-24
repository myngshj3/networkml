# -*- coding: utf-8 -*-


def get_interpreter(owner, generator, manager):
    from networkml.interpreter import NetworkInterpreter
    interp = NetworkInterpreter(owner)
    return interp


def arm_interpreter(owner):
    from networkml.interpreter import NetworkInterpreter
    interp = NetworkInterpreter(owner)
    owner.register_method(owner, interp.signature, interp, depth=0, overwrite=None)
