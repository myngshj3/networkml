# -*- coding: utf-8 -*-

import re
from networkml.generic import GenericComponent, GenericValueHolder, GenericValidator, GenericUnaryEvaluatee
from networkml.generic import GenericBinaryEvaluatee, GenericValidatorParam, GenericEvaluatee


class Validatee(GenericComponent, GenericValueHolder):

    def __init__(self, owner, spec=None):
        super().__init__(owner)
        self._spec = spec


class MultiArityEvaluatee(GenericComponent, GenericEvaluatee):

    def __init__(self, owner, sym="*", evaluatees=(), repr_with_parent=True):
        super().__init__(owner)
        self._sym = sym
        self._evaluatees = evaluatees
        self._repr_with_parent = repr_with_parent
        self._symbolic_args = [False for _ in self._evaluatees]

    @property
    def arity(self):
        return len(self._evaluatees)

    @property
    def sym(self):
        return self._sym

    @property
    def validator(self):
        if self.owner is None:
            return None
        return self.owner.validator

    @property
    def value(self):
        ret = []
        for i in range(self.arity):
            ret.append(self.nth(i))
        return ret

    def set_owner(self, owner):
        super().set_owner(owner)
        for c in self._evaluatees:
            if isinstance(c, GenericComponent):
                c.set_owner(owner)

    def get_symbolic(self, n):
        return self._symbolic_args[n]

    def set_symbolic(self, n, f):
        self._symbolic_args[n] = f

    def set_repr_with_parent(self, flag: bool):
        self._repr_with_parent = flag

    def nth(self, n):
        if not self.get_symbolic(n):
            return self._evaluatees[n]
        elif self.validator is None:
            return self._evaluatees[n]
        return self.validator.validate(self._evaluatees[n])

    def evaluate(self, caller=None):
        rtn = []
        if caller is None:
            validator = None
        else:
            validator = caller.validator
        for i in range(self.arity):
            if validator is None or not self.get_symbolic(i):
                rtn.append(self.nth(i))
            else:
                if isinstance(self._evaluatees[i], GenericEvaluatee):
                    rtn.append(self._evaluatees[i].evaluate(caller))
                else:
                    rtn.append(validator.validate(self._evaluatees[i]))
        return tuple(rtn)

    def __repr__(self):
        if self._repr_with_parent:
            lpar = "("
            rpar = ")"
        else:
            lpar = ""
            rpar = ""
        if not self.get_symbolic(0) and type(self._evaluatees[0]) is str:
            quote = "\""
        else:
            quote = ""
        repr = "{}{}{}".format(quote, self.nth(0), quote)
        for i, c in enumerate(self._evaluatees[1:]):
            i = i+1
            if not self.get_symbolic(i) and type(self._evaluatees[i]) is str:
                quote = "\""
            else:
                quote = ""
            repr = "{},{}{}{}".format(repr, quote, c, quote)
        return "{}{}{}{}".format(self.sym, lpar, repr, rpar)


class UnaryEvaluatee(MultiArityEvaluatee, GenericUnaryEvaluatee):

    def __init__(self, owner, sym, expr, as_symbol=False, repr_with_parent=False):
        super().__init__(owner, sym, [expr], repr_with_parent=repr_with_parent)
        super().set_symbolic(0, as_symbol)

    @property
    def value(self):
        return super().nth(0)
        # if not self.get_symbolic(0):
        #     return self._evaluatees[0]
        # elif self.validator is None:
        #     return self._evaluatees[0]
        # else:
        #     return self.validator.unary_validate(self._evaluatees[0])

    def evaluate(self, caller=None):
        if caller is None:
            validator = None
        else:
            validator = caller.validator
        if validator is None:
            return self._evaluatees[0]
        if isinstance(self._evaluatees[0], GenericEvaluatee):
            if validator is None:
                expr = self._evaluatees[0]
            else:
                expr = validator.validate(self._evaluatees[0])
        else:
            expr = self.value
        return expr

    def __repr__(self):
        if self._repr_with_parent:
            lpar = "("
            rpar = ")"
        else:
            lpar = ""
            rpar = ""
        if not self.get_symbolic(0) and type(self.value) is str:
            quote = "\""
        else:
            quote = ""
        return "{}{} {}{}{}{}".format(lpar, self._evaluatees[0], quote, self.value, quote, rpar)


class TrueEvaluatee(UnaryEvaluatee):

    def __init__(self, owner):
        super().__init__(owner, "", True, as_symbol=False, repr_with_parent=False)


class BinaryEvaluatee(MultiArityEvaluatee, GenericBinaryEvaluatee):

    def __init__(self, owner, l, r, sym, l_symbol=False, r_symbol=False, repr_with_parent=False):
        super().__init__(owner, sym=sym, evaluatees=(l, r), repr_with_parent=repr_with_parent)
        super().set_symbolic(0, l_symbol)
        super().set_symbolic(1, r_symbol)

    @property
    def l_symbol(self):
        return self.get_symbolic(0)

    @l_symbol.setter
    def l_symbol(self, f):
        self.set_symbolic(0, f)

    @property
    def r_symbol(self):
        return self.get_symbolic(1)

    @r_symbol.setter
    def r_symbol(self, f):
        self.set_symbolic(1, f)

    @property
    def l(self):
        return super().nth(0)
        # if not self.l_symbol:
        #     return self._evaluatees[0]
        # else:
        #     if self.validator is None:
        #         l = self._evaluatees[0]
        #     else:
        #         l = self.validator.validate(self._evaluatees[0])
        #     if type(l) is str:
        #         l = "\"{}\"".format(l)
        #     return l

    @property
    def r(self):
        return super().nth(1)
        # if not self.r_symbol:
        #     return self._evaluatees[1]
        # else:
        #     if self.validator is None:
        #         r = self._evaluatees[1]
        #     else:
        #         r = self.validator.validate(self._evaluatees[1])
        #     if type(r) is str:
        #         r = "\"{}\"".format(r)
        #     return r

    def evaluate(self, caller=None):
        return super().evaluate(caller)
        # if caller is None:
        #     validator = self.validator
        # else:
        #     validator = caller.validator
        # if validator is None:
        #     l = self.l
        #     r = self.r
        # else:
        #     if self.l_symbol:
        #         if isinstance(self._evaluatees[0], GenericEvaluatee):
        #             l = self._evaluatees[0].evaluate(caller)
        #         else:
        #             l = validator.validate(self._evaluatees[0])
        #     else:
        #         l = self._evaluatees[0]
        #     if self.r_symbol:
        #         if isinstance(self._evaluatees[1], GenericEvaluatee):
        #             r = self._evaluatees[1].evaluate(caller)
        #         else:
        #             r = validator.validate(self._evaluatees[1])
        #     else:
        #         r = self._evaluatees[1]
        # return l, r

    def __repr__(self):
        if self._repr_with_parent:
            lpar = "("
            rpar = ")"
        else:
            lpar = ""
            rpar = ""
        if not self.l_symbol and type(self.l) is str:
            l_quote = "\""
        else:
            l_quote = ""
        if not self.r_symbol and type(self.r) is str:
            r_quote = "\""
        else:
            r_quote = ""
        return "{}{}{}{}{}{}{}{}{}".format(lpar, l_quote, self.l, l_quote, self._sym, r_quote, self.r, r_quote, rpar)


class BooleanUnaryEvaluatee(UnaryEvaluatee):

    def __init__(self, owner, expr, sym="", as_symbol=False, repr_with_parent=False):
        super().__init__(owner, expr, sym, as_symbol, repr_with_parent)

    # @property
    # def value(self):
    #     return super().value
    #
    # def evaluate(self, caller):
    #     return super().evaluate(caller)


class BooleanNegatee(BooleanUnaryEvaluatee):

    def __init__(self,owner,  expr, sym="not", as_symbol=False, repr_with_parent=False):
        super().__init__(owner, expr, sym, as_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        return not super().evaluate(caller)


class BooleanBinaryEvaluatee(BinaryEvaluatee):

    def __init__(self, owner, l, r, sym, l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)


class BooleanConjunctiveEvaluatee(BooleanBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="and", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l and r


class BooleanDisjunctiveEvaluatee(BooleanBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="or", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l or r


class BooleanEqualityEvaluatee(BooleanBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="==", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l == r


class BooleanDifferenceEvaluatee(BooleanBinaryEvaluatee):
    def __init__(self, owner, l, r, sym="!=", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l != r


class BooleanMatchee(BooleanBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="=~", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def matches(self, l, r):
        if len(r) < 2:
            return False
        elif r[0] != "/" or r[len(r)-1] != "/":
            return False
        r = r[1:len(r)-1]
        m = re.search(r, l)
        return m is not None

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return self.matches(l, r)


class BooleanUnmatchee(BooleanMatchee):

    def __init__(self, owner, l, r, sym="!=~", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        return not super().evaluate(caller)


class BooleanLessThanEvaluatee(BooleanBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="<", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l < r


class BooleanLessOrEqualsEvaluatee(BooleanBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="<=", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l <= r


class BooleanGreaterThanEvaluatee(BooleanBinaryEvaluatee):

    def __init__(self, owner, l, r, sym=">", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l > r


class BooleanGreaterOrEqualsEvaluatee(BooleanBinaryEvaluatee):

    def __init__(self, owner, l, r, sym=">=", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l >= r


class ArithmeticBinaryEvaluatee(BinaryEvaluatee):

    def __init__(self, owner, l, r, sym="", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        return super().evaluate(caller)

    def __repr__(self):
        return "{}{}{}".format(self._evaluatees[0], self.sym, self._evaluatees[1])


class ArithmeticAdditionalEvaluatee(ArithmeticBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="+", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l + r


class ArithmeticSubtractalEvaluatee(ArithmeticBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="-", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l - r


class ArithmeticMultiplicableEvaluatee(ArithmeticBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="*", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l * r


class ArithmeticDivideEvaluatee(ArithmeticBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="*", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l / r


class ArithmeticModulusEvaluatee(ArithmeticBinaryEvaluatee):

    def __init__(self, owner, l, r, sym="%", l_symbol=False, r_symbol=True, repr_with_parent=False):
        super().__init__(owner, l, r, sym, l_symbol, r_symbol, repr_with_parent)

    def evaluate(self, caller=None):
        l, r = super().evaluate(caller)
        return l % r
