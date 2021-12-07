# -*- coding: utf-8 -*-

import ply.lex as lex
import ply.yacc as yacc
import traceback
# import re
# import sys
# import networkx as nx
# import openpyxl
# import os
# import json
# import sys
# import inspect
# from enum import Enum

# import our modules
from networkml.generic import GenericEvaluatee
from networkml.error import NetworkError, NetworkParserError, NetworkLexerError
from networkml.validator import Validatee, ArithmeticModulusEvaluatee, ArithmeticMultiplicableEvaluatee
from networkml.validator import ArithmeticSubtractalEvaluatee, ArithmeticBinaryEvaluatee, ArithmeticAdditionalEvaluatee
from networkml.validator import ArithmeticDivideEvaluatee, ArithmeticBinaryEvaluatee
from networkml.validator import BooleanNegatee, BooleanBinaryEvaluatee
from networkml.validator import BooleanConjunctiveEvaluatee, BooleanDisjunctiveEvaluatee, BooleanGreaterOrEqualsEvaluatee
from networkml.validator import BooleanGreaterThanEvaluatee, BooleanLessOrEqualsEvaluatee, BooleanLessThanEvaluatee
from networkml.validator import BooleanEqualityEvaluatee, BooleanDifferenceEvaluatee, BooleanMatchee, BooleanUnmatchee
from networkml.validator import BooleanUnaryEvaluatee, TrueEvaluatee
from networkml.network import NetworkClassInstance, NetworkMethodCaller, WhileStatement, IfElifElseStatement
from networkml.network import ReachabilitySpecification, NetworkBreak
from networkml.network import NetworkMethod, ForeachStatement, NetworkSubstituter
from networkml.network import ReachNetworkConstructor, Interval, SimpleVariable, NetworkReturn
from networkml.network import Interval, Numberset, NumbersetOperator, CommandOption
from networkml.network import NetworkSymbol


class NetworkLexer:

    # Word analysis
    reserved = {
        'if': 'IF',
        'elif': 'ELIF',
        'else': 'ELSE',
        'while': 'WHILE',
        'for': 'FOR',
        'this': 'THIS',
        'class': 'CLASS',
        'function': 'FUNC',
        'return': 'RETURN',
        'break': 'BREAK',
        'global': 'GLOBAL',
        'private': 'PRIVATE',
        'protected': 'PROTECTED',
        'public': 'PUBLIC',
        'property': 'PROPERTY',
        'read': 'READ',
        'write': 'WRITE',
        'and': 'AND',
        'or': 'OR',
        'not': 'NOT',
        'null': 'NULL',
        'true': 'TRUE',
        'True': 'UTRUE',
        'false': 'FALSE',
        'False': 'UFALSE',
        '$initializer': 'INITIALIZER',
        # '$self': 'SELF',
        # '$generator': 'GENERATOR',
        # '$manager': 'MANAGER',
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
              # 'DOUBLEQUOTE',
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
    t_FOR = r"for"
    t_WHILE = r"while"
    t_IF = r"if"
    t_ELIF = r"elif"
    t_ELSE = r"else"
    t_REPATTERN = r"/[^/]+/"
    t_PLUS = r"\+"
    t_MINUS = r"\-"
    t_MULTIPLY = r"\*"
    t_DIVIDE = r"\/"
    t_MOD = r"\%"
    t_RETURN = r"return"
    t_BREAK = r"break"
    t_GLOBAL = r"global"
    t_CLASS = r"class"
    t_FUNC = r"function"
    t_PROPERTY = r"property"
    t_READ = r"read"
    t_WRITE = r"write"
    t_INITIALIZER = r"\$initializer"

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
    t_HIERARCH_SYMBOL = r"(\$self|\$generator|\$manager|[a-zA-Z_]+[a-zA-Z_0-9]*)(\.[a-zA-Z_]+[a-zA-Z_0-9])*"
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
    t_OPTION = r"\-{1,2}[a-zA-Z]+([_]+[a-zA-Z0-9]+)*"
    t_DOUBLEPERIOD = r"\.\."
    t_AND = r"and"
    t_OR = r"or"
    t_NOT = r"not"
    t_HIPHON = r"\-+"
    t_OUTBOUND = r"\-+>"
    t_INBOUND = r"<\-+"
    t_COMMA = r","
    t_TRUE = r"true"
    t_FALSE = r"false"
    t_UTRUE = r"True"
    t_UFALSE = r"False"
    # t_PERIOD = r"\."
    t_SUBST = r"="
    # t_DOUBLEQUOTE = r"\""
    t_SEMICORON = r";"
    # t_SELF = r"\$self"
    # t_GENERATOR = r"\$generator"
    # t_MANAGER = r"\$manager"

    # initializer
    def __init__(self):
        self.lexer = lex.lex(module=self)

    def t_error(self, t):
        # _print("Illegal character {}".format(t.value[0]))
        t.lexer.skip(1)

    def build(self, **kwargs):
        self._lexer = lex.lex(module=self, **kwargs)

    def test(self, data):
        self._lexer.input(data)
        while True:
            tok = self._lexer.token()
            if not tok:
                break
            print(tok)


class NetworkParser:

    # Parsing rules
    tokens = NetworkLexer.tokens

    def p_world_program(self, p):
        """
        world_program : program
        """
        p[0] = p[1]

    def p_program(self, p):
        """
        program : class_declaration
        program : func_declaration
        program : global_func_declaration
        program : single_execution
        program : program program
        """
        if len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 3:
            if type(p[2]) is str:
                p[0] = [p[1]]
            else:
                p[1].extend(p[2])
                p[0] = p[1]

    def p_class_declaration(self, p):
        """
        class_declaration : CLASS SYMBOL LBRACKET initializer_decl class_member_declarations RBRACKET
        class_declaration : CLASS SYMBOL LPAR SYMBOL RPAR LBRACKET initializer_decl class_member_declarations RBRACKET
        """
        if len(p) == 7:
            # clazz = NetworkClassInstance(None, p[1], self.owner, super_class=None, lexdata=p.lexer.lexdata)
            clazz = NetworkClassInstance(None, p[1], self.owner, super_class=None)
            self.init_clazz(clazz, p[4], p[5])
        elif len(p) == 10:
            # clazz = NetworkClassInstance(None, p[1], self.owner, super_class=p[4], init_args=(), lexdata=p.lexer.lexdata)
            clazz = NetworkClassInstance(None, p[1], self.owner, super_class=p[4])
            self.init_clazz(clazz, p[7], p[8])
        else:
            raise NetworkParserError(p)
        p[0] = clazz

    def p_initializer_decl(self, p):
        """
        initializer_decl : INITIALIZER empty_tuple      LBRACKET executions RBRACKET
        initializer_decl : INITIALIZER func_args_tuple  LBRACKET executions RBRACKET
        """
        method = NetworkMethod(self.owner, p[1], args=p[2], stmts=p[4], globally=False, lexdata=p.lexer.lexdata)
        p[0] = method

    def p_class_member_declarations(self, p):
        """
        class_member_declarations : property_declaration
        class_member_declarations : func_declaration
        class_member_declarations : executions
        class_member_declarations : class_declaration
        class_member_declarations : class_member_declarations class_member_declarations
        """
        if len(p) == 2:
            if type(p[1]) is list:
                p[0] = p[1]
            else:
                p[0] = [p[1]]
        elif len(p) == 3:
            p[1].extend(p[2])
            p[0] = p[1]
        else:
            raise NetworkParserError(p)

    def p_property_declaration(self, p):
        """
        property_declaration : PROPERTY SYMBOL             LBRACKET executions RBRACKET
        property_declaration : PROPERTY SYMBOL READ        LBRACKET executions RBRACKET
        property_declaration : PROPERTY SYMBOL      WRITE  LBRACKET executions RBRACKET
        property_declaration : PROPERTY SYMBOL READ WRITE  LBRACKET executions RBRACKET
        """
        if len(p) == 6:
            method = NetworkMethod(self.owner, p[2], args=p[3], stmts=p[5], globally=False, lexdata=p.lexer.lexdata)
            p[0] = method
        elif len(p) == 7:
            method = NetworkMethod(self.owner, p[2], args=p[3], stmts=p[5], globally=False, lexdata=p.lexer.lexdata)
            p[0] = method
        elif len(p) == 8:
            method = NetworkMethod(self.owner, p[2], args=p[3], stmts=p[5], globally=False, lexdata=p.lexer.lexdata)
            p[0] = method
        else:
            raise NetworkParserError(p)

    def p_func_declaration(self, p):
        """
        func_declaration : FUNC SYMBOL empty_tuple      LBRACKET executions RBRACKET
        func_declaration : FUNC SYMBOL func_args_tuple  LBRACKET executions RBRACKET
        """
        if len(p) == 7:
            method = NetworkMethod(self.owner, p[2], args=p[3], stmts=p[5], globally=False, lexdata=p.lexer.lexdata)
            p[0] = method
        else:
            raise NetworkParserError(p)

    def p_global_func_declaration(self, p):
        """
        global_func_declaration : GLOBAL FUNC SYMBOL empty_tuple     LBRACKET executions RBRACKET
        global_func_declaration : GLOBAL FUNC SYMBOL func_args_tuple LBRACKET executions RBRACKET
        """
        if len(p) == 8:
            method = NetworkMethod(self.owner, p[3], args=p[4], stmts=p[6], globally=True, lexdata=p.lexer.lexdata)
            p[0] = method
        else:
            raise NetworkParserError(p)

    def p_func_arg_option(self, p):
        """
        func_arg_option : OPTION
        """
        option = CommandOption(p[1], has_assignee=False)
        p[0] = option

    def p_func_arg_options(self, p):
        """
        func_arg_options : func_arg_option
        func_arg_options : func_arg_options  COMMA  func_arg_option
        """
        if len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 4:
            p[0] = p[1]
            p[0].append(p[3])
        else:
            raise NetworkParserError(p)

    def p_func_args_tuple(self, p):
        """
        func_args_tuple : empty_tuple
        func_args_tuple : func_opened_args_tuple RPAR
        func_args_tuple : func_opened_args_tuple COMMA func_arg_options RPAR
        """
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = p[1]
        elif len(p) == 5:
            p[0] = p[1]
            options = p[3]
            p[0].append(options)
        else:
            raise NetworkParserError(p)

    def p_func_opened_args_tuple(self, p):
        """
        func_opened_args_tuple : LPAR  SYMBOL
        func_opened_args_tuple : func_opened_args_tuple COMMA SYMBOL
        """
        # print("method_opened_args_tuple")
        if len(p) == 3:
            p[0] = [p[2]]
        elif len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        else:
            raise NetworkParserError(p)

    def p_single_execution(self, p):
        """
        single_execution : subst       SEMICORON
        single_execution : method_call SEMICORON
        single_execution : return      SEMICORON
        single_execution : break       SEMICORON
        single_execution : while_statement
        single_execution : for_statement
        single_execution : if_statement
        """
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = p[1]
        else:
            raise NetworkParserError(p)

    def p_executions(self, p):
        """
        executions : single_execution
        executions : executions  executions
        """
        if len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 3:
            p[1].extend(p[2])
            p[0] = p[1]
        else:
            raise NetworkParserError(p)

    def p_substitutee(self, p):
        """
        substitutee : reference
        """
        var = p[1]
        p[0] = var

    def p_symbol(self, p):
        """
        symbol : SYMBOL
        """
        var = NetworkSymbol(self.owner, p[1])
        p[0] = var

    def p_hierarch_symbol(self, p):
        """
        hierarch_symbol : HIERARCH_SYMBOL
        """
        var = NetworkSymbol(self.owner, p[1])
        p[0] = var

    def p_complex_symbol(self, p):
        """
        complex_symbol : symbol            LBRACE NUMBER  RBRACE
        complex_symbol : symbol            LBRACE SYMBOL  RBRACE
        complex_symbol : symbol            LBRACE LITERAL RBRACE
        complex_symbol : hierarch_symbol   LBRACE NUMBER  RBRACE
        complex_symbol : hierarch_symbol   LBRACE SYMBOL  RBRACE
        complex_symbol : hierarch_symbol   LBRACE LITERAL RBRACE
        complex_symbol : complex_symbol    LBRACE NUMBER  RBRACE
        complex_symbol : complex_symbol    LBRACE SYMBOL  RBRACE
        complex_symbol : complex_symbol    LBRACE LITERAL RBRACE
        """
        var = p[1]
        sym = "{}[{}]".format(var.symbol, p[3])
        var.set_symbol(sym)
        p[0] = var

    def p_subst_callee(self, p):
        """
        subst_callee : method_call
        subst_callee : arith_oper
        subst_callee : int
        subst_callee : float
        subst_callee : string
        subst_callee : bool
        subst_callee : bool_evaluable
        subst_callee : empty_tuple
        subst_callee : empty_list
        subst_callee : empty_hash
        subst_callee : null
        subst_callee : reference
        subst_callee : reachability_network
        subst_callee : method_args_tuple
        subst_callee : LPAR spec RPAR
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[2]

    def p_subst(self, p):
        """
        subst : GLOBAL substitutee SUBST subst_callee
        subst :        substitutee SUBST subst_callee
        """
        if len(p) == 5:
            globally = True
            writee = p[2]
            callee = p[4]
        else:
            globally = False
            writee = p[1]
            callee = p[3]
        subst = NetworkSubstituter(self.owner, writee, callee, globally=globally)
        p[0] = subst

    def p_natural_number(self, p):
        """
        natural_number : NUMBER
        """
        p[0] = int(p[1])

    def p_empty_tuple(self, p):
        """
        empty_tuple : LPAR RPAR
        """
        p[0] = ()

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

    def p_literal(self, p):
        """
        literal : LITERAL
        """
        p[0] = p[1]

    def p_string(self, p):
        """
        string : LITERAL
        """
        s = p[1][1:len(p[1])-1]
        s = s.replace('""', '"')
        s = s.replace("\\n", "\n")
        p[0] = s

    def p_bool(self, p):
        """
        bool : true
        bool : false
        """
        p[0] = bool(p[1])

    def p_true(self, p):
        """
        true : TRUE
        true : UTRUE
        """
        p[0] = True

    def p_false(self, p):
        """
        false : FALSE
        false : UFALSE
        """
        p[0] = False

    def p_null(self, p):
        """
        null : NULL
        """
        p[0] = None

    def p_reference(self, p):
        """
        reference : symbol
        reference : hierarch_symbol
        reference : complex_symbol
        """
        p[0] = p[1]

    def p_args_tuple(self, p):
        """
        args_tuple : func_args_tuple
        args_tuple : empty_tuple
        """
        if type(p[1]) is str:
            args = []
            for a in p[1]:
                args.append(SimpleVariable(self.owner, a, None))
        else:
            args = p[1]
        p[0] = args

    def p_method_args_tuple(self, p):
        """
        method_args_tuple : empty_tuple
        method_args_tuple : method_opened_args_tuple RPAR
        method_args_tuple : method_opened_args_tuple COMMA options RPAR
        """
        if len(p) == 2:
            p[0] = []
        elif len(p) == 3:
            p[0] = p[1]
        elif len(p) == 5:
            p[0] = p[1]
            options = p[3]
            p[0].append(options)
        else:
            raise NetworkParserError(p)

    def p_method_arg_tuple_condidate(self, p):
        """
        method_arg_tuple_condidate : int
        method_arg_tuple_condidate : float
        method_arg_tuple_condidate : string
        method_arg_tuple_condidate : bool
        method_arg_tuple_condidate : null
        method_arg_tuple_condidate : option
        method_arg_tuple_condidate : reference
        method_arg_tuple_condidate : arith_oper
        method_arg_tuple_condidate : empty_list
        method_arg_tuple_condidate : empty_hash
        method_arg_tuple_condidate : argumental_spec_list
        method_arg_tuple_condidate : spec_assignments
        method_arg_tuple_condidate : method_call
        method_arg_tuple_condidate : method_args_tuple
        """
        p[0] = p[1]

    def p_argumental_spec_list(self, p):
        """
        argumental_spec_list : LBRACKET spec_list RBRACKET
        argumental_spec_list : LBRACE   spec_list RBRACE
        """
        p[0] = p[2]

    def p_method_opened_args_tuple(self, p):
        """
        method_opened_args_tuple : LPAR  method_arg_tuple_condidate
        method_opened_args_tuple : method_opened_args_tuple COMMA method_arg_tuple_condidate
        """
        if len(p) == 3:
            p[0] = [p[2]]
        elif len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        else:
            raise NetworkParserError(p)

    def p_break(self, p):
        """
        break : BREAK
        """
        brk = NetworkBreak(self.owner)
        p[0] = brk

    def p_return(self, p):
        """
        return : RETURN
        return : RETURN returnee
        """
        if len(p) == 2:
            returnee = None
        else:
            returnee = p[2]
        subst = NetworkReturn(self.owner, returnee)
        subst.closer = True
        p[0] = subst

    def p_returnee(self, p):
        """
        returnee : int
        returnee : literal
        returnee : float
        returnee : bool
        returnee : null
        returnee : reference
        """
        p[0] = p[1]

    def p_for_statement(self, p):
        """
        for_statement : FOR symbol symbol single_execution
        for_statement : FOR symbol symbol LBRACKET executions RBRACKET
        """
        if len(p) == 5:
            fetch = p[2]
            fetchee = p[3]
            stmt = ForeachStatement(self.owner, fetch, fetchee)
            stmt.set_statements((p[4]))
            p[0] = stmt
        elif len(p) == 7:
            fetch = p[2]
            fetchee = p[3]
            stmt = ForeachStatement(self.owner, fetch, fetchee)
            stmt.set_statements(p[5])
            p[0] = stmt

    def p_while_statement(self, p):
        """
        while_statement : WHILE LPAR condition RPAR single_execution
        while_statement : WHILE LPAR condition RPAR LBRACKET executions RBRACKET
        """
        if len(p) == 6:
            cond = p[3]
            stmt = WhileStatement(self.owner, cond)
            stmt.set_statements((p[5]))
            p[0] = stmt
        elif len(p) == 8:
            cond = p[3]
            stmt = WhileStatement(self.owner, cond)
            stmt.set_statements(p[6])
            p[0] = stmt

    def p_if_statement(self, p):
        """
        if_statement : open_if_statement
        if_statement : open_if_statement ELSE single_execution
        if_statement : open_if_statement ELSE LBRACKET executions RBRACKET
        """
        if len(p) == 2:
            p[0] = p[1]
        if len(p) == 4:
            stmt: IfElifElseStatement = p[1]
            stmt.append_else_statements((p[3]))
            p[0] = stmt
        elif len(p) == 6:
            stmt: IfElifElseStatement = p[1]
            stmt.append_else_statements(p[4])
            p[0] = stmt

    def p_open_if_statement(self, p):
        """
        open_if_statement : IF LPAR condition RPAR single_execution
        open_if_statement : IF LPAR condition RPAR LBRACKET executions RBRACKET
        open_if_statement : open_if_statement ELIF LPAR bool_evaluable RPAR single_execution
        open_if_statement : open_if_statement ELIF LPAR bool_evaluable RPAR LBRACKET executions RBRACKET
        """
        if len(p) == 6:
            stmt = IfElifElseStatement(self.owner)
            cond = p[3]
            stmt.append_if_elif_statements(cond, (p[5]))
            p[0] = stmt
        elif len(p) == 8:
            stmt = IfElifElseStatement(self.owner)
            cond = p[3]
            stmt.append_if_elif_statements(cond, p[6])
            p[0] = stmt
        elif len(p) == 7:
            stmt = p[1]
            cond = p[4]
            stmt.append_if_elif_statements(cond, (p[6]))
            p[0] = stmt
        elif len(p) == 9:
            stmt: IfElifElseStatement = p[1]
            cond = p[4]
            stmt.append_if_elif_statements(cond, p[7])
            p[0] = stmt
        else:
            raise NetworkParserError(p)

    def p_condition(self, p):
        """
        condition : bool
        condition : bool_evaluable
        """
        if type(p[1]) is bool:
            cond = BooleanUnaryEvaluatee(self.owner, p[1])
        else:
            cond = p[1]
        p[0] = cond

    def p_bool_evaluable(self, p):
        """
        bool_evaluable : ambiguous_spec
        """
        p[0] = p[1]

    def p_method_argumental_tuple(self, p):
        """
        method_argumental_tuple : empty_tuple
        method_argumental_tuple : method_args_tuple
        """
        p[0] = p[1]

    def p_method_call(self, p):
        """
        method_call : reference          method_argumental_tuple
        """
        p[0] = NetworkMethodCaller(self.owner, p[1], p[2])

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
            ev = p[2]
        elif p[2] == "+":
            if type(p[1]) is int or type(p[1]) is float:
                l_symbol = False
            else:
                l_symbol = True
            if type(p[3]) is int or type(p[3]) is float:
                r_symbol = False
            else:
                r_symbol = True
            ev = ArithmeticAdditionalEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        elif p[2] == "-":
            if type(p[1]) is int or type(p[1]) is float:
                l_symbol = False
            else:
                l_symbol = True
            if type(p[3]) is int or type(p[3]) is float:
                r_symbol = False
            else:
                r_symbol = True
            ev = ArithmeticSubtractalEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        elif p[2] == "*":
            if type(p[1]) is int or type(p[1]) is float:
                l_symbol = False
            else:
                l_symbol = True
            if type(p[3]) is int or type(p[3]) is float:
                r_symbol = False
            else:
                r_symbol = True
            ev = ArithmeticMultiplicableEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        elif p[2] == "/":
            if type(p[1]) is int or type(p[1]) is float:
                l_symbol = False
            else:
                l_symbol = True
            if type(p[3]) is int or type(p[3]) is float:
                r_symbol = False
            else:
                r_symbol = True
            ev = ArithmeticDivideEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        elif p[2] == "%":
            if type(p[1]) is int or type(p[1]) is float:
                l_symbol = False
            else:
                l_symbol = True
            if type(p[3]) is int or type(p[3]) is float:
                r_symbol = False
            else:
                r_symbol = True
            ev = ArithmeticModulusEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        else:
            raise NetworkParserError(p)
        p[0] = ev

    def p_arith_lopr(self, p):
        """
        arith_lopr : int
        arith_lopr : float
        arith_lopr : reference
        """
        p[0] = p[1]

    def p_arith_ropr(self, p):
        """
        arith_ropr : nonnegative_int
        arith_ropr : nonnegative_float
        arith_ropr : reference
        """
        p[0] = p[1]

    def p_opened_optional_tuple(self, p):
        """
        opened_optional_tuple : LPAR option
        opened_optional_tuple : opened_optional_tuple COMMA option
        """
        if len(p) == 3:
            p[0] = [p[2]]
        elif len(p) == 4:
            p[0] = p[1]
            p[0].append(p[3])
        else:
            raise NetworkParserError(p)

    def p_optional_tuple(self, p):
        """
        optional_tuple : opened_optional_tuple RPAR
        """
        p[0] = tuple(p[1])

    def p_option_assignee(self, p):
        """
        option_assignee : reference
        option_assignee : int
        option_assignee : float
        option_assignee : bool
        option_assignee : literal
        option_assignee : numberset
        option_assignee : empty_list
        option_assignee : empty_tuple
        option_assignee : method_args_tuple
        option_assignee : LPAR spec_list RPAR
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = tuple(p[2])

    def p_option(self, p):
        """
        option : OPTION
        option : OPTION SUBST option_assignee
        """
        if len(p) == 2:
            p[0] = CommandOption(p[1], None, has_assignee=False, symbolic_assignee=False)
        elif len(p) == 4:
            if type(p[1]) is str and p[1][0] == "\"" and p[1][len(p[1])-1] == "\"":
                symbolic = True
            elif isinstance(p[1], NetworkSymbol):
                symbolic = True
            else:
                symbolic = False
            p[0] = CommandOption(p[1], p[3], has_assignee=True, symbolic_assignee=symbolic)
        else:
            raise NetworkParserError(p)

    def p_options(self, p):
        """
        options : option
        options : options COMMA option
        """
        if len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 4:
            p[0] = p[1]
            p[0].append(p[3])
        else:
            raise NetworkParserError(p)

    def p_file(self, p):
        """
        file : string
        """
        p[0] = p[1]

    def p_spec_symbolic_operand(self, p):
        """
        spec_symbolic_operand : reference
        """
        p[0] = p[1]

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
        if type(p[1]) is NetworkSymbol:
            l_symbol = True
        else:
            l_symbol = False
        if type(p[3]) is NetworkSymbol:
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
        if type(p[1]) is NetworkSymbol:
            l_symbol = True
        else:
            l_symbol = False
        if type(p[3]) is NetworkSymbol:
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanDifferenceEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        p[0] = spec

    def p_gt_spec_assignments(self, p):
        """
        gt_spec_assignments : spec_symbolic_operand GREATER_THAN int
        gt_spec_assignments : spec_symbolic_operand GREATER_THAN float
        gt_spec_assignments : spec_symbolic_operand GREATER_THAN spec_symbolic_operand
        """
        if type(p[1]) is NetworkSymbol:
            l_symbol = True
        else:
            l_symbol = False
        if type(p[3]) is NetworkSymbol:
            r_symbol = True
        spec = BooleanGreaterThanEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        p[0] = spec

    def p_ge_spec_assignments(self, p):
        """
        ge_spec_assignments : spec_symbolic_operand GREATER_OR_EQUAL int
        ge_spec_assignments : spec_symbolic_operand GREATER_OR_EQUAL float
        ge_spec_assignments : spec_symbolic_operand GREATER_OR_EQUAL spec_symbolic_operand
        """
        if type(p[1]) is NetworkSymbol:
            l_symbol = True
        else:
            l_symbol = False
        if type(p[3]) is NetworkSymbol:
            r_symbol = True
        spec = BooleanGreaterOrEqualsEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        p[0] = spec

    def p_le_spec_assignments(self, p):
        """
        le_spec_assignments : spec_symbolic_operand LESS_OR_EQUAL int
        le_spec_assignments : spec_symbolic_operand LESS_OR_EQUAL float
        le_spec_assignments : spec_symbolic_operand LESS_OR_EQUAL spec_symbolic_operand
        """
        if type(p[1]) is NetworkSymbol:
            l_symbol = True
        else:
            l_symbol = False
        if type(p[3]) is NetworkSymbol:
            r_symbol = True
        spec = BooleanLessOrEqualsEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        p[0] = spec

    def p_lt_spec_assignments(self, p):
        """
        lt_spec_assignments : spec_symbolic_operand LESS_THAN int
        lt_spec_assignments : spec_symbolic_operand LESS_THAN float
        lt_spec_assignments : spec_symbolic_operand LESS_THAN spec_symbolic_operand
        """
        if type(p[1]) is NetworkSymbol:
            l_symbol = True
        else:
            l_symbol = False
        if type(p[3]) is NetworkSymbol:
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanLessThanEvaluatee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        p[0] = spec

    def p_match_spec_assignments(self, p):
        """
        match_spec_assignments : spec_symbolic_operand MATCH REPATTERN
        match_spec_assignments : spec_symbolic_operand MATCH spec_symbolic_operand
        """
        if type(p[1]) is NetworkSymbol:
            l_symbol = True
        else:
            l_symbol = False
        if type(p[3]) is NetworkSymbol:
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanMatchee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
        p[0] = spec

    def p_unmatch_spec_assignments(self, p):
        """
        unmatch_spec_assignments : spec_symbolic_operand UNMATCH REPATTERN
        unmatch_spec_assignments : spec_symbolic_operand UNMATCH spec_symbolic_operand
        """
        if type(p[1]) is NetworkSymbol:
            l_symbol = True
        else:
            l_symbol = False
        if type(p[3]) is NetworkSymbol:
            r_symbol = True
        else:
            r_symbol = False
        spec = BooleanUnmatchee(self.owner, p[1], p[3], sym=p[2], l_symbol=l_symbol, r_symbol=r_symbol)
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
        ambiguous_spec : reference EQUAL     arith_lopr
        ambiguous_spec : reference EQUAL     string
        ambiguous_spec : reference EQUAL     bool
        ambiguous_spec : arith_lopr EQUAL reference
        ambiguous_spec : arith_lopr EQUAL arith_lopr
        ambiguous_spec : string     EQUAL reference
        ambiguous_spec : string     EQUAL string
        ambiguous_spec : string     EQUAL bool
        ambiguous_spec : string     EQUAL arith_lopr
        ambiguous_spec : bool       EQUAL reference
        ambiguous_spec : bool       EQUAL bool
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
                if isinstance(p[1], NetworkSymbol):
                    l_symbol = True
                else:
                    l_symbol = False
                # right is symbolic evaluatee
                if isinstance(p[3], NetworkSymbol):
                    r_symbol = True
                else:
                    r_symbol = False
                p[0] = BooleanEqualityEvaluatee(self.owner, p[1], p[3], sym="==", l_symbol=l_symbol, r_symbol=r_symbol)
            elif p[2] == "!=":
                if type(p[1]) is str or isinstance(p[1], NetworkSymbol):
                    l_symbol = True
                else:
                    l_symbol = False
                # right is symbolic evaluatee
                if type(p[3]) is int or type(p[3]) is float or type(p[3]) is str:
                    r_symbol = False
                else:
                    r_symbol = True
                p[0] = BooleanDifferenceEvaluatee(self.owner, p[1], p[3], sym="!=", l_symbol=l_symbol, r_symbol=r_symbol)
            elif p[2] == "=~":
                if type(p[1]) is str or isinstance(p[1], NetworkSymbol):
                    l_symbol = True
                else:
                    l_symbol = False
                # right is symbolic evaluatee
                if type(p[3]) is int or type(p[3]) is float or type(p[3]) is str:
                    r_symbol = False
                else:
                    r_symbol = True
                p[0] = BooleanMatchee(self.owner, p[1], p[3], sym="=~", l_symbol=l_symbol, r_symbol=r_symbol)
            elif p[2] == "!=~":
                if type(p[1]) is str or isinstance(p[1], NetworkSymbol):
                    l_symbol = True
                else:
                    l_symbol = False
                # right is symbolic evaluatee
                if type(p[3]) is int or type(p[3]) is float or type(p[3]) is str:
                    r_symbol = False
                else:
                    r_symbol = True
                p[0] = BooleanUnmatchee(self.owner, p[1], p[3], sym="!=~", l_symbol=l_symbol, r_symbol=r_symbol)
            elif p[2] == "<":
                # left is symbolic evaluatee
                if type(p[1]) is str or isinstance(p[1], NetworkSymbol):
                    l_symbol = True
                    p[0] = BooleanLessThanEvaluatee(self.owner, p[1], p[3], sym="<", l_symbol=True, r_symbol=False)
                else:
                    l_symbol = True
                # right is symbolic evaluatee
                if type(p[3]) is int or type(p[3]) is float:
                    r_symbol = False
                else:
                    r_symbol = True
                p[0] = BooleanLessThanEvaluatee(self.owner, p[1], p[3], sym="<", l_symbol=l_symbol, r_symbol=r_symbol)
            elif p[2] == "<=":
                # left is symbolic evaluatee
                if type(p[1]) is str or isinstance(p[1], NetworkSymbol):
                    l_symbol = True
                    p[0] = BooleanLessThanEvaluatee(self.owner, p[1], p[3], sym="<", l_symbol=True, r_symbol=False)
                else:
                    l_symbol = True
                # right is symbolic evaluatee
                if type(p[3]) is int or type(p[3]) is float:
                    r_symbol = False
                else:
                    r_symbol = True
                p[0] = BooleanLessOrEqualsEvaluatee(self.owner, p[1], p[3], sym="<=", l_symbol=l_symbol, r_symbol=r_symbol)
            elif p[2] == ">":
                # left is symbolic evaluatee
                if type(p[1]) is str or isinstance(p[1], NetworkSymbol):
                    l_symbol = True
                    p[0] = BooleanLessThanEvaluatee(self.owner, p[1], p[3], sym="<", l_symbol=True, r_symbol=False)
                else:
                    l_symbol = True
                # right is symbolic evaluatee
                if type(p[3]) is int or type(p[3]) is float:
                    r_symbol = False
                else:
                    r_symbol = True
                p[0] = BooleanGreaterThanEvaluatee(self.owner, p[1], p[3], sym=">", l_symbol=l_symbol, r_symbol=r_symbol)
            elif p[2] == ">=":
                # left is symbolic evaluatee
                if type(p[1]) is str or isinstance(p[1], NetworkSymbol):
                    l_symbol = True
                    p[0] = BooleanLessThanEvaluatee(self.owner, p[1], p[3], sym="<", l_symbol=True, r_symbol=False)
                else:
                    l_symbol = True
                # right is symbolic evaluatee
                if type(p[3]) is int or type(p[3]) is float:
                    r_symbol = False
                else:
                    r_symbol = True
                p[0] = BooleanGreaterOrEqualsEvaluatee(self.owner, p[1], p[3], sym=">=", l_symbol=l_symbol,
                                                       r_symbol=r_symbol)
            elif p[2] == "and":
                l_symbol = True
                r_symbol = True
                p[0] = BooleanConjunctiveEvaluatee(self.owner, p[1], p[3], sym="and", l_symbol=l_symbol, r_symbol=r_symbol)
            elif p[2] == "or":
                l_symbol = True
                r_symbol = True
                p[0] = BooleanDisjunctiveEvaluatee(self.owner, p[1], p[3], sym="or", l_symbol=l_symbol, r_symbol=r_symbol)
            else:
                raise NetworkParserError(p)
        else:
            raise NetworkParserError(p)

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
            p[0] = TrueEvaluatee(self.owner)
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
            p[0] = TrueEvaluatee(self.owner)
        elif len(p) == 6:
            p[0] = p[3]
        else:
            raise NetworkParserError(p)

    # inedge
    def p_inedge(self, p):
        """
        inedge : INBOUND empty_list HIPHON
        inedge : INBOUND LBRACE bool_evaluable RBRACE HIPHON
        """
        if len(p) == 4:
            p[0] = TrueEvaluatee(self.owner)
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
        else:
            raise NetworkParserError(p)

    # reach
    def p_outreaches(self, p):
        """
        outreaches : outreach
        """
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
        raise NetworkLexerError(p)

    def __init__(self, owner):
        self._owner = owner
        self._lexer = NetworkLexer()
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
    m = NetworkLexer()
    m.build()
    p = NetworkParser(m)
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
