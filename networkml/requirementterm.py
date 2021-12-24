# -*- coding: utf-8 -*-

from networkml.generic import GenericDescription


class Description(GenericDescription):

    def __init__(self, name, is_symbol=False):
        super().__init__(name, is_symbol)
    #     self._name = name
    #     self._is_symbol = is_symbol
    #
    # @property
    # def name(self):
    #     return self._name
    #
    # @property
    # def is_symbol(self):
    #     return self._is_symbol
    #
    # def __repr__(self):
    #     if self.is_symbol:
    #         return "{} '{}'".format("symbol ", self.name)
    #     else:
    #         return "{} '{}'".format("description ", self.name)


class RequirementTerm(Description):

    def __init__(self, name, is_symbol=False, role="actor"):
        super().__init__(name, is_symbol)
        self._role = role

    @property
    def role(self):
        return self._role

    def set_role(self, role):
        self._role = role

    def __repr__(self):
        return "{} {}".format(self.role, super().__repr__())


class RequirementTermOption:

    def __init__(self, name: str, assignee=None, has_assignee=False):
        self._name = name
        self._assignee = assignee
        self._has_assignee = has_assignee

    @property
    def name(self):
        return self._name.replace("-", "")

    @property
    def has_assignee(self):
        return self._has_assignee

    @property
    def assignee(self):
        return self._assignee

    def __repr__(self):
        if self._has_assignee:
            return "{}={}".format(self._name, self._assignee)
        else:
            return "{}".format(self._name)


class ActionRequirement:

    def __init__(self, action, requirer, requiree, predicates_for_action=None,
                 predicates_for_requirer=None, predicates_for_requiree=None):
        self._action = action
        self._requirer = requirer
        self._requiree = requiree
        self._predicates_for_action = predicates_for_action
        self._predicates_for_requirer = predicates_for_requirer
        self._predicates_for_requiree = predicates_for_requiree

    @property
    def action(self):
        return self._action

    @property
    def requirer(self):
        return self._requirer

    @property
    def requiree(self):
        return self._requiree

    @property
    def predicates_for_action(self):
        return self._predicates_for_action

    @property
    def predicates_for_requirer(self):
        return self._predicates_for_requirer

    @property
    def predicates_for_requiree(self):
        return self._predicates_for_requiree

    def __repr__(self):
        if self.predicates_for_requirer is None:
            spred = "without predicate"
        else:
            spred = "with predicates {}".format(self.predicates_for_requirer)
        if self.predicates_for_action is None:
            mpred = "without predicate"
        else:
            mpred = "with predicates {}".format(self.predicates_for_action)
        if self.predicates_for_requiree is None:
            opred = "without predicate"
        else:
            opred = "with predicates {}".format(self.predicates_for_requiree)
        return "subject {} {},\nmethod {} {},\nobject {} {}"\
            .format(self._requirer, spred, self._action, mpred, self._requiree, opred)


class ExistenceRequirement(RequirementTerm):

    def __init__(self, name, role, options, is_symbol=True):
        super().__init__(name, is_symbol, role)
        self._options = options

    @property
    def options(self):
        return self._options

    def __repr__(self):
        return "extence {} with role:{} and requirements {}".format(self.name, self.role, self._options)


class ActionScript(RequirementTerm):

    def __init__(self, name, executables=(), is_symbol=True):
        super().__init__(name, is_symbol)
        self._executables = executables

    @property
    def executables(self):
        return self._executables

    def __repr__(self):
        tab = "\t"
        script = self.name
        for e in self.executables:
            script = "\n{}{}".format(tab, e)
        return script

