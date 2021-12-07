# -*- coding:utf-8 -*-

import ply.lex as lex
import ply.yacc as yacc
import re
import sys
import enum
from NetworkML import interpret
# from enspecparser import EnSpecParser, EnSpecParserError, EnSpecLexerError
import nltk
import benepar
import importlib


nltk.download('punkt')
benepar.download('benepar_en2')


class EnSpecLexerError(Exception):
    def __init__(self, lexer, ex=None):
        super().__init__("Lexer error")
        self._lexer = lexer

    @property
    def value(self):
        return self._lexer.value

    @property
    def type(self):
        return self._lexer.type

    def detail(self):
        pass


class EnSpecParserError(Exception):
    def __init__(self, parser):
        super().__init__("Parser error")
        self._parser = parser
        if parser is None:
            self._pos = None
            self._lineno = None
            self._type = None
            self._value = None
            self._lexdata = None
            self._lexpos = None
            self._lexmatch = None
        else:
            self._parser = parser
            self._pos = parser.lexpos
            self._lineno = parser.lineno
            self._type = parser.type
            self._value = parser.value
            self._lexdata = parser.lexer.lexdata
            self._lexpos = parser.lexer.lexpos
            self._lexmatch = parser.lexer.lexmatch
        # print('Syntax error: %d: %d: %r' % (parser.lineno, parser.lexpos, parser.value))

    @property
    def pos(self):
        return self._pos

    @property
    def lineno(self):
        return self._lineno

    @property
    def type(self):
        return self._type

    @property
    def value(self):
        return self._value

    @property
    def lexdata(self):
        return self._lexdata

    @property
    def lexpos(self):
        return self._lexpos

    @property
    def lexmatch(self):
        return self._lexmatch

    def detail(self):
        print("pos:{}, value:'{}':{}, lexdata:{}".format(self.pos, self.value, self.type, self.lexdata))
        if self._parser is None or self._parser.lexer is None:
            return
        tag = "detail:"
        preerr = self.lexdata[:self.pos]
        i = len(preerr)-1
        for i in sorted(range(len(preerr)), reverse=True):
            if preerr[i] == "\n":
                break
        if preerr[i] == "\n":
            i = i+1
        posterr = ""
        for j, c in enumerate(self.lexdata[i:]):
            if c == "\n":
                break
            else:
                posterr = "{}{}".format(posterr, c)
        posterr = "{}".format(posterr)
        e = ""
        for c in preerr[i:]:
            if c != "\t":
                c = " "
            e = "{}{}".format(e, c)
        for _ in range(len(self.value)):
            e = "{}{}".format(e, "^")
        e = "{} <-- unexpected token:'{}':{}".format(e, self.value, self.type)
        e = "{}\n{}{}\n{}".format(tag, preerr[:i], posterr, e)
        print(e)
        return e


class EnSpecLexer:

    # Word analysis
    reserved = {
        # identifiers
        ".": "PERIOD"
    }
    tokens = [
            'PERIOD',
            'LITERAL',
            'OBJECT',
              ] + list(reserved.values())
    token_list = (
        # Reserved words
    )
    token = tokens

    t_ignore_COMMENT = r"/\*\[\s\S]*\*/|//.*"
    t_ignore = " \t"

    t_PERIOD = r"\."
    t_LITERAL = r"\"(\"\"|[^\"])*\""

    def t_OBJECT(self, t):
        r"[^\.]+"
        # print("picked as object:", t)
        if t.value in self.reserved.keys():
            t.type = self.reserved[t.value]
            return t
        m = re.match(self.t_LITERAL, t.value)
        if m is not None:
            t.type = "LITERAL"
            return t
        return t

    def __init__(self):
        self.lexer = lex.lex(module=self)

    def t_error(self, t):
        # _print("Illegal character {}".format(t.value[0]))
        t.lexer.skip(1)
        # err = SentenceSyntacticError(t)
        # raise err

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)


class EnSpecParser:

    def what_phase(self, phase):
        if type(phase) is tuple:
            return phase[0]
        else:
            return None

    def concat_phrases(self, *phrases):
        v = []
        for phrase in phrases:
            if type(phrase) is list or type(phrase) is tuple:
                for p in phrase:
                    v.append(p)
            else:
                v.append(phrase)
        return tuple(v)

    def concat_verbs(self, p):
        v = self.concat_phrases(p)
        return v

    # Parsing rules
    tokens = EnSpecLexer.tokens

    def p_interpretable(self, p):
        """
        min_required : sentence
        min_required : min_required sentence
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_period(self, p):
        """
        period : PERIOD
        """
        p[0] = p[1]

    def p_sentence(self, p):
        """
        sentence : open_sentence period
        """
        p[0] = tuple(p[1])

    def p_open_sentence(self, p):
        """
        open_sentence : object
        open_sentence : literal
        open_sentence : open_sentence object
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_object(self, p):
        """
        object : OBJECT
        """
        p[0] = p[1]

    def p_period(self, p):
        """
        period : PERIOD
        """
        p[0] = p[1]

    def p_literal(self, p):
        """
        literal : LITERAL
        """
        p[0] = p[1]

    # if error occurred
    def p_error(self, p):
        # print('Syntax error: %d: %d: %r' % (p.lineno, p.lexpos, p.value))
        err = EnSpecParserError(p)
        raise err

    def __init__(self, owner):
        self._owner = owner
        self._lexer = EnSpecLexer()
        self.lexer = self._lexer.lexer
        self.parser = yacc.yacc(module=self)

    @property
    def owner(self):
        return self._owner

    def check_syntax(self, text):
        self._lexer.build()
        self._lexer.test(text)

    def parse_script(self, text, pretest=True):
        if pretest:
            self._lexer.test(text)
        result = self.parser.parse(text, lexer=self.lexer)
        return result


class SyntaxAnalysisError(Exception):

    def __init__(self, msg):
        super().__init__(msg)


class EnglishSyntaxAnalyzer:

    class Tokens(enum.Enum):

        S = "S"
        NP = "NP"
        VP = "VP"
        PRP = "PRP"
        VBD = "VBD"
        VBZ = "VBZ"
        NN = "NN"
        CC = "CC"
        IN = "IN"
        ADJP = "ADJP"
        ADVP = "ADVP"
        CONJP = "CONJP"
        RB = "RB"
        NNP = "NNP"
        SBAR = "SBAR"
        COMMA = ","

    def __init__(self):
        self._parser = benepar.Parser("benepar_en2")
        self._target = None
        self._dispatcher = {
            self.Tokens.S: lambda t: self.analyze_statement(t),
            self.Tokens.NP: lambda t: self.analyze_np(t),
            self.Tokens.VP: lambda t: self.analyze_vp(t),
            # self.Tokens.PRP: lambda t: self.analyze_prp(t),
            # self.Tokens.VBD: lambda t: self.analyze_vbd(t),
            # self.Tokens.VBZ: lambda t: self.analyze_vbz(t),
            # self.Tokens.NN: lambda t: self.analyze_nn(t),
            # self.Tokens.CC: lambda t: self.analyze_cc(t),
            # self.Tokens.ADJP: lambda t: self.analyze_adjp(t),
            # self.Tokens.ADVP: lambda t: self.analyze_advp(t),
            # self.Tokens.RB: lambda t: self.analyze_rb(t),
            # self.Tokens.NNP: lambda t: self.analyze_nnp(t)
        }

    def reload(self):
        print("setting up target 'interpret.interpret'")
        importlib.reload(interpret)
        self._target = interpret.interpret

    def analyze(self, text):
        if self._target is None:
            print("Analysis receiver not loaded.")
            return False
        try:
            tree = self._parser.parse(text)
            # print("Tree is:", tree)
            # spec = self.analyze_statement(tree)
            self._target(tree)
            return True
        except EnSpecLexerError as ex:
            print(ex)
        except EnSpecParserError as ex:
            print(ex)
            ex.detail()
        except Exception as ex:
            print(ex)

    def analyze_statement(self, tree: nltk.tree.Tree):
        if not self.is_tree(tree):
            return tree
        if not self.has_child(tree):
            return tree.label()
        children = []
        for c in tree:
            c = self.analyze_statement(c)
            children.append(c)
        return tuple(["'{}".format(tree.label()), tuple(children)])

    def is_tree(self, tree):
        return isinstance(tree, nltk.tree.Tree)

    def has_child(self, tree):
        has = False
        for _ in tree:
            has = True
        return has

    def analyze_np(self, tree):
        pass

    def analyze_vp(self, tree):
        pass


def main():
    analyzer = EnglishSyntaxAnalyzer()
    args = sys.argv
    parser = EnSpecParser(None)
    while True:
        try:
            text = input("$input ")
            pat = r"^\s*(\-f\s+(?P<file>.+)|(?P<quit>(quit|exit))|(load|reload)\s+(?P<target>[a-zA-Z0-9_]+)|)\s*$"
            m = re.match(pat, text)
            if m is not None:
                g = m.groupdict()
                if g["file"] is not None:
                    with open(g["file"], "r") as f:
                        for s in parser.parse_script(f.read()):
                            analyzer.analyze(s)
                elif g["quit"] is not None:
                    break
                elif g["target"] is not None:
                    analyzer.reload(g["target"])
                else:
                    continue
            else:
                sent = analyzer.analyze(text)
                print("Sent:", sent)
        except EnSpecLexerError as ex:
            print(ex)
        except EnSpecParserError as ex:
            print(ex)
            ex.detail()
        except Exception as ex:
            print(ex)
            print("quit")


if __name__ == "__main__":
    main()
