# -*- coding: utf-8 -*-

import ply.lex as lex
import ply.yacc as yacc
import traceback

# import our modules
from generic import GenericEvaluatee
from error import NetworkError, NetworkParserError, NetworkLexerError
from validator import Validatee, ArithmeticModulusEvaluatee, ArithmeticMultiplicableEvaluatee
from validator import ArithmeticSubtractalEvaluatee, ArithmeticBinaryEvaluatee, ArithmeticAdditionalEvaluatee
from validator import ArithmeticDivideEvaluatee, ArithmeticBinaryEvaluatee
from validator import BooleanNegatee, BooleanBinaryEvaluatee
from validator import BooleanConjunctiveEvaluatee, BooleanDisjunctiveEvaluatee, BooleanGreaterOrEqualsEvaluatee
from validator import BooleanGreaterThanEvaluatee, BooleanLessOrEqualsEvaluatee, BooleanLessThanEvaluatee
from validator import BooleanEqualityEvaluatee, BooleanDifferenceEvaluatee, BooleanMatchee, BooleanUnmatchee
from validator import BooleanUnaryEvaluatee
from network import NetworkClassInstance, NetworkMethodCaller, WhileStatement, IfElifElseStatement
from network import ReachabilitySpecification, NetworkCallable, NetworkConditionalArg, NetworkBreak
from network import NetworkMethod, ForeachStatement, NetworkSubstituter, HierarchicalRefer, NetworkFetcher
from network import NetworkConditionValidatee, ReachNetworkConstructor, Interval, SimpleVariable, NetworkReturn
from network import Interval, Numberset, NumbersetOperator, CommandOption
from requirementterm import RequirementTerm, RequirementTermOption, ActionRequirement, ExistenceRequirement
from requirementterm import ActionScript


class RequirementSyntacticAnalyzer:

    # Word analysis
    reserved = {
        'and': 'AND',
        'or': 'OR',
        'not': 'NOT',
        'null': 'NULL',
        'True': 'TRUE',
        'False': 'FALSE',
        'there': 'THERE',
        'exists': 'EXISTS',
        "doesn't": 'DOESNT',
        'such': 'SUCH',
        'that': 'THAT',
        'method': 'METHOD',
        'object': 'OBJECT',
        '$caller': 'CALLER'
    }
    tokens = [
              'SYMBOL', 'HIERARCH_SYMBOL',
              'EQUAL', 'DIFFERENT', 'LESS_THAN', 'LESS_OR_EQUAL', 'GREATER_THAN', 'GREATER_OR_EQUAL',
              'MATCH', 'UNMATCH',
              'LPAR', 'RPAR', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
              'COMMA', 'DOUBLEPERIOD',
              'NUMBER', 'NEGATIVE_INT', 'FLOAT', 'LITERAL', 'REPATTERN',
              'NEGATIVE_FLOAT',
              'PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE', 'MOD',
              'HIPHON',
              'OUTBOUND', 'INBOUND',
              'OPTION',
              'SUBST',
              'SEMICORON',
              'COMMENT'
              ] + list(reserved.values())
    token_list = (
        # Reserved words
    )
    token = tokens

    t_ignore_COMMENT = r"/\*\[\s\S]*\*/|//.*"
    t_ignore = " \t"

    # t_INDEX = r""
    t_REPATTERN = r"/[^/]+/"
    t_PLUS = r"\+"
    t_MINUS = r"\-"
    t_MULTIPLY = r"\*"
    t_DIVIDE = r"\/"
    t_MOD = r"\%"

    def t_SYMBOL(self, t):
        r"([a-zA-Z_]+[a-zA-Z_0-9]*\.)*[a-zA-Z_]+[a-zA-Z_0-9]*"
        # r"[a-zA-Z_]+[a-zA-Z_0-9]*"
        if t.value in self.reserved:
            t.type = self.reserved[t.value]
            return t
        elif "." in t.value:
            t.type = 'HIERARCH_SYMBOL'
            return t
        else:
            return t
    t_HIERARCH_SYMBOL = r"[a-zA-Z_]+[a-zA-Z_0-9]*(\.[a-zA-Z_]+[a-zA-Z_0-9])*"
    t_EQUAL = r"=="
    t_DIFFERENT = r"!="
    t_LESS_THAN = r"<"
    t_LESS_OR_EQUAL = r"<="
    t_GREATER_THAN = r">"
    t_GREATER_OR_EQUAL = r">="
    t_MATCH = r"=~"
    t_UNMATCH = r"!=~"
    t_LPAR = r"\("
    t_RPAR = r"\)"
    t_LBRACE = r"\["
    t_RBRACE = r"\]"
    t_LBRACKET = r"\{"
    t_RBRACKET = r"\}"
    t_NUMBER = r"[0-9]+"
    t_NEGATIVE_INT = r"\-[0-9]+"
    t_FLOAT = r"[0-9]+\.[0-9]+"
    t_NEGATIVE_FLOAT = r"\-[0-9]+\.[0-9]+"
    t_LITERAL = r"\"(\"\"|[^\"])*\""
    t_NULL = r"null"
    t_OPTION = r"\-{1,2}[a-zA-Z]+([_]*[a-zA-Z0-9]+)*"
    t_DOUBLEPERIOD = r"\.\."
    t_AND = r"and"
    t_OR = r"or"
    t_NOT = r"not"
    t_THERE = r"there"
    t_EXISTS = r"exists"
    t_DOESNT = r"doesn't"
    t_SUCH = r"such"
    t_THAT = r"that"
    t_METHOD = r"method"
    t_OBJECT = r"object"
    t_CALLER = r"\$caller"
    t_HIPHON = r"\-+"
    t_OUTBOUND = r"\-+>"
    t_INBOUND = r"<\-+"
    t_COMMA = r","
    t_SUBST = r"="
    t_SEMICORON = r";"

    # initializer
    def __init__(self):
        self.lexer = lex.lex(module=self)

    def t_error(self, t):
        # _print("Illegal character {}".format(t.value[0]))
        t.lexer.skip(1)

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)


class RequirementParser:

    # Parsing rules
    tokens = RequirementSyntacticAnalyzer.tokens

    def p_action_requirement_list(self, p):
        """
        action_requirement_list : prerequisitional_requirements  action_requirements
        """
        p[0] = p[1]
        p[0].extend(p[2])

    def p_prerequisitional_requirements(self, p):
        """
        prerequisitional_requirements : existence_requirements action_descriptions
        """
        p[0] = p[1]
        p[0].extend(p[2])
        # action_requirement_list : action_requirement_list  action_requirement_list

    def p_term_kind(self, p):
        """
        term_kind : OBJECT
        term_kind : METHOD
        """
        p[0] = p[1]

    def p_existence_requirements(self, p):
        """
        existence_requirements : THERE EXISTS term_kind SYMBOL                               SEMICORON
        existence_requirements : THERE EXISTS term_kind SYMBOL SUCH THAT requirement_options SEMICORON
        existence_requirements : existence_requirements existence_requirements
        """
        if len(p) == 3:
            p[0] = p[1]
            p[0].extend(p[2])
        elif len(p) == 6:
            p[0] = ExistenceRequirement(p[4], p[3], None, is_symbol=True)
            p[0] = [p[0]]
        elif len(p) == 9:
            p[0] = ExistenceRequirement(p[4], p[3], p[7], is_symbol=True)
            p[0] = [p[0]]
        else:
            raise NetworkParserError(p)

    def p_action_descriptions(self, p):
        """
        action_descriptions : METHOD SYMBOL LBRACKET  action_requirements RBRACKET
        action_descriptions : action_descriptions action_descriptions
        """
        if len(p) == 6:
            desc = ActionScript(p[2], p[4], is_symbol=False)
            p[0] = [desc]
        elif len(p) == 3:
            p[0] = p[1]
            p[0].extend(p[2])
        else:
            raise NetworkParserError(p)

    def p_action_requirements(self, p):
        """
        action_requirements : requirement_term COMMA requirement_term COMMA requirement_term SEMICORON
        action_requirements : action_requirements  action_requirements
        """
        if len(p) == 3:
            p[0] = p[1]
            p[0].extend(p[2])
        elif len(p) == 7:
            p[1][0].set_role = "caller"
            p[1][0].set_role = "method"
            p[1][0].set_role = "object"
            p[0] = ActionRequirement(p[3][0], p[1][0], p[5][0], predicates_for_action=p[3][1],
                                     predicates_for_requirer=p[1][1], predicates_for_requiree=p[5][1])
            p[0] = [p[0]]
        else:
            raise NetworkParserError(p)

    def p_requirement_term(self, p):
        """
        requirement_term : LITERAL
        requirement_term : SYMBOL
        requirement_term : HIERARCH_SYMBOL
        requirement_term : requirement_term  requirement_options
        """
        if len(p) == 2:
            if p[1][0] == "\"" and p[1][len(p[1])-1] == "\"":
                is_symbol = False
            else:
                is_symbol = True
            p[0] = [RequirementTerm(p[1], is_symbol=is_symbol), None]
        else:
            p[0] = p[1]
            p[0][1] = p[2]

    def p_requirement_options(self, p):
        """
        requirement_options : requirement_option_assignment
        requirement_options : requirement_option_assignment  SUBST  requirement_option_assignee
        requirement_options : requirement_options  requirement_options
        """
        if len(p) == 2:
            option = RequirementTermOption(p[1], has_assignee=False)
            p[0] = [option]
        elif len(p) == 4:
            option = RequirementTermOption(p[1], p[3], has_assignee=True)
            p[0] = [option]
        elif len(p) == 3:
            p[0] = p[1]
            p[0].extend(p[2])
        else:
            raise NetworkParserError(p)

    def p_requirement_option_assignment(self, p):
        """
        requirement_option_assignment : OPTION
        """
        p[0] = p[1]

    def p_requirement_option_assignee(self, p):
        """
        requirement_option_assignee : int
        requirement_option_assignee : float
        requirement_option_assignee : bool
        requirement_option_assignee : LITERAL
        requirement_option_assignee : SYMBOL
        requirement_option_assignee : HIERARCH_SYMBOL
        requirement_option_assignee : numberset
        requirement_option_assignee : spec
        requirement_option_assignee : reachability_network
        requirement_option_assignee : tuple
        requirement_option_assignee : null
        """
        p[0] = p[1]

    def p_tuple(self, p):
        """
        tuple : opened_tuple RPAR
        """
        p[0] = p[1]

    def p_opened_tuple(self, p):
        """
        opened_tuple : LPAR
        opened_tuple : opened_tuple tuple_entry
        """
        if len(p) == 2:
            p[0] = []
        else:
            p[0] = p[1]
            p[0].extend(p[2])

    def p_tuple_entry(self, p):
        """
        tuple_entry : SYMBOL
        tuple_entry : LITERAL
        tuple_entry : int
        tuple_entry : float
        tuple_entry : bool
        tuple_entry : spec
        tuple_entry : reachability_network
        """
        p[0] = p[1]

    def p_natural_number(self, p):
        """
        natural_number : NUMBER
        """
        p[0] = int(p[1])

    def p_empty_tuple(self, p):
        """
        empty_tuple : LPAR RPAR
        """
        p[0] = []

    def p_empty_list(self, p):
        """
        empty_list : LBRACE RBRACE
        """
        p[0] = []

    def p_empty_hash(self, p):
        """
        empty_hash : LBRACKET RBRACKET
        """
        p[0] = {}

    def p_int(self, p):
        """
        int : nonnegative_int
        int : negative_int
        """
        p[0] = p[1]

    def p_nonnegative_int(self, p):
        """
        nonnegative_int : NUMBER
        """
        p[0] = int(p[1])

    def p_negative_int(self, p):
        """
        negative_int : NEGATIVE_INT
        """
        p[0] = int(p[1])

    def p_float(self, p):
        """
        float : nonnegative_float
        float : negative_float
        """
        p[0] = p[1]

    def p_nonnegative_float(self, p):
        """
        nonnegative_float : FLOAT
        """
        p[0] = float(p[1])

    def p_negative_float(self, p):
        """
        negative_float : NEGATIVE_FLOAT
        """
        p[0] = float(p[1])

    def p_string(self, p):
        """
        string : LITERAL
        """
        s = p[1][1:len(p[1])-1]
        s = s.replace('""', '"')
        p[0] = s

    def p_bool(self, p):
        """
        bool : TRUE
        bool : FALSE
        """
        p[0] = bool(p[1])

    def p_null(self, p):
        """
        null : NULL
        """
        p[0] = None

    def p_reference(self, p):
        """
        reference : SYMBOL
        reference : HIERARCH_SYMBOL
        """
        p[0] = p[1]

    def p_condition(self, p):
        """
        condition : bool_evaluable
        """
        p[0] = NetworkConditionalArg(self.owner, p[1])

    def p_bool_evaluable(self, p):
        """
        bool_evaluable : ambiguous_spec
        """
        p[0] = p[1]

    def p_number(self, p):
        """
        number : natural_number
        """
        p[0] = p[1]

    def p_arith_oper(self, p):
        """
        arith_oper : LPAR        arith_oper     LPAR
        arith_oper : arith_lopr  PLUS     arith_ropr
        arith_oper : arith_lopr  MINUS    arith_ropr
        arith_oper : arith_lopr  MULTIPLY arith_ropr
        arith_oper : arith_lopr  DIVIDE   arith_ropr
        arith_oper : arith_lopr  MOD      arith_ropr
        arith_oper : arith_oper  PLUS     arith_ropr
        arith_oper : arith_oper  MINUS    arith_ropr
        arith_oper : arith_oper  MULTIPLY arith_ropr
        arith_oper : arith_oper  DIVIDE   arith_ropr
        arith_oper : arith_oper  MOD      arith_ropr
        """
        if p[1] == "(" and p[3] == ")":
            p[0] = p[1]
        elif p[2] == "+":
            if isinstance(p[1], ArithmeticBinaryEvaluatee):
                ev = ArithmeticAdditionalEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=False, r_symbol=False)
            else:
                ev = ArithmeticAdditionalEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=False)
        elif p[2] == "-":
            if isinstance(p[1], ArithmeticBinaryEvaluatee):
                ev = ArithmeticSubtractalEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=False, r_symbol=False)
            else:
                ev = ArithmeticSubtractalEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=False)
        elif p[2] == "*":
            if isinstance(p[1], ArithmeticBinaryEvaluatee):
                ev = ArithmeticMultiplicableEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=False, r_symbol=False)
            else:
                ev = ArithmeticMultiplicableEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=False)
        elif p[2] == "/":
            if isinstance(p[1], ArithmeticBinaryEvaluatee):
                ev = ArithmeticDivideEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=False, r_symbol=False)
            else:
                ev = ArithmeticDivideEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=False)
        elif p[2] == "%":
            if isinstance(p[1], ArithmeticBinaryEvaluatee):
                ev = ArithmeticModulusEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=False, r_symbol=False)
            else:
                ev = ArithmeticModulusEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=False)
        else:
            raise NetworkParserError(p)

        p[0] = ev

    def p_arith_lopr(self, p):
        """
        arith_lopr : int
        arith_lopr : float
        arith_lopr : SYMBOL
        arith_lopr : HIERARCH_SYMBOL
        """
        p[0] = p[1]

    def p_arith_ropr(self, p):
        """
        arith_ropr : nonnegative_int
        arith_ropr : nonnegative_float
        arith_ropr : reference
        """
        p[0] = p[1]

    def p_option(self, p):
        """
        option : OPTION
        option : OPTION SUBST SYMBOL
        option : OPTION SUBST int
        option : OPTION SUBST float
        option : OPTION SUBST string
        option : OPTION SUBST numberset
        """
        if len(p) == 2:
            p[0] = CommandOption(p[1], "")
        elif len(p) == 4:
            p[0] = CommandOption(p[1], p[3])
        else:
            raise NetworkParserError(p)

    def p_file(self, p):
        """
        file : string
        """
        p[0] = p[1]

    def p_spec_symbolic_operand(self, p):
        """
        spec_symbolic_operand : SYMBOL
        """
        p[0] = "$$${}".format(p[1])

    def p_equality_spec_assignments(self, p):
        """
        equality_spec_assignments : spec_symbolic_operand EQUAL spec_symbolic_operand
        equality_spec_assignments : spec_symbolic_operand EQUAL int
        equality_spec_assignments : spec_symbolic_operand EQUAL float
        equality_spec_assignments : spec_symbolic_operand EQUAL string
        equality_spec_assignments : spec_symbolic_operand EQUAL bool
        equality_spec_assignments : int                   EQUAL spec_symbolic_operand
        equality_spec_assignments : float                 EQUAL spec_symbolic_operand
        equality_spec_assignments : string                EQUAL spec_symbolic_operand
        equality_spec_assignments : bool                  EQUAL spec_symbolic_operand
        """
        if type(p[1]) is str and p[1][0:3] == "$$$":
            p[1] = p[1][3:]
            l_symbol = True
        else:
            l_symbol = False
        if type(p[3]) is str and p[3][0:3] == "$$$":
            p[3] = p[3][3:]
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanEqualityEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        p[0] = spec

    def p_different_spec_assignments(self, p):
        """
        different_spec_assignments : spec_symbolic_operand DIFFERENT int
        different_spec_assignments : spec_symbolic_operand DIFFERENT float
        different_spec_assignments : spec_symbolic_operand DIFFERENT string
        different_spec_assignments : spec_symbolic_operand DIFFERENT bool
        different_spec_assignments : spec_symbolic_operand DIFFERENT spec_symbolic_operand
        """
        p[1] = p[1][3:]
        if type(p[3]) is str and p[3][0:3] == "$$$":
            p[3] = p[3][3:]
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanDifferenceEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=r_symbol)
        p[0] = spec

    def p_gt_spec_assignments(self, p):
        """
        gt_spec_assignments : spec_symbolic_operand GREATER_THAN int
        gt_spec_assignments : spec_symbolic_operand GREATER_THAN float
        gt_spec_assignments : spec_symbolic_operand GREATER_THAN spec_symbolic_operand
        """
        p[1] = p[1][3:]
        if type(p[3]) is str and p[3][0:3] == "$$$":
            p[3] = p[3][3:]
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanGreaterThanEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=r_symbol)
        p[0] = spec

    def p_ge_spec_assignments(self, p):
        """
        ge_spec_assignments : spec_symbolic_operand GREATER_OR_EQUAL int
        ge_spec_assignments : spec_symbolic_operand GREATER_OR_EQUAL float
        ge_spec_assignments : spec_symbolic_operand GREATER_OR_EQUAL spec_symbolic_operand
        """
        p[1] = p[1][3:]
        if type(p[3]) is str and p[3][0:3] == "$$$":
            p[3] = p[3][3:]
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanGreaterOrEqualsEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=r_symbol)
        p[0] = spec

    def p_le_spec_assignments(self, p):
        """
        le_spec_assignments : spec_symbolic_operand LESS_OR_EQUAL int
        le_spec_assignments : spec_symbolic_operand LESS_OR_EQUAL float
        le_spec_assignments : spec_symbolic_operand LESS_OR_EQUAL spec_symbolic_operand
        """
        p[1] = p[1][3:]
        if type(p[3]) is str and p[3][0:3] == "$$$":
            p[3] = p[3][3:]
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanLessOrEqualsEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=r_symbol)
        p[0] = spec

    def p_lt_spec_assignments(self, p):
        """
        lt_spec_assignments : spec_symbolic_operand LESS_THAN int
        lt_spec_assignments : spec_symbolic_operand LESS_THAN float
        lt_spec_assignments : spec_symbolic_operand LESS_THAN spec_symbolic_operand
        """
        p[1] = p[1][3:]
        if type(p[3]) is str and p[3][0:3] == "$$$":
            p[3] = p[3][3:]
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanLessThanEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=r_symbol)
        p[0] = spec

    def p_match_spec_assignments(self, p):
        """
        match_spec_assignments : spec_symbolic_operand MATCH REPATTERN
        match_spec_assignments : spec_symbolic_operand MATCH spec_symbolic_operand
        """
        p[1] = p[1][3:]
        if p[3][0:3] == "$$$":
            p[3] = p[3][3:]
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanMatchee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=r_symbol)
        p[0] = spec

    def p_unmatch_spec_assignments(self, p):
        """
        unmatch_spec_assignments : spec_symbolic_operand UNMATCH REPATTERN
        unmatch_spec_assignments : spec_symbolic_operand UNMATCH spec_symbolic_operand
        """
        p[1] = p[1][3:]
        if p[3][0:3] == "$$$":
            p[3] = p[3][3:]
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanUnmatchee(self.owner, p[1], p[3], sym=p[2], l_symbol=True, r_symbol=r_symbol)
        p[0] = spec

    def p_spec_assignments(self, p):
        """
        spec_assignments : equality_spec_assignments
        spec_assignments : different_spec_assignments
        spec_assignments : gt_spec_assignments
        spec_assignments : ge_spec_assignments
        spec_assignments : le_spec_assignments
        spec_assignments : lt_spec_assignments
        spec_assignments : match_spec_assignments
        spec_assignments : unmatch_spec_assignments
        spec_assignments : LPAR spec_assignments RPAR
        spec_assignments : spec_assignments AND spec_assignments
        spec_assignments : spec_assignments OR spec_assignments
        spec_assignments : NOT LPAR spec_assignments RPAR
        """
        if len(p) == 2:
            spec = p[1]
            p[0] = spec
        elif len(p) == 4:
            if p[1] == "(":
                spec = p[2]
            elif p[2] == "and":
                spec = BooleanConjunctiveEvaluatee(self.owner, p[1], p[3], sym="and", l_symbol=False, r_symbol=False)
            elif p[2] == "or":
                spec = BooleanDisjunctiveEvaluatee(self.owner, p[1], p[3], sym="or", l_symbol=False, r_symbol=False)
            else:
                raise NetworkParserError(p)
            p[0] = spec
        elif len(p) == 5:
            spec = BooleanNegatee(self.owner, p[3])
            p[0] = spec
        else:
            raise NetworkParserError(p)

    def p_reachability_network(self, p):
        """
        reachability_network : forward_network
        reachability_network : backward_network
        """
        p[0] = p[1]

    # forwardnetwork
    def p_forward_network(self, p):
        """
        forward_network : node_spec outreaches
        """
        if len(p) == 3:
            p[0] = ReachabilitySpecification(self.owner, p[1])
            p[0].set_reaches(p[2])

    # backwardnetwork
    def p_backward_network(self, p):
        """
        backward_network : node_spec inreaches
        """
        if len(p) == 2:
            p[0] = ReachabilitySpecification(self.owner, p[1])
        elif len(p) == 3:
            p[0] = ReachabilitySpecification(self.owner, p[1])
            p[0].set_reaches(p[2])

    # ambiguous_spec
    def p_ambiguous_spec(self, p):
        """
        ambiguous_spec : SYMBOL EQUAL     arith_lopr
        ambiguous_spec : SYMBOL EQUAL     string
        ambiguous_spec : SYMBOL EQUAL     bool
        ambiguous_spec : SYMBOL DIFFERENT arith_lopr
        ambiguous_spec : SYMBOL DIFFERENT string
        ambiguous_spec : SYMBOL DIFFERENT bool
        ambiguous_spec : SYMBOL MATCH     REPATTERN
        ambiguous_spec : SYMBOL UNMATCH   REPATTERN
        ambiguous_spec : SYMBOL GREATER_THAN arith_lopr
        ambiguous_spec : SYMBOL GREATER_OR_EQUAL arith_lopr
        ambiguous_spec : SYMBOL LESS_THAN arith_lopr
        ambiguous_spec : SYMBOL LESS_OR_EQUAL arith_lopr
        ambiguous_spec : NOT  ambiguous_spec
        ambiguous_spec : LPAR ambiguous_spec RPAR
        ambiguous_spec : ambiguous_spec AND ambiguous_spec
        ambiguous_spec : ambiguous_spec OR  ambiguous_spec
        """
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = BooleanNegatee(self.owner, p[2])
        elif len(p) == 4:
            if p[1] == "(":
                p[0] = p[2]
            elif p[2] == "==":
                if type(p[1]) is str:
                    p[0] = BooleanEqualityEvaluatee(self.owner, p[1], p[3], sym="==", l_symbol=True, r_symbol=False)
                else:
                    p[0] = BooleanEqualityEvaluatee(self.owner, p[1], p[3], sym="==", l_symbol=False, r_symbol=False)
            elif p[2] == "!=":
                if type(p[1]) is str:
                    p[0] = BooleanDifferenceEvaluatee(self.owner, p[1], p[3], sym="!=", l_symbol=True, r_symbol=False)
                else:
                    p[0] = BooleanDifferenceEvaluatee(self.owner, p[1], p[3], sym="!=", l_symbol=False, r_symbol=False)
            elif p[2] == "=~":
                if type(p[1]) is str:
                    p[0] = BooleanMatchee(self.owner, p[1], p[3], sym="=~", l_symbol=True, r_symbol=False)
                else:
                    p[0] = BooleanMatchee(self.owner, p[1], p[3], sym="=~", l_symbol=False, r_symbol=False)
            elif p[2] == "!=~":
                if type(p[1]) is str:
                    p[0] = BooleanUnmatchee(self.owner, p[1], p[3], sym="!=~", l_symbol=True, r_symbol=False)
                else:
                    p[0] = BooleanUnmatchee(self.owner, p[1], p[3], sym="!=~", l_symbol=False, r_symbol=False)
            elif p[2] == "<":
                if type(p[1]) is str:
                    p[0] = BooleanLessThanEvaluatee(self.owner, p[1], p[3], sym="<", l_symbol=True, r_symbol=False)
                else:
                    p[0] = BooleanLessThanEvaluatee(self.owner, p[1], p[3], sym="<", l_symbol=False, r_symbol=False)
            elif p[2] == "<=":
                if type(p[1]) is str:
                    p[0] = BooleanLessOrEqualsEvaluatee(self.owner, p[1], p[3], sym="<=", l_symbol=True, r_symbol=False)
                else:
                    p[0] = BooleanLessOrEqualsEvaluatee(self.owner, p[1], p[3], sym="<=", l_symbol=False, r_symbol=False)
            elif p[2] == ">":
                if type(p[1]) is str:
                    p[0] = BooleanGreaterThanEvaluatee(self.owner, p[1], p[3], sym=">", l_symbol=True, r_symbol=False)
                else:
                    p[0] = BooleanGreaterThanEvaluatee(self.owner, p[1], p[3], sym=">", l_symbol=False, r_symbol=False)
            elif p[2] == ">=":
                if type(p[1]) is str:
                    p[0] = BooleanGreaterOrEqualsEvaluatee(self.owner, p[1], p[3], sym=">=", l_symbol=True,
                                                           r_symbol=False)
                else:
                    p[0] = BooleanGreaterOrEqualsEvaluatee(self.owner, p[1], p[3], sym=">=", l_symbol=False,
                                                           r_symbol=False)
            elif p[2] == "and":
                p[0] = BooleanConjunctiveEvaluatee(self.owner, p[1], p[3], sym="and", l_symbol=True, r_symbol=False)
            elif p[2] == "or":
                p[0] = BooleanDisjunctiveEvaluatee(self.owner, p[1], p[3], sym="or", l_symbol=False, r_symbol=False)
            else:
                raise NetworkParserError(p)
        else:
            raise NetworkParserError(p)
        # """
        # ambiguous_spec : reference
        # ambiguous_spec : reference EQUAL     arith_lopr
        # ambiguous_spec : reference EQUAL     string
        # ambiguous_spec : reference EQUAL     bool
        # ambiguous_spec : reference DIFFERENT arith_lopr
        # ambiguous_spec : reference DIFFERENT string
        # ambiguous_spec : reference DIFFERENT bool
        # ambiguous_spec : reference MATCH     REPATTERN
        # ambiguous_spec : reference UNMATCH   REPATTERN
        # ambiguous_spec : reference GREATER_THAN arith_lopr
        # ambiguous_spec : reference GREATER_OR_EQUAL arith_lopr
        # ambiguous_spec : reference LESS_THAN arith_lopr
        # ambiguous_spec : reference LESS_OR_EQUAL arith_lopr
        # ambiguous_spec : NOT  ambiguous_spec
        # ambiguous_spec : LPAR ambiguous_spec RPAR
        # ambiguous_spec : ambiguous_spec AND ambiguous_spec
        # ambiguous_spec : ambiguous_spec OR  ambiguous_spec
        # """

    # spec
    def p_spec(self, p):
        """
        spec : ambiguous_spec
        """
        p[0] = p[1]

    # spec_list
    def p_spec_list(self, p):
        """
        spec_list : spec
        spec_list : spec_list COMMA spec
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[1].append(p[3])
            p[0] = p[1]

    # node spec
    def p_node_spec(self, p):
        """
        node_spec : empty_list
        node_spec : LBRACE spec RBRACE
        """
        if len(p) == 2:
            p[0] = BooleanUnaryEvaluatee(self.owner, True)
        elif len(p) == 4:
            p[0] = p[2]
        else:
            raise NetworkParserError(p)

    # outedge
    def p_outedge(self, p):
        """
        outedge : HIPHON empty_list OUTBOUND
        outedge : HIPHON LBRACE spec RBRACE OUTBOUND
        """
        if len(p) == 4:
            p[0] = BooleanUnaryEvaluatee(self.owner, True)
        elif len(p) == 5:
            p[0] = p[3]
        else:
            raise NetworkParserError(p)

    # inedge
    def p_inedge(self, p):
        """
        inedge : INBOUND empty_list HIPHON
        inedge : INBOUND LBRACE bool_evaluable RBRACE HIPHON
        """
        if len(p) == 5:
            p[0] = BooleanUnaryEvaluatee(self.owner, True)
        elif len(p) == 6:
            p[0] = p[3]
        else:
            raise NetworkParserError(p)

    # numbercombination
    def p_numbercombination(self, p):
        """
        numbercombination : NUMBER
        numbercombination : NUMBER DOUBLEPERIOD NUMBER
        numbercombination : NUMBER DOUBLEPERIOD
        numbercombination : numbercombination COMMA numbercombination
        """
        if len(p) == 2:
            p[0] = Numberset(int(p[1]))
        elif len(p) == 3:
            start = int(p[1])
            N = Numberset(start)
            I = Interval(start)
            I.infinitize()
            N.add_interval(I)
            p[0] = N
        elif len(p) == 4:
            if p[1] is Numberset:
                p[0] = p[1]
                for i in p[3].intervals:
                    p[0].add_interval(i)
            else:
                p[0] = Numberset(int(p[1]))
                p[0].add_interval(Interval(int(p[1]), int(p[3])))
        else:
            raise NetworkParserError(p)

    # numberset
    def p_numberset(self, p):
        """
        numberset : LBRACKET numbercombination RBRACKET
        """
        p[0] = p[2]

    def p_outreach(self, p):
        """
        outreach : outedge node_spec
        outreach : LPAR outreach RPAR numberset
        outreach : outreach outreach
        """
        constructor = ReachNetworkConstructor()
        if len(p) == 3:
            if isinstance(p[2], GenericEvaluatee):
                p[0] = constructor.simple_reach(True, p[1], p[2], Numberset(1))
            else:
                p[0] = constructor.extend(p[1], p[2], Numberset(1))
        elif len(p) == 5:
            p[0] = constructor.multiply(p[2], p[4])

    # reach
    def p_outreaches(self, p):
        """
        outreaches : outreach
        """
        if len(p) == 2:
            p[0] = p[1]

    # reach
    def p_inreach(self, p):
        """
        inreach : inedge node_spec
        inreach : numberset LPAR inreach RPAR
        inreach : inreach inreach
        """
        constructor = ReachNetworkConstructor()
        if len(p) == 3:
            if isinstance(p[1], Validatee):
                p[0] = constructor.simple_reach(True, p[1], p[2], Numberset(1))
            else:
                p[0] = constructor.extend(p[1], p[2], Numberset(1))
        elif len(p) == 5:
            p[0] = constructor.multiply(p[2], p[4])
        else:
            raise NetworkParserError(p)

    def p_inreaches(self, p):
        """
        inreaches : inreach
        """
        p[0] = p[1]

    # if error occurred
    def p_error(self, p):
        print('Syntax error: %d: %d: %r' % (p.lineno, p.lexpos, p.value))
        raise NetworkParserError(p)

    def __init__(self, owner):
        self._owner = owner
        self._lexer = RequirementSyntacticAnalyzer()
        self.lexer = self._lexer.lexer
        self.parser = yacc.yacc(module=self)

    @property
    def owner(self):
        return self._owner

    def check_syntax(self, text):
        self._lexer.build()
        self._lexer.test(text)

    def parse_script(self, text):
        result = self.parser.parse(text, lexer=self.lexer)
        return result


def main():
    m = RequirementSyntacticAnalyzer()
    m.build()
    p = RequirementParser(m)
    while True:
        try:
            txt = input("script-> ")
            if txt == "exit" or txt == "quit":
                break
            m.test(txt)
            rs = p.parse_script(txt)
            if rs is None:
                continue
            for r in rs:
                print(r)
        except Exception as ex:
            print(traceback.format_exc())
    pass


if __name__ == "__main__":
    main()
