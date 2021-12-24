# -*- coding: utf-8 -*-

import os
import re
from enum import Enum
from networkml.error import NetworkError, NetworkNotImplementationError
from networkml import config
import log4p


_debug = True
_traceback = True
_print_info = True
_print_fatal = True


def is_debug_mode():
    return _debug


def set_debug(flag):
    global _debug
    _debug = flag


def is_traceback():
    return _traceback


def set_traceback(flag):
    global _traceback
    _traceback = flag


def debug(*args):
    global _debug
    if _debug:
        msg = args[0]
        for a in args[1:]:
            msg = "{} {}".format(msg, a)
        print(msg)


def print_debug(*args):
    global _debug
    if _debug:
        msg = args[0]
        for a in args[1:]:
            msg = "{} {}".format(msg, a)
        print(msg)


def print_info(*args):
    global _print_info
    if _debug:
        msg = args[0]
        for a in args[1:]:
            msg = "{} {}".format(msg, a)
        print(msg)


def print_fatal(*args):
    global _print_fatal
    if _debug:
        msg = args[0]
        for a in args[1:]:
            msg = "{} {}".format(msg, a)
        print(msg)


class Generic:
    pass


class GenericCallable(Generic):

    def __call__(self, *args, **kwargs):
        pass


class Comparator(Generic):
    def __init__(self):
        super().__init__()
        pass

    def ordered(self, l, r):
        if l < r:
            return True
        else:
            return False

    def equivalent(self, l, r):
        if self.ordered(l, r) and self.ordered(r, l):
            return True
        else:
            return False

    def matches(self, left, right):
        if type(left) is str and type(right) is REPattern:
            return right.matches(left)

    def equals(self, left, right):
        if (type(left) is int or type(left) is float) and (type(right) is int or type(right) is float):
            return left == right
        elif type(left) is bool and type(right) is bool:
            return left == right
        elif type(left) is str and type(right) is str:
            return left == right
        else:
            raise NetworkError("uncomparable operand(s).")

    def different(self, left, right):
        if type(left) in (int, float) and type(right) in (int, float):
            return left != right
        elif type(left) is bool and type(right) is bool:
            return left != right
        elif type(left) is str and type(right) is str:
            return left != right
        else:
            raise NetworkError("uncomparable operand(s).")

    def less_than(self, left, right):
        if type(left) in (int, float) and type(right) in (int, float):
            return left < right
        elif type(left) is bool and type(right) is bool:
            return left < right
        elif type(left) is str and type(right) is str:
            return left < right
        else:
            raise NetworkError("uncomparable operand(s).")

    def less_or_equal(self, left, right):
        if type(left) in (int, float) and type(right) in (int, float):
            return left <= right
        elif type(left) is bool and type(right) is bool:
            return left <= right
        elif type(left) is str and type(right) is str:
            return left <= right
        else:
            raise NetworkError("uncomparable operand(s).")

    def greater_than(self, left, right):
        if type(left) in (int, float) and type(right) in (int, float):
            return left > right
        elif type(left) is bool and type(right) is bool:
            return left > right
        elif type(left) is str and type(right) is str:
            return left > right
        else:
            raise NetworkError("uncomparable operand(s).")

    def greater_or_equal(self, left, right):
        if type(left) in (int, float) and type(right) in (int, float):
            return left >= right
        elif type(left) is bool and type(right) is bool:
            return left >= right
        elif type(left) is str and type(right) is str:
            return left >= right
        else:
            raise NetworkError("uncomparable operand(s).")


class REPattern(Generic):
    def __init__(self, pattern: str):
        self._last_matches = None
        self._pattern = pattern

    @property
    def pattern(self) -> str:
        return self._pattern

    def matches(self, target: str):
        self._last_matches = re.match(self.pattern, target)
        return self._last_matches is not None

    def groupdict(self):
        if self._last_matches is None:
            return None
        else:
            return self._last_matches.groupdict()

    def __repr__(self):
        return "{}".format(self.pattern)


class GenericValueHolder(Generic):

    @property
    def value(self):
        raise NetworkNotImplementationError("{}.value not implemented".format(self))

    def __repr__(self):
        return "{}".format(self.value)


class ValueHolder(GenericValueHolder):

    def __init__(self):
        super().__init__()


class GenericComponent(Generic):

    _log = log4p.GetLogger(logger_name=__name__, config=config.get_log_config()).logger

    def __init__(self, owner):
        self._owner = owner

    @property
    def owner(self):
        return self._owner

    def set_owner(self, owner):
        self._owner = owner

    @property
    def log(self):
        return self._log


class GenericValidator(Generic):

    def reset_evaluation_policy(self):
        pass

    def validate(self, evaluatee):
        pass

    def unary_validate(self, evaluatee):
        pass

    def binary_validate(self, l, r):
        pass

    def validate_left(self, evaluatee):
        pass

    def validate_right(self, evaluatee):
        pass

    def validate_tagged_data(self, validatee, dic: dict):
        pass

    def validate_as_var(self, validatee):
        pass


class GenericEvaluatee(Generic):

    def set_validator(self, validtor):
        pass

    def reset_validator(self):
        pass

    @property
    def validator(self):
        return None

    @property
    def value(self):
        return None

    def evaluate(self, caller):
        return None


class GenericValidatorParam(Enum):

    # Validation kinds
    VALIDATE_NOTHING = "none"
    VALIDATE_AS_TAG = "tag"
    VALIDATE_AS_VARABLE = "var"

    # Exception handling policy
    FeedbackAnyException = "feedback any exception"
    ReportExceptionReasons = "report exception reasons"


class GenericUnaryEvaluatee(GenericEvaluatee):

    @property
    def expr(self):
        return None


class GenericBinaryEvaluatee(GenericEvaluatee):

    @property
    def l(self):
        return None

    @property
    def r(self):
        return None


class GenericDescription:

    def __init__(self, name, is_symbol=False):
        self._name = name
        self._is_symbol = is_symbol

    @property
    def name(self):
        return self._name

    @property
    def is_symbol(self):
        return self._is_symbol

    def __repr__(self):
        if self.is_symbol:
            return "{} '{}'".format("symbol ", self.name)
        else:
            return "{} '{}'".format("description ", self.name)
