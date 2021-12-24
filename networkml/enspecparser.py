# -*- coding: utf-8 -*-

import ply.lex as lex
import ply.yacc as yacc
import re
import sys
import traceback

# import our modules
from networkml.error import NetworkError


class EnSpecLexerError(NetworkError):
    def __init__(self, lexer, ex=None):
        super().__init__("Lexer error", ex)
        self._lexer = lexer

    @property
    def value(self):
        return self._lexer.value

    @property
    def type(self):
        return self._lexer.type

    def detail(self):
        pass


class EnSpecParserError(NetworkError):
    def __init__(self, parser, ex=None):
        super().__init__("Parser error", ex)
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

    t_LITERAL = r"\"(\"\"|[^\"])*\""

    def t_OBJECT(self, t):
        r"[^\"]+"
        # print("picked as object:", t)
        if t.value in self.reserved.keys():
            t.type = self.reserved[t.value]
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
        interpretable : proper_sentence
        """
        p[0] = p[1]

    def p_period(self, p):
        """
        period : PERIOD
        """
        p[0] = p[1]

    def p_proper_sentence(self, p):
        """
        proper_sentence : subject verb period
        """
        p[0] = (p[1], p[2])

    def p_subject(self, p):
        """
        subject : np
        subject : np_group
        """
        p[0] = p[1]

    def p_np(self, p):
        """
        np : NP
        """
        p[0] = p[1]

    def p_np_group(self, p):
        """
        np_group : closed_np_list
        """
        p[0] = p[1]

    def p_closed_np_list(self, p):
        """
        closed_np_list : opened_np_list cc np
        """
        p[1].append(p[3])
        p[0] = (p[2], tuple(p[2]))

    def p_opened_np_list(self, p):
        """
        opened_np_list : np
        opened_np_list : opened_np_list comma np
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[1].append(p[3])
            p[0] = p[1]

    def p_cc(self, p):
        """
        cc : CC
        """
        p[0] = p[1]

    def p_verb(self, p):
        """
        verb : vp
        """
        p[0] = p[1]

    def p_vp(self, p):
        """
        vp : VP vp_detail
        """
        p[0] = [_ for _ in p[1:]]
        p[0] = tuple(p[0])

    def p_vp_detail(self, p):
        """
        vp_detail : vp
        vp : vp_symbol md  vp_detail
        vp : vp_symbol vbp rb vp_detail
        vp : vp_symbol md  rb vp_detail
        vp : vp_symbol vbp advp vp_detail
        vp : vp_symbol vbp advp vp_detail
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


def try_parse(text, parser, pretest=True):
    try:
        return parser.parse_script(text, pretest=pretest)
    except Exception as ex:
        return ex


def stimulous_parse(text, parser, pretest=True):
    done = False
    while not done:
        rtn = try_parse(text, parser, pretest=pretest)
        if isinstance(rtn, EnSpecLexerError):
            print("stop type:{}, value:{}", rtn.type, rtn.value)
            break
        if isinstance(rtn, EnSpecParserError):
            rtn.detail()
            done = True
        elif isinstance(rtn, Exception):
            print("exception:", rtn)
            done = True
        else:
            print("interpretable:", rtn)
            break


def main():
    pretest = False
    for a in sys.argv[1:]:
        if a == "test":
            pretest = True
    p = EnSpecParser(None)
    null_pat = r"^\s*$"
    while True:
        txt = input("script-> ")
        m = re.match(null_pat, txt)
        if m is not None:
            continue
        if txt == "exit" or txt == "quit":
            break
        stimulous_parse(txt, p, pretest=pretest)


if __name__ == "__main__":
    main()
