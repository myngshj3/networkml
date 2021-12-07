# -*- coding: utf-8 -*-

import re
import ply.lex as lex
import ply.yacc as yacc
import sys
import traceback
import networkx as nx
import openpyxl
import os
import json
import sys
import inspect
from enum import Enum
from networkml.error import NetworkError, NetworkMethodError, NetworkParseError, NetworkNotImplementationError
from networkml.error import NetworkReferenceError
from networkml.generic import GenericCallable, GenericComponent, GenericValueHolder, Comparator, REPattern
from networkml.generic import GenericValidator, GenericDescription
import networkml.genericutils as GU
from networkml.validator import GenericEvaluatee, BinaryEvaluatee, UnaryEvaluatee, GenericValidatorParam, TrueEvaluatee


class NetworkComponent(GenericComponent):

    def __init__(self, owner, **kwargs):
        super().__init__(owner)


class NetworkReturnValue(GenericValueHolder):

    def __init__(self, value, success=True, reasons=None, cancel=False):
        self._value = value
        self._success = success
        self._reasons = reasons
        self._cancel = cancel

    @property
    def value(self):
        return self._value

    @property
    def fail(self):
        return not self._success

    @property
    def success(self):
        return self._success

    @property
    def reasons(self):
        return self._reasons

    @property
    def cancel(self):
        return self._cancel

    def __repr__(self):
        repr = "request success:{}, cancel proceed:{}, reason why:{},\n".format(self.success, self.cancel, self.reasons)
        if type(self.value) is list:
            repr = "{}value:[".format(repr)
            for e in self.value:
                repr = "{}\n{}".format(repr, e)
            repr = "{}]".format(repr)
            pass
        else:
            repr = "{}value:{}".format(repr, self.value)
        return repr


class DefaultSorter:
    def __init__(self, sortee):
        super().__init__()
        self._sortee = sortee
        self._default_comparator = Comparator()

    @property
    def sortee(self):
        return self._sortee

    def minimum(self, sortee, comparator: Comparator = None):
        if comparator is None:
            comparator = self._default_comparator
        m = sortee[0]
        idx = 0
        for i in range(1, len(sortee)):
            if comparator.ordered(sortee[i], m):
                m = sortee[i]
                idx = i
        return m, idx

    def sort(self, comparator: Comparator = None):
        if comparator is None:
            comparator = self._default_comparator
        result = []
        target = self.sortee.copy()
        while len(target) != 0:
            m, idx = self.minimum(target, comparator)
            target.pop(idx)
            result.append(m)
        return result


class Literal:
    def __init__(self, value):
        super().__init__()
        self._value = value

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return "{}".format(self._value)


class Interval:
    def __init__(self, start: int, end=None):
        if end is None:
            self._start = start
            self._end = end
        else:
            if start < end:
                self._start = start
                self._end = end
            else:
                self._start = end
                self._end = start

    @property
    def infinte(self) -> bool:
        return self._end is None

    @property
    def start(self) -> int:
        return self._start

    @property
    def end(self):
        return self._end

    def minimum(self):
        return self.start

    def maximum(self):
        return self.end

    def infinitize(self):
        self._end = None

    def contains(self, n):
        if n < self._start:
            return False
        elif self.infinte:
            return True
        elif self._end < n:
            return False
        return True

    def term(self) -> str:
        return self.__repr__()

    def __repr__(self):
        if self.infinte:
            m = ""
        else:
            m = self.end
        return "{}..{}".format(self.start, m)


class Numberset:
    def __init__(self, *numbers):
        self._infinite = False
        self._intervals = []
        for n in numbers:
            self.add_number(n)

    @property
    def intervals(self) -> list:
        return self._intervals

    @property
    def infinite(self) -> bool:
        for i in self.intervals:
            if i.infinte:
                return True
        return False

    def infinitize(self):
        if self.infinite:
            return
        m = None
        for i in self._intervals:
            if m is None:
                m = i
            else:
                if m.maximum < i.maximum:
                    m = i
        if m is None:
            self.add_interval(Interval(1, None))
        else:
            m.infinitize()

    def add_number(self, n: int):
        for i in self._intervals:
            if i.contains(n):
                return
        self._intervals.append(Interval(n, n))

    def add_interval(self, i: Interval):
        removal = []
        start_hook = None
        end_hook = None
        for it in self._intervals:
            if it.start <= i.start and i.end <= it.end:
                return
            elif i.start <= it.start and it.end <= i.end:
                removal.append(it)
            elif it.start < i.start and it.end < i.end:
                start_hook = it
            elif i.start < it.start and i.end < it.end:
                end_hook = it
        for r in removal:
            self._intervals.remove(r)
        if start_hook is None and end_hook is None:
            self._intervals.append(i)
        elif start_hook is not None and end_hook is None:
            new_start = start_hook.start
            new_end = i.end
            new_interval = Interval(new_start, new_end)
            self._intervals.remove(start_hook)
            self._intervals.append(new_interval)
        elif start_hook is None and end_hook is not None:
            new_start = i.start
            new_end = end_hook.end
            new_interval = Interval(new_start, new_end)
            self._intervals.remove(start_hook)
            self._intervals.append(new_interval)

    @property
    def minimum(self):
        if self.infinite:
            return 1
        m = None
        for i in self._intervals:
            if m is None:
                m = i.start
            elif i.start < m:
                m = i.start
        return m

    @property
    def maximum(self):
        if self.infinite:
            return None
        m = None
        for i in self._intervals:
            if m is None:
                m = i.end
            elif m < i.end:
                m = i.end
        return m

    def contains(self, n: int):
        for i in self._intervals:
            if i.contains(n):
                return True
        return False

    def succ(self, n):
        if n == self.maximum:
            return None
        m = n+1
        while not self.contains(m):
            m += 1
        return m

    def term(self) -> str:
        return self.__repr__()

    def __repr__(self):
        series = None
        for i in self._intervals:
            if series is None:
                series = "{}".format(i)
            else:
                series = "{},{}".format(series, i)
        return "{" + series + "}"


class NumbersetOperator:
    def __init__(self):
        pass

    def multiply(self, N: Numberset, x) -> Numberset:
        new_N = None
        for i in N.intervals:
            new_i = Interval(i.start * x, i.end.x)
            if new_N is None:
                new_N = Numberset(new_i.start)
            new_N.add_interval(new_i)
        return new_N

    def product(self, N: Numberset, M: Numberset):
        new_N = None
        for n in N.intervals:
            for m in M.intervals:
                new_i = Interval(n.start * m.start, n.end * m.end)
                if new_N is None:
                    new_N = Numberset(new_i.start)
                new_N.add_interval(new_i)
        return new_N


class CommandOption:

    def __init__(self, name: str, value=None, has_assignee=False, symbolic_assignee=False):
        self._name = name
        self._value = value
        self._has_assignee = has_assignee
        self._symbolic_assignee = symbolic_assignee

    @property
    def name(self):
        return self._name.replace("-", "")

    @property
    def value(self):
        return self._value

    @property
    def has_assignee(self):
        return self._has_assignee

    @property
    def symbolic_assignee(self):
        return self._symbolic_assignee

    def parse_value(self):
        pattern = r"[a-z]+=(?P<symbol>[a-z]+)|(?P<number>[0-9]+)|(?P<numberset>\{(\d+(,\d+)+)\})|(?P<anynumber>\{\d+\.\.\})"
        m = re.search(pattern, self.value)
        if m:
            dic = m.groupdict()
            if "symbol" in dic.keys():
                self._value = dic["symbol"]
            elif "number" in dic.keys():
                self._value = int(dic["number"])
            elif "numberset" in dic.keys():
                nums = dic["numberset"][1:len(dic["numberset"])-1].split(",")
                N = []
                for n in nums:
                    N.append(int(n))
                self._value = Numberset(N)
            elif "anynumber" in dic.keys():
                self._value = Numberset("*")
            else:
                raise NetworkError("unknown pattern:{}".format(self.value))
            pass
        else:
            raise NetworkError("unrecognized pattern:{}".format(self.value))

    def __repr__(self):
        if self.has_assignee:
            return "{}={}".format(self._name, self._value)
        else:
            return "{}".format(self._name)


class SimpleReach:
    def __init__(self, forward: bool, edge_specs: GenericEvaluatee, node_specs: GenericEvaluatee):
        super().__init__()
        self._forward = forward
        self._edge_specs: GenericEvaluatee = edge_specs
        self._node_specs: GenericEvaluatee = node_specs

    @property
    def forward(self) -> bool:
        return self._forward

    @property
    def edge_specs(self) -> GenericEvaluatee:
        return self._edge_specs

    @property
    def node_specs(self) -> GenericEvaluatee:
        return self._node_specs

    def term(self) -> str:
        return self.__repr__()

    def __repr__(self):
        if self.forward:
            outbound = ">"
            inbound = ""
        else:
            outbound = ""
            inbound = "<"
        return "{}--[{}]--{}[{}]".format(inbound, self.edge_specs, outbound, self.node_specs)


class ReachNetwork:
    def __init__(self, forward: bool, numbers: Numberset, reach: SimpleReach):
        self._forward = forward
        self._numbers = numbers
        self._reach = reach

    @property
    def numbers(self) -> Numberset:
        return self._numbers

    @property
    def reach(self) -> SimpleReach:
        return self._reach

    @property
    def forward(self) -> bool:
        return self._forward

    def term(self) -> str:
        return self.__repr__()

    def __repr__(self):
        return "({}){}".format(self.reach, self.numbers)


class ConstructiveReachNetwork:
    def __init__(self, quantifier: Numberset, l, r=None, atomic: bool = False):
        self._quantifier = quantifier
        self._reaches = [l, r]
        self._atomic = atomic

    @property
    def quantifier(self) -> Numberset:
        return self._quantifier

    @property
    def reaches(self):
        return self._reaches

    @property
    def atomic(self) -> bool:
        return self._atomic

    @property
    def left(self):
        return self._reaches[0]

    @property
    def right(self):
        return self._reaches[1]

    def multiply(self, numbers: Numberset):
        operator = NumbersetOperator()
        self._quantifier = operator.product(self._quantifier, numbers)

    def serialize_left(self, most_left):
        if self.atomic:
            left: SimpleReach = self.left
            edge_connection = [most_left, left.edge_specs, left.node_specs]
            right_node_specs = left.node_specs
        else:
            edge_connection, right_node_specs = self.left.serialize_left(most_left)
        return edge_connection, right_node_specs

    def serialize_right(self, most_left):
        if self.right is None:
            return None, None
        if self.atomic:
            right: SimpleReach = self.right
            edge_connection = [most_left, right.edge_specs, right.node_specs]
            right_node_specs = right.node_specs
        else:
            edge_connection, right_node_specs = self.right.serialize_right(most_left)
        return edge_connection, right_node_specs

    def serialize(self, most_left):
        if self.atomic:
            left: SimpleReach = self.left
            edge_connection = [most_left, left.edge_specs, left.node_specs, self.quantifier]
            return edge_connection, left.node_specs
        else:
            left_edge_connection, left_right_node_specs = self.left.serialize(most_left)
            if self.right is None:
                return left_edge_connection
            else:
                right_edge_connection, right_right_node_spec = self.right.serialize(left_right_node_specs)
                return [left_edge_connection, right_edge_connection, self.quantifier], right_right_node_spec

    def term(self) -> str:
        return self.__repr__()

    def __repr__(self):
        if self.reaches[1] is None:
            return "({}){}".format(self.reaches[0], self.quantifier)
        else:
            return "(({}){}){}".format(self.reaches[0], self.reaches[1], self.quantifier)


class ReachNetworkConstructor:
    def __init__(self):
        pass

    def simple_reach(self, forward: bool, edge_specs: GenericEvaluatee, node_specs: GenericEvaluatee, numbers: Numberset):
        simple = SimpleReach(forward, edge_specs, node_specs)
        n = ConstructiveReachNetwork(numbers, simple, atomic=True)
        return n

    def extend(self, l: ConstructiveReachNetwork, r: ConstructiveReachNetwork, quantifier: Numberset):
        n = ConstructiveReachNetwork(quantifier, l, r)
        return n

    def multiply(self, n: ConstructiveReachNetwork, q: Numberset):
        n.multiply(q)
        return n


class ReachabilitySpecification(GenericComponent):

    # Constants
    SRC_SPEC = "src-spec"
    EDGE_SPEC = "edge-spec"
    DST_SPEC = "dst-spec"
    QUANTIFIER = "quantifier"
    DEPTHS = "depths"
    SRC_NODES = "src-nodes"
    LOOPBACK_NODES = "loopback-nodes"
    SRC_REACHABLE = "src-reachable"
    DST_NODES = "dst-nodes"
    DST_REACHABLE = "dst-reachable"

    def __init__(self, owner, node_specs: GenericEvaluatee):
        super().__init__(owner)
        self._node_specs = node_specs
        self._reaches = None
        self._sentence = None
        self._edge_dict = None
        self._serialization = None

    @property
    def serialization(self):
        return self._serialization

    @property
    def edge_dict(self):
        return self._edge_dict

    @edge_dict.setter
    def edge_dict(self, dic):
        self._edge_dict = dic

    @property
    def sentence(self) -> str:
        return self._sentence

    @sentence.setter
    def sentence(self, s):
        self._sentence = s

    def set_reaches(self, reaches: ConstructiveReachNetwork):
        self._reaches = reaches

    def serialize(self):
        if self.reaches is not None:
            edge_connection, _ = self.reaches.serialize(self.node_specs)
            self._serialization = edge_connection
            return edge_connection
            # print(edge_connection)

    def edge_dictionary(self, dic, c, binary_path, order):
        idx = binary_path.copy()
        idx.append(order)
        if len(c) == 4:  # simple edge
            src_spec = c[0]
            edge_spec = c[1]
            dst_spec = c[2]
            quantifier = c[3]
            index = "{}".format(idx[0])
            for i in idx[1:]:
                index = "{}.{}".format(index, i)
            dic[index] = {self.SRC_SPEC: src_spec,
                          self.EDGE_SPEC: edge_spec,
                          self.DST_SPEC: dst_spec,
                          self.QUANTIFIER: quantifier}
        else:  # compound:
            for i, d in enumerate(c[:len(c)-1]):
                self.edge_dictionary(dic, d, idx, i+1)
        self._edge_dict = dic

    @property
    def node_specs(self) -> GenericEvaluatee:
        return self._node_specs

    @property
    def reaches(self) -> ConstructiveReachNetwork:
        return self._reaches

    @property
    def outbound(self) -> bool:
        if self._reaches is None:
            return False
        elif self._reaches.forward:
            return True
        else:
            return False

    @property
    def inbound(self) -> bool:
        if self._reaches is None:
            return False
        elif self._reaches.forward:
            return False
        else:
            return True

    def term(self) -> str:
        return self.__repr__()

    def __repr__(self):
        return "[{}]{}".format(self.node_specs, self.reaches)

    @property
    def value(self):
        return True


class NetworkResolver(NetworkComponent):

    def __init__(self, owner):
        super().__init__(owner)

    def get_method(self, caller, sig):
        raise NetworkNotImplementationError("get_method not implemented")


class NetworkArithmeticResolver(NetworkResolver):

    ATOMIC_RESOLVER = [(int, lambda x: x),
                       (bool, lambda x: x),
                       (str, lambda x: x),
                       (bool, lambda x: x)]
    ARITHMETIC_RESOLVERS = {
        "+": lambda c, a: a[0]+a[1],
        "-": lambda c, a: a[0]-a[1],
        "*": lambda c, a: a[0]*a[1],
        "%": lambda c, a: a[0]%a[1]
    }

    def __init__(self, owner):
        super().__init__(owner)

    def get_method(self, caller, sig):
        if sig in self.ARITHMETIC_RESOLVERS.keys():
            return self.ARITHMETIC_RESOLVERS[sig]
        return None

    def resolve_value(self, value):
        for r in self.ATOMIC_RESOLVER:
            if type(value) is r[0]:
                return r[1](value)


class NetworkResolverManager(NetworkResolver):

    RESOLVERS = []

    def __init__(self, owner):
        super().__init__(owner)

    def resolve_value(self, value):
        for r in self.RESOLVERS:
            if r.supported(value):
                return r.resolve_value(value)

    def append_resolver(self, resolver):
        self.RESOLVERS.append(resolver)


class NetworkSerializer:

    @property
    def opened(self):
        raise NetworkNotImplementationError("{}".format(self))

    def serialize(self, obj):
        raise NetworkNotImplementationError("{}".format(self))

    def deserialize(self):
        raise NetworkNotImplementationError("{}".format(self))

    def open(self, for_read=True, for_write=False):
        raise NetworkNotImplementationError("{}".format(self))

    def close(self):
        raise NetworkNotImplementationError("{}".format(self))


class NetworkTextSerializer(NetworkSerializer):

    def __init__(self, filename):
        self._filename = filename
        self._mode = None
        self._opened = False
        self._f = None

    @property
    def filename(self):
        return self._filename

    @property
    def opened(self):
        return self._opened

    def serialize(self, obj):
        if self.opened and "w" in self._mode:
            self._f.write(obj)
        else:
            raise NetworkError("Invalid attempt for srialization")

    def deserialize(self):
        if self.opened and "r" in self._mode:
            return self._f.read()
        else:
            raise NetworkError("Invalid attempt for desrialization")

    def open(self, for_read=True, for_write=False):
        try:
            mode = ""
            if for_read:
                mode = "{}{}".format(mode, "r")
            if for_write:
                mode = "{}{}".format(mode, "w")
            if mode == "":
                raise NetworkError("Invalid attempt with options:{}".format(mode))
            self._opened = True
            self._f = open(self.filename, mode)
            self._mode = mode
        except Exception as ex:
            self._opened = False
            raise NetworkError("file {} open error.".format(self.filename))
        finally:
            pass

    def close(self):
        self._f = None
        self._opened = False


class NetworkDocumentable:

    @property
    def document(self):
        return None


class NetworkCallable(NetworkComponent, GenericCallable, NetworkDocumentable):

    Lasted = 0
    ControlBroken = 1
    ControlReturned = 2

    def __init__(self, owner, args=None, closer=False, cancel_stacking=False, safe_call=False, **kwargs):
        super().__init__(owner)
        self._args = args
        self._closer = closer
        self._cancel_stacking = cancel_stacking
        self._safe_call = safe_call

    @property
    def args(self):
        return self._args

    def set_args(self, args):
        self._args = args

    @property
    def closer(self):
        return self._closer

    @closer.setter
    def closer(self, _closer):
        self._closer = _closer

    @property
    def cancel_stacking(self):
        return self._cancel_stacking

    def set_owners(self, caller, args):
        for a in args:
            if isinstance(a, NetworkVariable):
                a.set_owner(caller)

    def callee_type(self):
        return self

    @property
    def safe_call(self):
        return self._safe_call

    def __call__(self, *args, **kwargs):
        if len(args) == 0:
            raise NetworkNotImplementationError("{}.__call__() without argument.".format(type(self)))
        caller = args[0]
        if len(args) == 1:
            args = []
        else:
            args = args[1]
        result = self.args_impl(caller, args)
        if isinstance(result, NetworkReturnValue):
            if result.fail:
                print(result.reasons)
                return result.value
            else:
                if result.cancel:
                    print(result.reasons)
                    return result.value
                else:
                    args = result.value
        else:
            args = result
        report_break_point = True
        if "report_break_point" in kwargs.keys():
            report_break_point = kwargs["report_break_point"]
        context_id = None
        if not self.cancel_stacking and not isinstance(caller, NetworkClassInstance):
            context_id = caller.push_context()
        try:
            return self.call_impl(caller, args)
        except Exception as ex:
            raise NetworkError("{}({}) call failed.".format(self, caller), ex)
        finally:
            break_info = caller.break_point
            if not self.cancel_stacking and not isinstance(caller, NetworkClassInstance):
                caller.pop_context(context_id)
            if report_break_point:
                caller.set_break_point(break_info)

    def args_impl(self, caller, args, **kwargs):
        new_args = []
        for a in args:
            if isinstance(a, NetworkCallable):
                x = a(caller)
            elif isinstance(a, GenericEvaluatee):
                x = a.evaluate(caller)
            elif isinstance(a, NetworkSymbol):
                x = a.value
            elif isinstance(a, GenericValueHolder):
                x = a.value
            else:
                x = a
            new_args.append(x)
        return new_args

    def call_impl(self, caller, args, **kwargs):
        raise NetworkNotImplementationError("{}.__call__() not implemented.".format(type(self)))


class NetworkInvoker:

    def get_method(self, caller, m):
        raise NetworkNotImplementationError("Not implemented")

    def invoke(self, sig, caller, args):
        raise NetworkNotImplementationError("Not implemented")


class HierachicalHolder(NetworkComponent):

    def __init__(self, owner):
        super().__init__(owner)
        self._member_dict = {}
        self._name_duplicated = False
        self._indices = []

    def set_owner(self, owner):
        super().set_owner(owner)
        for m in self._member_dict.values():
            m.set_owner(owner)

    @property
    def name_duplicated(self):
        return self._name_duplicated

    def append_member(self, name, member):
        if name in self._member_dict.keys():
            print("Name duplicated:{}".format(name))
            self._name_duplicated = True
        self._member_dict[name] = member

    def append_index(self, index):
        self._indices.append(index)

    def has_member(self, name):
        return name in self._member_dict.keys()

    def get_member(self, name):
        if name in self._member_dict.keys():
            return self._member_dict[name]
        else:
            return None


class NetworkDocument:

    def __init__(self, signature, description="", script="", note=""):
        self._signature = signature
        self._description = description
        self._script = script
        self._note = note
        pass

    @property
    def signature(self):
        return self._signature

    @property
    def description(self):
        return self._description

    def set_description(self, desc):
        self._description = desc

    @property
    def script(self):
        return self._script

    def set_script(self, script):
        # print(script)
        self._script = script

    @property
    def note(self):
        return self._note

    def set_note(self, note):
        self._note = note

    def analyze(self):
        pass

    def serialize(self, serializer):
        pass

    def deserialize(self, serializer):
        pass


class NetworkMethodDocument(NetworkDocument):

    def __init__(self, sig, method, *args, **kwargs):
        super().__init__(sig)
        self._method = method
        self._arg_types = []
        self._args = args
        self._kwargs = kwargs
        self._steps = []
        self._callable = True
        self._args_requirement = ""

    @property
    def args_requirement(self):
        return self._args_requirement

    def set_args_requirement(self, req):
        self._args_requirement = req

    @property
    def callable(self):
        return self._callable

    @property
    def arg_count(self):
        return len(self._arg_types)

    @property
    def arg_types(self):
        return self._arg_types

    @property
    def method(self):
        return self._method

    def analyze(self):
        # FIXME implement method analysis statement(s) here
        # argument analysis
        for a in self.method.args:
            self._arg_types.append(type(a))
        # arg name duplication
        args = []
        for a in self.method.args:
            if a not in args:
                args.append(a)
        if len(args) == len(self.method.args):
            self._callable = True
        # process information
        for i, s in enumerate(self.method.callees):
            self._steps.append((i, s.callee_type))


class NetworkProperty(NetworkComponent):

    def __init__(self, owner, name, writee=False, get_stmts=(), set_stmts=()):
        super().__init__(owner)
        self._name = name
        self._writee = writee
        self._set_stmts = set_stmts
        self._get_stmts = get_stmts

    def get(self, caller):
        rtn = None
        for s in self._get_stmts:
            rtn = s(caller)
        return rtn

    def set(self, caller, val):
        if self._writee:
            for s in self._set_stmts:
                rtn = s(caller)


class NetworkMethod(NetworkCallable):

    class BreakPointState(Enum):

        Return = "return"
        Break = "break"
        Exception = "exception"

    def __init__(self, owner, signature, args=(), stmts=(), *otherargs, **kwargs):
        super().__init__(owner, args=args, safe_call=True)
        self._signature = signature
        self._clazz = None
        self._callees = []
        self._document = NetworkMethodDocument(signature, self)
        if "lexdata" in kwargs.keys():
            self._document.set_script(kwargs["lexdata"])
        self._globally = False
        if "globally" in kwargs.keys():
            self._globally = kwargs["globally"]
        for s in stmts:
            self._callees.append(s)

    @property
    def signature(self):
        return self._signature

    @property
    def globally(self):
        return self._globally

    @property
    def is_global(self):
        return self.globally

    @property
    def clazz(self):
        if isinstance(self.owner, NetworkClassInstance):
            self._clazz = self.owner
        elif isinstance(self.owner, NetworkClass):
            self._clazz = self.owner
        else:
            self._clazz = None
        return self._clazz

    @clazz.setter
    def clazz(self, clazz):
        self._clazz = clazz

    @property
    def document(self):
        return self._document

    @property
    def callable(self):
        if self.document is None:
            return None
        else:
            return self.document.callable

    @property
    def callees(self):
        return self._callees

    def append_callee(self, callee):
        return self._callees.append(callee)

    def actual_call_impl(self, caller, args, **kwargs):
        rtn = None
        for c in self.callees:
            rtn = c(caller)
            if isinstance(rtn, NetworkError):
                print("Error Captured.")
                print(rtn)
                print("resumed")
                continue
            elif isinstance(rtn, NetworkReturnValue):
                print("Special dealing with:")
                print(rtn)
                continue
            if caller.break_point is not None:
                print("caller.break_point:", caller.break_point)
                if isinstance(rtn, NetworkReturnValue):
                    print("Exception occurred, but safely resumed.")
                    print(rtn)
                    return rtn.reasons
                elif isinstance(rtn, GenericValueHolder):
                    return rtn.value
                else:
                    return rtn
        return rtn

    def call_impl(self, caller, args, **kwargs):
        is_callable = self.callable
        if is_callable is not None and not is_callable:
            raise NetworkError("{}.{} is not in callable state.".format(self.clazz, self.signature))
        if is_callable is None:
            print("Cannot analyze argumenet for {}.{}() ".format(self.owner, self.signature))
        if self.safe_call:
            try:
                return self.actual_call_impl(caller, args)
            except Exception as ex:
                print("Internal Error occurred, but safely resumed.")
                print(ex)
                return self.actual_call_impl(caller, args)
        else:
            return self.actual_call_impl(caller, args)

    def args_impl(self, caller, args, **kwargs):
        # FIXME argument adequateness varifiable here
        # new_args = []
        if len(args) < len(self.args):
            return NetworkReturnValue(args, False, "At least {} args needed, but {} args given.".format(len(self.args), len(args)))
        args = super().args_impl(caller, args[:len(self.args)])
        for a, x in zip(self.args, args):
            caller.accessor.set(caller, a, x)
        # for a, b in zip(self.args, args[:len(self.args)]):
        #     if isinstance(b, NetworkMethodCaller):
        #         x = b(caller)
        #     elif isinstance(b, NetworkSymbol):
        #         x = b.value
        #     elif isinstance(b, GenericValueHolder):
        #         x = b.value
        #     else:
        #         x = b
        #     caller.accessor.set(caller, a, x)
        return args

    def __repr__(self):
        return "{}.{}()".format(self.clazz, self.signature)


class NetworkInstanceDocument(NetworkDocument):

    def __init__(self, sig, instance, clazz, *args, **kwargs):
        super().__init__(sig)
        self._instance = instance
        self._clazz = clazz
        self._args = args
        self._kwargs = kwargs

    @property
    def instance(self):
        return self._instance

    @property
    def clazz(self):
        return self._clazz

    def analyze(self):
        # FIXME implement method analysis statement(s) here
        # argument analysis
        pass

    def serialize(self, serializer):
        serializer.serialize(self.script)
        pass

    def deserialize(self, serializer):
        pass


class NetworkInstance(NetworkComponent, NetworkDocumentable):

    def __init__(self, clazz, _id, owner, *args, **kwargs):
        super().__init__(owner)
        self._attributes = {}
        self.set_private_attribute(self, "$self", self)
        self.set_private_attribute(self, "$owner", self.owner)
        # # FIXME lex data shouldn't be holded here.
        # lexdata = None
        # if "lexdata" in kwargs.keys():
        #     lexdata = kwargs["lexdata"]
        # self._validator = None
        if "validator" in kwargs.keys():
            self._validator = kwargs["validator"]
        self._clazz = clazz
        self._id = _id
        self._context = [{
            "vars": {},
            "methods": {},
            "classes": {},
            "break_point": None
        }]
        self._accessor = HierarchicalAccessor(self)
        self._enable_stack = False
        self._document = NetworkInstanceDocument(self.signature, self.id, self.clazz)
        # self._document.set_script(lexdata)
        # FIXME this attribute should be removed
        self._globally = False
        if "globally" in kwargs.keys():
            self._globally = kwargs["globally"]
        # FIXME deal with args

    @property
    def signature(self):
        return "{}.{}".format(self.clazz.signature, self.id)

    @property
    def id(self):
        return self._id

    def get_accessible_attribute(self, caller, name):
        if isinstance(caller, HierarchicalAccessor):
            return NetworkNothing("Access denied.")
        var = self.accessor.get(caller, name)
        if isinstance(var, NetworkNothing):
            if name in self._attributes.keys():
                return self._attributes[name]
            return NetworkNothing("{} is not accessible.".format(name))
        return var

    def set_owner(self, owner):
        self.set_owner(owner)
        self.set_private_attribute(self, "$owner", owner)

    @property
    def parent(self):
        return self.owner

    def set_parent(self, parent):
        self.set_owner(parent)

    @property
    def clazz(self):
        return self._clazz

    @property
    def globally(self):
        return self._globally

    @property
    def is_global(self):
        return self.globally

    @property
    def context(self):
        return self._context[len(self._context)-1]

    @property
    def enable_stack(self):
        return self._enable_stack

    @property
    def accessor(self):
        return self._accessor

    @property
    def validator(self):
        if self._validator is not None:
            return self._validator
        return self.owner.validator

    def set_validator(self, v):
        self._validator = v

    def set_stack_enable(self, en):
        self._enable_stack = en

    def push_context(self):
        if self.enable_stack:
            new_ctx = {
                "methods": {},
                "vars": {},
                "classes": {},
                "break_point": None
            }
            self._context.append(new_ctx)
            return len(self._context)

    def pop_context(self, context_id):
        if self.enable_stack:
            self._context = self._context[0:context_id-1]

    def has_attribute(self, name):
        for i in sorted(range(len(self._context))):
            if name in self._context[i]["vars"].keys():
                return True
        if name in self._attributes.keys():
            return True
        return False

    def get_attribute(self, name):
        for i in sorted(range(len(self._context))):
            if name in self._context[i]["vars"].keys():
                return self._context[i]["vars"][name]
        if name in self._attributes.keys():
            return self._attributes[name]
        return NetworkNothing("name")

    def set_attribute(self, name, val):
        i = len(self._context)-1
        for i in sorted(range(len(self._context)), reverse=True):
            if name in self._context[i]["vars"].keys():
                self._context[i]["vars"][name] = val
        self._context[i]["vars"][name] = val

    def set_private_attribute(self, caller, name, val):
        # FIXME well-consider implementation of secure access.
        # if self != caller and self.owner != caller:
        #     raise NetworkError("Invalid attempt to access private attribute.")
        self._attributes[name] = val

    # local variable
    def declare_var(self, var, globally=False):
        if var.globally or globally:
            self._context[0]["vars"][var.name] = var
        else:
            self.context["vars"][var.name] = var
        var.set_owner(var)

    # local method
    def declare_method(self, method, globally=False):
        if method.globally or globally:
            self._context[0]["methods"][method.signature] = method
        else:
            self.context["methods"][method.signature] = method
        method.set_owner(self)

    def declare_class(self, clazz, globally=False):
        if clazz.globally or globally:
            self._context[0]["classes"][clazz.signature] = clazz
        else:
            self.context["classes"][clazz.signature] = clazz
        clazz.set_parent(self)

    def create_class(self, signature, owner, initializer_args=()):
        if signature in self.context["classes"].keys():
            raise NetworkError("Instance {} already has named class <{}>.".format(self, signature))
        clazz = NetworkClassInstance(self, (signature, owner, initializer_args))  # local class doesn't has meta-class.
        self.declare_class(clazz)
        return clazz

    def create_method(self, signature, args, stmt):
        if signature in self.context["methods"].keys():
            raise NetworkError("Instance {} already has named method '{}'.".format(self, signature))
        m = NetworkMethod(self, (signature, args, stmt))
        self.declare_method(m)
        return m

    def get_callable_var(self, caller, sig):
        var = self.accessor.get(caller, sig)
        if isinstance(var, NetworkCallable):
            return var
        return None

    def get_method(self, caller, sig):
        # print("This method is updated for secure access.")
        if sig in self._attributes.keys():
            m = self._attributes[sig]
            if isinstance(m, NetworkMethod):
                return m
        for i in sorted(range(len(self._context))):
            context = self._context[i]
            if "methods" in context.keys():
                context = context["methods"]
                if sig in context.keys():
                    return context[sig]

        if self.clazz is not None:
            m = self.clazz.get_method(caller, sig)
            if m is not None:
                return m
        if self.owner is not None:
            return self.owner.get_method(caller, sig)
        return None

    def get_class(self, caller, sig):
        # print("This method is updated for secure access.")
        # FIXME consider class hierarchy and security
        if sig in self._attributes.keys():
            c = self._attributes[sig]
            if isinstance(c, NetworkClassInstance):
                return c
        for i in sorted(range(len(self._context))):
            context = self._context[i]
            if "classes" in context.keys():
                context = context["classes"]
                if sig in context.keys():
                    return context[sig]
        if self.clazz is not None:
            return self.clazz.get_class(caller, sig)
        return None

    def get_var(self, name, globally=True):
        print("This method is deprecated. use accessor.get() instead.")
        rtn = self.get_accessible_attribute(self, name)
        # FIXME consider class hierarchy and security
        if name in self._attributes.keys():
            v = self._attributes[name]
            if isinstance(v, NetworkVariable):
                return v
        if globally:  # searches globally
            for i in sorted(range(len(self._context))):
                context = self._context[i]
                if "vars" in context.keys():
                    context = context["vars"]
                    if name in context.keys():
                        return context[name]
        else:  # searches locally
            context = self.context
            if "vars" in context.keys():
                context = context["vars"]
                if name in context.keys():
                    return context[name]
        return None

    def set_var(self, var, globally=False):
        print("This method is deprecated. use accessor.set() instead.")
        if globally:
            self._context[0]["vars"][var.name] = var
        else:
            for i in sorted(range(len(self._context)), reverse=True):
                if var.name in self._context[i]["vars"].keys():
                    self._context[i]["vars"][var.name] = var
                    return
            self.context["vars"][var.name] = var

    @property
    def break_point(self):
        return self.context["break_point"]

    def set_break_point(self, break_info):
        self.context["break_point"] = break_info

    def managing_methods(self):
        methods = []
        for i, ctx in enumerate(self._context):
            for k in ctx["methods"].keys():
                methods.append(ctx["methods"][k])
        return methods

    def managing_vars(self):
        vars = []
        for i, ctx in enumerate(self._context):
            for k in ctx["vars"].keys():
                vars.append(ctx["vars"][k])
        return vars

    def managing_classes(self):
        classes = []
        for i, ctx in enumerate(self._context):
            for k in ctx["classes"].keys():
                classes.append(ctx["classes"][k])
        return classes

    def create_builtin_methods_wrapper(self):
        wrapper = NetworkMethodWrapper(self, self, "get_var", lambda c, arg: c.get_var(c, arg[0]), ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "get_method", lambda c, arg: c.get_method(c, arg[0]), ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "get_class", lambda c, arg: c.get_class(c, arg[0]), ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "signature", lambda c, arg: c.signature, ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "clazz", lambda c, arg: c.clazz, ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "managing_methods", lambda c, arg: c.managing_methods(), ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "managing_classes", lambda c, arg: c.managing_classes(), ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "managing_vars", lambda c, arg: c.managing_vars(), ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "managing_vars", lambda c, arg: c.managing_vars(), ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "create_class", lambda c, arg: c.create_class(), ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "create_instance", lambda c, arg: c.create_instance(), ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "document", lambda c, arg: c.document, ["m"])
        wrapper = NetworkMethodWrapper(self, self, "method_document", lambda c, arg: c.arg[0].document, ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "method_document", lambda c, arg: c.arg[0].document, ["m"])
        self.declare_method(wrapper)
        wrapper = NetworkMethodWrapper(self, self, "script", lambda c, arg: c.arg[0].script, ["m"])
        self.declare_method(wrapper)

    def stack_structure(self):
        stack_structure = ""
        for i, c in enumerate(self._context):
            vars = "vars: "
            for k in c["vars"].keys():
                vars = vars + k + ","
            methods = "methods: "
            for k in c["methods"].keys():
                methods = methods + k + ","
            classes = "classes: "
            for k in c["classes"].keys():
                classes = classes + k + ","
            stack_structure = stack_structure + "{}:[{}, {}, {}] ".format(i, vars, methods, classes)
        return stack_structure

    def __repr__(self):
        return "{}.{}".format(self.clazz.signature, self.id)


class NetworkClassInstanceDocument(NetworkDocument):

    def __init__(self, sig, instance, clazz, *args, **kwargs):
        super().__init__(sig)
        self._instance = instance
        self._clazz = clazz
        self._args = args
        self._kwargs = kwargs

    @property
    def instance(self):
        return self._instance

    @property
    def clazz(self):
        return self._clazz

    def analyze(self):
        # FIXME implement method analysis statement(s) here
        # argument analysis
        pass

    def serialize(self, serializer):
        for i in self.clazz:
            pass
        serializer.serialize(self.script)
        pass

    def deserialize(self, serializer):
        pass


class NetworkSymbol(UnaryEvaluatee):

    def __init__(self, owner, symbol):
        super().__init__(owner, symbol, symbol, as_symbol=True)
        self._symbol = symbol

    @property
    def symbol(self):
        return self._evaluatees[0]

    def set_symbol(self, sym):
        self._evaluatees[0] = sym

    def evaluate(self, caller=None):
        return super().evaluate(caller)

    def __repr__(self):
        return self.symbol


class NetworkClassInstance(NetworkInstance, NetworkCallable):

    def __init__(self, meta_clazz, signature, owner, super_class=None, **kwargs):
        self._super_class = super_class
        self._signature = signature
        super().__init__(owner, 0, meta_clazz, args=None)
        self._globally = False
        if "globally" in kwargs.keys():
            globally = kwargs["globally"]
        self._init_args = None
        if "init_args" in kwargs.keys():
            self._init_args = kwargs["init_args"]
        self._lexdata = None
        if "lexdata" in kwargs.keys():
            self._lexdata = kwargs["lexdata"]
        self._initializer = None
        self._last_instance = 0
        self._instance_ids = []
        self._document = NetworkInstanceDocument(self.signature, self.id, self.clazz)
        self._document.set_script(self._lexdata)
        # FIXME deal with init args

    @property
    def signature(self):
        return self._signature
        # return "{}.{}".format(self.clazz, self._signature)

    @property
    def clazz(self):
        return None

    @property
    def super_class(self):
        return self._super_class

    @property
    def instance_ids(self):
        return self._instance_ids

    @property
    def next_instance_id(self):
        if len(self._instance_ids) == 0:
            return 1
        return self._instance_ids[len(self._instance_ids)-1] + 1

    def init_clazz(self, initializer, method_list=()):
        self._initializer = initializer
        for e in method_list:
            self.declare_method(e)

    @property
    def globally(self):
        return self._globally

    @property
    def document(self):
        return self._document

    @property
    def is_global(self):
        return self.globally

    def push_context(self):
        raise NetworkError("NetworkClassInstance doesn't support context stack operation.")

    def pop_context(self, context_id):
        raise NetworkError("NetworkClassInstance doesn't support context stack operation.")

    def declare_var(self, var, globally=False):
        super().declare_var(var, globally=globally)

    def declare_method(self, method, globally=True):
        super().declare_method(method, globally=globally)

    def get_method(self, caller, sig):
        # FIXME consider class hierarchy and security
        m = super().get_method(caller, sig)
        if m is not None:
            return m
        if self.super_class is not None:
            m = self.super_class.get_method(caller, sig)
            if m is not None:
                return m
        elif self.owner is not None:
            return self.owner.get_method(caller, sig)
        else:
            return None

    def get_initializer(self) -> NetworkMethod:
        initializer = self._initializer
        return initializer

    def create_instance(self, _id, owner, args):
        instance = NetworkInstance(self, _id, owner, args)
        initializer: NetworkMethod = self.get_initializer()
        instance.set_stack_enable(False)
        if initializer is not None:
            initializer(instance, args)
        instance.set_stack_enable(True)
        return instance

    def release_instance(self, instance):
        if instance.clazz == self:
            self._instance_ids.remove(instance.id)
        else:
            print("Not managed object {}".format(instance))

    def call_impl(self, caller, args, **kwargs):
        self._last_instance += 1
        self._instance_ids.append(self._last_instance)
        return self.create_instance(self._last_instance, caller, args)

    def invoke(self, sig, instance, args):
        m = self.get_method(instance, sig)
        # m = self.accessor.get(instance, sig, NetworkMethod)
        # if m is None:
        #     m = instance.accessor.get(instance, sig, NetworkMethod)
        #     if m is not None:
        #         return m(instance, args)
        if m is None:
            raise NetworkError("Method {}.{} not found.".format(self.clazz.signature, sig))
        return m(instance, args)

    def __repr__(self):
        return "{}::{}: MetaClass:{}>".format(self.super_class, self.signature, self.clazz)


class NetworkClass(NetworkClassInstance):

    def __init__(self, owner, signature, super_class=None, globally=False):
        super().__init__(owner, signature, owner)
        self._super_class = super_class
        self._signature = signature
        self._globally = globally
        self._classes = {}

    @property
    def super_class(self):
        return self._super_class

    @property
    def globally(self):
        return self._globally

    @property
    def is_global(self):
        return self.globally

    @property
    def classes(self):
        return self._classes

    def create_instance(self, owner, clazz_signature, **kwargs):
        if clazz_signature in self._classes:
            raise NetworkError("class {} is already created.".format(clazz_signature))
        init_args = []
        if "init_args" in kwargs.keys():
            init_args = kwargs["init_args"]
        clazz = NetworkClassInstance(self, clazz_signature, owner, init_args=init_args)
        self.classes[clazz.signature] = clazz
        return clazz

    def __call__(self, *args, **kwargs):
        caller = args[0]
        clazz_signature = args[1]
        init_args = args[2]
        return self.create_instance(caller, clazz_signature, init_args=init_args)

    def __repr__(self):
        return "{}:{}:MetaClass".format(self.signature, self.signature)


class NetworkWritee(NetworkComponent):

    def __init__(self, owner):
        super().__init__(owner)

    def write(self, value):
        raise NetworkNotImplementationError("not implemented")


class NetworkVariable(NetworkWritee, GenericValueHolder):
    def __init__(self, owner, name, globally=False):
        super().__init__(owner)
        self._name = name
        self._value = None
        self._globally = globally

    @property
    def name(self):
        return self._name

    @property
    def globally(self):
        return self._globally

    @property
    def is_global(self):
        return self.globally

    def write(self, value):
        if self.owner is None:
            raise NetworkError("{} cannot handle writing operation.:{}={}".format(self, self.name, value))
        self._value = value

    @property
    def value(self):
        if self.owner is None:
            raise NetworkError("{} cannot resolve name. owner doesn't exist.:{}".format(self, self.name))
        else:
            return self._value

    def __repr__(self):
        return "{}".format(self._name)


class SimpleVariable(NetworkVariable):

    def __init__(self, owner, name, value, globally=False):
        super().__init__(owner, name, globally)
        self._value = value

    @property
    def value(self):
        if self.owner is None:
            print("Bug!!! value reference without declaration.")
            return self._value
        else:
            return self._value

    def write(self, value):
        self._value = value

    def __repr__(self):
        return "{}".format(self.name)


class NetworkNothing(NetworkError):

    def __init__(self, args):
        super().__init__(args)


class HierarchicalAccessor(NetworkComponent):

    def __init__(self, owner=None):
        super().__init__(owner)

    def separate_name(self, name):
        if isinstance(name, NetworkSymbol):
            name = name.symbol
        names = name.split(".")
        last_segment = names[len(names)-1]
        sympat = r"\s*(?P<symbol>(\$|)[a-zA-Z_]+([a-zAZ0-9_\$]*[a-zAZ0-9]+)*)\s*"
        m = re.match(sympat, last_segment)
        if m is None:
            raise NetworkReferenceError("Invalid reference format.{}".format(last_segment))
        last_name = m.groupdict()['symbol']
        indices_segment = last_segment[m.span()[1]:]
        indices = []
        idxpat = r"\[((?P<number>\d+)|(?P<literal>\"[^\"]+\")|(?P<symbol>[a-zA-Z_]+([a-zAZ0-9_]*[a-zAZ0-9]+)*))\]"
        while True:
            m = re.match(idxpat, indices_segment)
            if m is None:
                break
            num_idx = m.groupdict()['number']
            sym_idx = m.groupdict()['symbol']
            ltr_idx = m.groupdict()['literal']
            if num_idx is not None and num_idx != "":
                indices.append(int(num_idx))
            elif sym_idx is not None and sym_idx != "":
                indices.append(sym_idx)
            elif ltr_idx is not None and ltr_idx != "":
                indices.append(ltr_idx)
            else:
                return NetworkNothing(name)
            indices_segment = indices_segment[m.span()[1]:]
        if len(names) == 1:
            first_name = None  # last_name
            middle_names = ()
            # last_name = None
        else:
            first_name = names[0]
            middle_names = names[1:len(names)-1]
        return first_name, middle_names, last_name, indices

    def get_indexed_value(self, caller, var, indices):
        for i in indices:
            if isinstance(i, int):
                if i < 0:
                    raise NetworkReferenceError("Negative indexer {} assigned.".format(i))
                if isinstance(var, GenericValueHolder):
                    var = var.value
                if not (isinstance(var, list) or isinstance(var, tuple)):
                    raise NetworkReferenceError("Unaccessible referee {} for index {}.".format(var, i))
                var = var[i]
            elif isinstance(i, str):
                if i[0] == "\"" and i[len(i)-1] == "\"":
                    i = i[1:len(i)-1]
                    if not isinstance(var, dict):
                        raise NetworkReferenceError("Unaccessible referee {} for index {}.".format(var, i))
                    var = var[i]
                else:
                    i = self.get(caller, i, types=(int, str))
                    if type(i) is int and type(var) is list:
                        var = var[i]
                    elif type(i) is str and type(var) is dict:
                        var = var[i]
                    else:
                        raise NetworkReferenceError("Unaccessible referee {} for index {}.".format(var, i))
        return var

    def set_to_indexed_object(self, var, indices, val):
        i = indices[len(indices)-1]
        for i in indices[0:len(indices)-1]:
            if isinstance(i, int):
                if i < 0:
                    raise NetworkReferenceError("Negative indexer {} assigned.".format(i))
                if not isinstance(var, list):
                    raise NetworkReferenceError("Unaccessible referee {} for index {}.".format(var, i))
                else:
                    var = var[i]
            elif isinstance(i, str):
                if not isinstance(var, dict):
                    raise NetworkReferenceError("Unaccessible referee {} for index {}.".format(var, i))
                var = var[i]
            else:
                NetworkReferenceError("Unavailable indexer {}.".format(i))
        if isinstance(i, int):
            if i < 0:
                raise NetworkReferenceError("Negative indexer {} assigned.".format(i))
            if not isinstance(var, list):
                raise NetworkReferenceError("Unaccessible referee {} for index {}.".format(var, i))
            else:
                var[i] = val
        elif isinstance(i, str):
            if not isinstance(var, dict):
                raise NetworkReferenceError("Unaccessible referee {} for index {}.".format(var, i))
            var[i] = val
        else:
            return NetworkNothing("Unavailable indexer {}.".format(i))
        return True

    def get_named_value(self, caller, first_name, middle_names, last_name, indices):
        return self.get_named_object(caller, first_name, middle_names, last_name, indices)

    def get_named_object(self, caller, first_name, middle_names, last_name, indices):
        names = []
        if first_name is not None:
            names.append(first_name)
        names.extend(middle_names)
        if last_name is not None:
            names.append(last_name)
        obj = caller
        for i, n in enumerate(names):
            if isinstance(obj, NetworkInstance):
                if not obj.has_attribute(n):
                    symbol = self.complex_name(names, ())
                    return NetworkNothing("Couldn't access to {}.".format(symbol))
                obj = obj.get_attribute(n)
            elif isinstance(obj, dict):
                if not n in obj.keys():
                    symbol = self.complex_name(names, ())
                    return NetworkNothing("Couldn't access to {}.".format(symbol))
                obj = obj[n]
            elif i != len(names)-1:
                symbol = self.complex_name(names, ())
                return NetworkNothing("Couldn't access to {}.".format(symbol))
        for j, i in enumerate(indices):
            if isinstance(i, str):
                if i[0] == "\"" and i[len(i) - 1] == "\"":
                    i = i[1:len(i) - 1]
                    if not isinstance(obj, dict):
                        symbol = self.complex_name(names, indices[:j + 1])
                        return NetworkNothing("Couldn't access to {}.".format(symbol))
                    obj = obj[i]
                else:
                    i = self.get(caller, i, types=(int, str))
                    if type(i) is int and (type(obj) is list or type(obj) is tuple):
                        obj = obj[i]
                    elif type(i) is str and type(obj) is dict:
                        obj = obj[i]
                    else:
                        symbol = self.complex_name(names, indices[:j + 1])
                        return NetworkNothing("Couldn't access to {}.".format(symbol))
            elif type(i) is int and (isinstance(obj, list) or isinstance(obj, tuple)):
                obj = obj[i]
            else:
                symbol = self.complex_name(names, indices[:j+1])
                return NetworkNothing("Couldn't access to {}.".format(symbol))

        return obj

    def complex_name(self, names, indices):
        name = ".".join(names)
        idx = ""
        for j in indices:
            idx = "{}[{}]".format(idx, j)
        return "{}{}".format(name, idx)

    def get(self, caller, hierarchical_name, types=None):
        first_name, middle_names, last_name, indices = self.separate_name(hierarchical_name)
        rtn = self.get_named_value(caller, first_name, middle_names, last_name, indices)
        if isinstance(rtn, NetworkNothing):
            return rtn
        if not (type(types) is list or type(types) is tuple):
            available_types = [types]
        else:
            available_types = types
        for t in available_types:
            if t is None:
                return rtn
            if isinstance(rtn, t):
                return rtn
        return NetworkNothing("{} not found.".format(hierarchical_name))

    def set_named_value(self, caller, first_name, middle_names, last_name, indices, val):
        return self.set_named_object(caller, first_name, middle_names, last_name, indices, val)

    def set_named_object(self, caller, first_name, middle_names, last_name, indices, val):
        names = []
        if first_name is not None:
            names.append(first_name)
        names.extend(middle_names)
        if last_name is not None:
            names.append(last_name)
        obj = caller
        if len(indices) == 0:
            last = len(names)-1
            last_something = names[last]
        else:
            last = len(names)
            last_something = indices[len(indices)-1]
        for i, n in enumerate(names[:last]):
            if isinstance(obj, NetworkInstance):
                if not obj.has_attribute(n):
                    return NetworkNothing("Couldn't access to {}.".format(".".join(names[:i])))
                obj = obj.get_attribute(n)
            elif isinstance(obj, dict):
                if not n in obj.keys():
                    return NetworkNothing("Couldn't access to {}.".format(".".join(names[:i])))
                obj = obj[n]
            elif i != len(names):
                return NetworkNothing("Couldn't access to {}.".format(".".join(names[:i])))
        if len(indices) != 0:
            for j, i in enumerate(indices[:len(indices)-1]):
                if isinstance(i, str):
                    if i[0] == "\"" and i[len(i) - 1] == "\"":
                        i = i[1:len(i) - 1]
                        if not isinstance(obj, dict):
                            symbol = self.complex_name(names, indices[:j + 1])
                            return NetworkNothing("Couldn't access to {}.".format(symbol))
                        obj = obj[i]
                    else:
                        i = self.get(caller, i, types=(int, str))
                        if type(i) is int and (type(obj) is list or type(obj) is tuple):
                            obj = obj[i]
                        elif type(i) is str and type(obj) is dict:
                            obj = obj[i]
                        else:
                            symbol = self.complex_name(names, indices[:j + 1])
                            return NetworkNothing("Couldn't access to {}.".format(symbol))
                elif type(i) is int and (isinstance(obj, list) or isinstance(obj, tuple)):
                    obj = obj[i]
                else:
                    symbol = self.complex_name(names, indices[:j + 1])
                    return NetworkNothing("Couldn't access to {}.".format(symbol))
        if isinstance(obj, NetworkInstance):
            obj.set_attribute(last_something, val)
            return True
        i = last_something
        if isinstance(i, str):
            if last_something[0] == "\"" and i[len(i) - 1] == "\"":
                i = i[1:len(i) - 1]
                if not isinstance(obj, dict):
                    symbol = self.complex_name(names, indices)
                    return NetworkNothing("Couldn't access to {}.".format(symbol))
                obj[i] = val
            else:
                i = self.get(caller, i, types=(int, str))
                if type(i) is int and (type(obj) is list or type(obj) is tuple):
                    obj[i] = val
                elif type(i) is str and type(obj) is dict:
                    obj[i] = val
                else:
                    symbol = self.complex_name(names, indices)
                    return NetworkNothing("Couldn't access to {}.".format(symbol))
        elif isinstance(i, int):
            obj[i] = val
        else:
            symbol = self.complex_name(names, indices)
            return NetworkNothing("Couldn't access to {}.".format(symbol))
        return True

    def set(self, caller, hierarchical_name, val, value=True, method=False, clazz=False):
        first_name, middle_names, last_name, indices = self.separate_name(hierarchical_name)
        return self.set_named_value(caller, first_name, middle_names, last_name, indices, val)


class NetworkMethodCaller(NetworkCallable):

    def __init__(self, owner, hierarchy_name, args=()):
        super().__init__(owner, args=args)
        name = hierarchy_name.symbol
        self._hierarchical_name = name
        names = name.split(".")
        self._actual_caller = ".".join(names[0:len(names)-1])
        self._method_name = names[len(names)-1]
        self._is_default_method = self._method_name == name

    @property
    def hierarchical_name(self):
        return self._hierarchical_name

    @property
    def actual_caller(self):
        return self._actual_caller

    @property
    def method_name(self):
        return self._method_name

    @property
    def is_default_method(self):
        return self._is_default_method

    def call_impl(self, caller, args, **kwargs):        # acquire instance and args
        if self.is_default_method:
            holder = caller
        else:
            accessor = caller.accessor
            holder = accessor.get(caller, self.actual_caller)
        if isinstance(holder, GenericValueHolder):
            holder = holder.value
        if not isinstance(holder, NetworkInstance):
            raise NetworkError("Invalid method holder {}.".format(holder))
        m = holder.get_method(self, self.method_name)
        if m is None:
            m = holder.get_callable_var(caller, self.method_name)
            if m is None:
                return NetworkReturnValue(None, False,
                                          "Method {}.{} not found.".format(holder.signature, self.method_name))
        return m(caller, args)

    def args_impl(self, caller, args, **kwargs):
        if not isinstance(caller, NetworkInstance):
            raise NetworkError("Invalid caller {}.".format(caller))
        args = super().args_impl(caller, self.args)
        return args
        # new_args = []
        # for a in self.args:
        #     if isinstance(a, NetworkSymbol):
        #         b = a.value
        #     elif isinstance(a, GenericValueHolder):
        #         b = a.value
        #     elif isinstance(a, NetworkCallable):
        #         b = a(caller)
        #     else:
        #         b = a
        #     new_args.append(b)
        # return new_args

    def __repr__(self):
        args = ""
        if len(self.args) > 0:
            args = "{}".format(self.args[0])
            for a in self.args[1:]:
                args = "{},{}".format(args, a)
        return "{}({})".format(self.hierarchical_name, args)


class NetworkSubstituter(NetworkCallable):

    def __init__(self, owner, var, callee, globally=False):
        super().__init__(owner, cancel_stacking=True)
        self._var = var.symbol
        self._callee = callee
        self._globally = globally

    @property
    def var(self):
        return self._var

    @property
    def callee(self):
        return self._callee

    @property
    def globally(self):
        return self._globally

    def call_impl(self, caller, args, **kwargs):
        if type(self.callee) is list or type(self.callee) is tuple:
            new_args = []
            for a in self.callee:
                new_args.append(a)
            args = super().args_impl(caller, new_args)
            args = [args]
        else:
            args = super().args_impl(caller, [self.callee])
        accessor = caller.accessor
        accessor.set(caller, self.var, args[0])

    def args_impl(self, caller, args, **kwargs):
        # do nothing, since no argument preparation have to be done here.
        pass
    #     args = super().args_impl(caller, self.args)
    #     self.args[0] = args[0]
    #     return args

    def __repr__(self):
        return "{} <<- {}".format(self.var, self.callee)


class NetworkBreak(NetworkCallable):

    def __init__(self, owner):
        super().__init__(owner, closer=True)

    def call_impl(self, caller, args, **kwargs):
        caller.set_break_point("break")

    def args_impl(self, caller, args, **kwargs):
        return args

    def __repr__(self):
        return "break;"


class NetworkReturn(NetworkCallable, GenericValueHolder):

    def __init__(self, owner, callee):
        super().__init__(owner, closer=True)
        self._callee = callee

    @property
    def callee(self):
        return self._callee

    def call_impl(self, caller, args, **kwargs):
        accessor = caller.accessor
        if isinstance(self.callee, NetworkCallable):
            a = self.callee(caller)
        elif isinstance(self.callee, NetworkSymbol):
            a = accessor.get(caller, self.callee.symbol)
        elif isinstance(self.callee, GenericValueHolder):
            a = self.callee.value
        else:
            a = self.callee
        caller.set_break_point(NetworkMethod.BreakPointState.Return)
        return a

    def __repr__(self):
        return "return {};".format(self.callee)


class NetworkSequentialStatements(NetworkCallable):

    def __init__(self, owner):
        super().__init__(owner)
        self._statements = ()

    @property
    def statements(self):
        return self._statements

    def set_statements(self, stmt):
        self._statements = tuple(stmt)

    def append_statements(self, stmt):
        statements = list(self.statements)
        statements.append(stmt)
        self._statements = tuple(statements)

    def call_impl(self, caller, args, **kwargs):
        rtn = None
        for stmt in self.statements:
            rtn = stmt(caller, args)
            if caller.break_point is not None:
                return rtn
        return rtn

    def __repr__(self):
        stmts = ""
        for s in self.statements:
            stmts = "{} {}".format(stmts, s)
        return "{};".format(stmts)


class StatementParam(Enum):

    STEP = "step"
    CONDITIONAL_ARGS = "conditional-args"
    CONDITION_TRUELY_EVALUATED = "condition-truely-evaluated"
    STATEMENTS = "statements"
    OPTIONS = "options"
    REACHED = "reached"
    VISITED = "visited"
    IF = "if"
    ELIF = "elif"
    ELSE = "else"
    END = "end"


class ForeachStatement(NetworkSequentialStatements):

    def __init__(self, owner, var, fetchee):
        super().__init__(owner)
        self._var = var.symbol
        self._fetchee = fetchee.symbol

    @property
    def var(self):
        return self._var

    @property
    def fetchee(self):
        return self._fetchee

    def fetch(self, caller):
        accessor = caller.accessor
        fetchee = accessor.get(caller, self.fetchee)
        pos = accessor.get(caller, self.fetch_pos_name)
        pos = pos + 1
        accessor.set(caller, self.fetch_pos_name, pos)
        if pos < len(fetchee):
            accessor.set(caller, self.var, fetchee[pos])
            return True
        else:
            return False

    @property
    def fetch_pos_name(self):
        return "{}$pos".format(self.var)

    def prepare(self, caller):
        try:
            caller.accessor.set(caller, self.fetch_pos_name, -1)
            return True
        except NetworkReferenceError as ex:
            print("preparation failed in ForeachStatement.")
            return False

    def call_impl(self, caller, args, **kwargs):
        rtn = None
        while self.fetch(caller):
            rtn = super().call_impl(caller, args)
            if caller.break_point is not None:
                break
        return rtn

    def args_impl(self, caller, args, **kwargs):
        if not self.prepare(caller):
            rtn = NetworkReturnValue(caller, False, "fetching from {} failed.".format(self.fetchee))
            return rtn
        return args

    def __repr__(self):
        return "for {} {} {}".format(self.var, self.fetchee, self.statements)


class WhileStatement(NetworkSequentialStatements):

    def __init__(self, owner, cond):
        super().__init__(owner)
        self._cond = cond

    @property
    def condition(self):
        return self._cond

    def call_impl(self, caller, args, **kwargs):
        rtn = None

        while self.condition.evaluate(caller):
            rtn = super().call_impl(caller, args)
            if caller.break_point is not None:
                break
        return rtn

    def __repr__(self):
        return "while({}){}".format(self._cond, self.statements)


class IfElifElseStatement(NetworkSequentialStatements):

    def __init__(self, owner):
        super().__init__(owner)
        self._closed = False
        self._conditions = []

    @property
    def closed(self):
        return self._closed

    @property
    def conditions(self):
        return self._conditions

    def append_if_elif_statements(self, condition, statements):
        if self.closed:
            raise NetworkError("{} illegal attempt. statement already closed.".format(self))
        else:
            self.conditions.append(condition)
            self.append_statements(statements)

    def append_else_statements(self, statements):
        if self.closed:
            raise NetworkError("{} illegal attempt. statement already closed.".format(self))
        else:
            condition = TrueEvaluatee(None)
            self.conditions.append(condition)
            self.append_statements(statements)
            self._closed = True

    def call_impl(self, caller, args, **kwargs):
        rtn = None
        for cond, stmt in zip(self.conditions, self.statements):
            if cond.evaluate(caller):
                for s in stmt:
                    rtn = s(caller)
                    if caller.break_point is not None:
                        return rtn
                return rtn
        return rtn

    def __repr__(self):
        repr = "if ({}) {}".format(self._conditions[0], len(self.statements[0]))
        for c, s in zip(self.conditions[1:], self.statements[1:]):
            if c == self.conditions[len(self.conditions)-1]:
                _repr = "else {}".format(s)
            else:
                _repr = "elif ({}) {}".format(c, s)
            repr = "{} {}".format(repr, _repr)
        return repr


class MethodAvator(NetworkMethod):

    def __init__(self, method_owner, signature, callee_owner, callee_entity, extra_args, globally=True):
        super().__init__(method_owner, signature, args=None, globally=globally)
        self._callee_owner = callee_owner
        self._callee_entity = callee_entity
        self._extra_args = extra_args

    def call_impl(self, caller, args, **kwargs):
        if self._callee_owner is None:
            return self._callee_entity(caller, args, self._extra_args)
        else:
            return self._callee_entity(self._callee_owner, caller, args, self._extra_args)

    def args_impl(self, caller, args, **kwargs):
        new_args = []
        for a in args:
            if isinstance(a, GenericValueHolder):
                new_args.append(a.value)
            else:
                new_args.append(a)
        return new_args

    def __repr__(self):
        return "{}.{}:wrapper(actual owner:{})".format(self.owner.signature, self.signature, self._callee_owner)


class BoundMethodAvator(NetworkMethod):

    def __init__(self, method_owner, signature, callee_owner, method_entity, globally=True):
        super().__init__(method_owner, signature, args=None, globally=globally)
        self._callee_owner = callee_owner
        self._method_entity = method_entity

    def call_impl(self, caller, args, **kwargs):
        args_str = ""
        if len(args) != 0:
            args_str = "a[0]"
            for i in range(1, len(args)):
                args_str = "{},a[{}]".format(args_str, i)
        eqn = "lambda o, a: o.{}({})".format(self.signature, args_str)
        func = eval(eqn)
        return func(caller, args)

    def args_impl(self, caller, args, **kwargs):
        new_args = []
        for a in args:
            if isinstance(a, GenericValueHolder):
                new_args.append(a.value)
            else:
                new_args.append(a)
        return new_args

    def __repr__(self):
        return "{}.{}:wrapper(actual owner:{})".format(self.owner.signature, self.signature, self._callee_owner)


class WrappedAccessor(NetworkMethod):

    def __init__(self, accessor_owner, signature, actual_owner, accessor, globally=True, extra_args=None, **kwargs):
        super().__init__(accessor_owner, signature, args=None, globally=globally)
        self._actual_owner = actual_owner
        self._accessor = accessor
        self._extra_args = extra_args
        self._kwargs = {}
        for k in kwargs.keys():
            self._kwargs[k] = kwargs[k]

    @property
    def accessor_owner(self):
        return self.owner

    @property
    def accessor(self):
        return self._accessor

    @property
    def actual_owner(self):
        return self._actual_owner

    @property
    def extra_args(self):
        return self._extra_args

    @property
    def kwargs(self):
        return self._kwargs

    def call_impl(self, caller, args, **kwargs):
        rtn = self.accessor(self.accessor_owner, caller, self.actual_owner, args, self.extra_args)
        return rtn

    def args_impl(self, caller, args, **kwargs):
        new_args = []
        for a in args:
            if isinstance(a, GenericValueHolder):
                new_args.append(a.value)
            else:
                new_args.append(a)
        return new_args

    def __repr__(self):
        return "WrappedAccessor to {}.{}".format(self.actual_owner, self.signature)


class StrictWrappedAccessor(WrappedAccessor):

    def __init__(self, accessor_owner, signature, actual_owner, accessor, args_validator=None, globally=True, extra_args=None, **kwargs):
        super().__init__(accessor_owner, signature, actual_owner=actual_owner, accessor=accessor,
                         globally=globally, extra_args=extra_args, kwargs=kwargs)
        self._args_validator = args_validator

    @property
    def args_validator(self):
        return self._args_validator

    def call_impl(self, caller, args, **kwargs):
        caller_args = args
        result = self.accessor(self.accessor_owner, caller, self.actual_owner, caller_args, self.extra_args)
        return result

    def args_impl(self, caller, args, **kwargs):
        caller_args = args
        result = self.args_validator(self.accessor_owner, caller, self.actual_owner, caller_args, self.extra_args)
        if isinstance(result, NetworkReturnValue):
            return result
        elif result:
            rtn = NetworkReturnValue(caller_args, True, "")
        else:
            rtn = NetworkReturnValue(caller_args, False, "argument check error")
        return rtn

    def __repr__(self):
        return "StrictWrappedAccessor to {}.{}".format(self.actual_owner, self.signature)


class ExtensibleWrappedAccessor(StrictWrappedAccessor):

    def __init__(self, accessor_owner, signature, actual_owner, accessor, args_validator=None, globally=True,
                 extra_args=(), help_text="", preprocesses=(), postprocesses=(), **kwargs):
        super().__init__(accessor_owner, signature, actual_owner=actual_owner, accessor=accessor,
                         args_validator=args_validator,
                         globally=globally, extra_args=extra_args, kwargs=kwargs)
        self._preprocesses = preprocesses
        self._postprocesses = postprocesses
        self._help_text = help_text

    @property
    def preprocesses(self):
        return self._preprocesses

    @property
    def postprocesses(self):
        return self._postprocesses

    @property
    def help_text(self):
        return self._help_text

    def call_impl(self, caller, args, **kwargs):
        if len(args) > 0 and isinstance(args[0], CommandOption) and args[0].name == "help" and self.help_text is not None:
            print(self.help_text)
            return None
        for pre in self.preprocesses:
            rtn = pre[0](self.accessor_owner, caller, self.actual_owner, args, self.extra_args)
            if not pre[1]:
                return rtn
        rtn = self.accessor(self.accessor_owner, caller, self.actual_owner, args, self.extra_args)
        for post in self.postprocesses:
            rtn = post[0](self.accessor_owner, caller, self.actual_owner, args, self.extra_args)
            if not post[1]:
                break
        return rtn

    def args_impl(self, caller, args, **kwargs):
        if self.args_validator is None:
            return args
        caller_args = args
        result = self.args_validator(self.accessor_owner, caller, self.actual_owner, caller_args, self.extra_args)
        if isinstance(result, NetworkReturnValue):
            return result
        elif result:
            rtn = NetworkReturnValue(caller_args, True, "")
        else:
            rtn = NetworkReturnValue(caller_args, False, "argument check error")
        return rtn

    def __repr__(self):
        return "ExtensibleWrappedAccessor to {}.{}".format(self.actual_owner, self.signature)


class MethodWrapper(NetworkMethod):

    def __init__(self, method_owner, signature, default_caller, callee_entity, args):
        super().__init__(method_owner, signature, args, [])
        self._default_caller = default_caller
        self._callee_entity = callee_entity

    def call_impl(self, caller, args, **kwargs):
        if self._default_caller is not None:
            caller = self._default_caller
        return self._callee_entity(caller, args)

    def __repr__(self):
        return "{}:wrapper".format(self.signature)


class NetworkGenericWorld(NetworkClass):

    def __init__(self, owner, signature, super_class):
        super().__init__(owner, signature, super_class)
        self._resolvers = []
        self._bound_methods = []

    def append_resolver(self, resolver):
        self._resolvers.append(resolver)

    def remove_resolver(self, resolver):
        self._resolvers.remove(resolver)

    def deserialize(self, serializer: NetworkSerializer):
        try:
            serializer.open(for_read=True)
            # script = serializer.deserialize()
            serializer.close()
        except Exception as ex:
            if serializer.opened:
                serializer.close()
            raise ex

    def serialize(self, serializer: NetworkSerializer):
        try:
            serializer.open(for_read=False, for_write=True)
            for clazz in self.classes:
                doc = clazz.document
                doc.serizlize(serializer)
        except Exception as ex:
            if serializer.opened:
                serializer.close()
            raise ex

    def get_method(self, caller, sig):
        m = super().get_method(caller, sig)
        if m is not None:
            return m
        for r in self._resolvers:
            m = r.get_method(caller, sig)
            if m is not None:
                return m
        return None

    def get_bound_method(self, obj, args):
        for m in inspect.getmembers(obj, inspect.ismethod):
            if m[0] == args:
                return m[1]
        return None

    def get_bound_methods_info(self, obj, args):
        I = []
        for m, _ in inspect.getmembers(obj, inspect.ismethod):
            # if m in args:
            I.append(m)
        return I

    def implement_bound_methods(self, obj, args):
        R = []
        for n, m in inspect.getmembers(obj, inspect.ismethod):
            if n in args:
                # callee_entity = lambda c, caller, caller_args, generator_args: generator_args[0](caller, caller_args)
                # method = BoundMethodAvator(obj, n, obj, callee_entity, [m], globally=True)
                method = BoundMethodAvator(obj, n, obj, m, globally=True)
                obj.declare_method(method, globally=True)
                R.append(n)
        return R


class NetworkMethodWrapper(NetworkMethod):

    def __init__(self, owner, swapped_context, signature, func, args):
        super().__init__(owner, signature, args, [], None)
        self._swapped_context = swapped_context
        self._func = func

    def set_context(self, context):
        self._swapped_context = context

    @property
    def swapped_context(self):
        return self._swapped_context

    @property
    def document(self):
        return self._document

    def call_impl(self, caller, args, **kwargs):
        return self._func(self._swapped_context, args)


class ResolverMediator:

    def __init__(self, mediator: NetworkInvoker):
        self._mediator = mediator

    @property
    def mediator(self) -> NetworkInvoker:
        return self._mediator


class ToplevelInstance(NetworkInstance):

    def __init__(self, signature):
        super().__init__(None, 0, None, None)
        self._signature = signature
        self._mediators = []

    @property
    def signature(self):
        return self._signature

    @property
    def mediators(self):
        return self._mediators

    def append_mediator(self, med):
        self._mediators.append(med)

    def remove_mediator(self, med):
        self._mediators.remove(med)

    def push_context(self):
        # stack control ignored
        pass

    def pop_context(self, context_id):
        # stack control ignored
        pass


class NetworkSecurityPolicy(GenericDescription):

    def __init__(self, name, is_symbol=False):
        super().__init__(name, is_symbol)
        self._desc = None
        self._map = {}

    @property
    def description(self):
        return self._desc

    def set_descriptoin(self, desc):
        self._desc = desc

    def encode_description(self):
        if self.description is None:
            return NetworkReturnValue(False, False, "no description")
        pos = 0
        skip_pat = r"\n*(\s*(//.*|)\n)*"
        # desc_pat = r"\s*(?P<start>[a-zA-Z]+0-9 ]*[a-zA-Z0-9]+)::\s*\n(?P<desc>.*)\n\s*::(?P<end>[a-zA-Z]+0-9 ]*[a-zA-Z0-9]+)(\s*\n)*"
        desc_pat = r"\s*(?P<type>(property|method))\s+(?P<member>)\s*::\s*(?P<desc>(private|protected|public)(\s*\n)*"
        while True:
            m, d, next_pos = GU.pattern_iter(skip_pat, self.description[pos:])
            if m is not None:
                pos = next_pos
                continue
            m, d, next_pos = GU.pattern_iter(desc_pat, self.description[pos:])
            if m is None:
                break
            t = d['type']
            m = d['member']
            desc = d['desc']
            self._map[m] = {}
            self._map[m]["type"] = t
            self._map[m]["desc"] = desc
