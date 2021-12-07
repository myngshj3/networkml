# -*- coding: utf-8 -*-

import ply.lex as lex
import ply.yacc as yacc
import re
import sys
import traceback

# import our modules
from networkml.error import NetworkError


class SentenceSyntacticError(NetworkError):
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


class SentenceParserError(NetworkError):
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

        # for c in self.lexdata[:self.pos]:
        #     if c != "\t":
        #         c = " "
        #     e = "{}{}".format(e, c)
        # for _ in range(len(self.value)):
        #     e = "{}{}".format(e, "^")
        # print(self.lexdata, "\n")
        # print(e, "<-- unexpected token:", "'{}':{}".format(self.value, self.type))


class SentenceSyntacticAnalyzer:

    # Word analysis
    reserved = {
        # identifiers
        'a': 'A',
        'the': 'THE',
        'that': 'THAT',
        "it's": 'ITS',
        "this": 'THIS',
        "his": 'HIS',
        "her": 'HER',
        "their": 'THEIR',
        # auxiliary verb
        "will": "WILL",
        "would": "WOULD",
        "can": "CAN",
        "could": "COULD",
        "may": "MAY",
        "might": "MIGHT",
        "should": "SHOULD",
        "shall": "SHALL",
        # auxiliary negative verb
        "wouldn't": "WOULDNT",
        "can't": "CANT",
        "couldn't": "COULDNT",
        "shouldn't": "SHOULDNT",
        "don't": "DONT",
        "doesn't": "DOESNT",
        "didn't": "DIDNT",
        "haven't": "HAVENT",
        "hasn't": "HASNT",
        "hadn't": "HADNT",
        "never": "NEVER",
        # question
        "who": "WHO",
        "what": "WHAT",
        "why": "WHY",
        "which": "WHICH",
        "whose": "WHOSE",
        "where": "WHERE",
        "how": "HOW",
        # be verb
        'be': 'BE',
        'is': 'IS',
        "are": "ARE",
        "was": "WAS",
        "were": "WERE",
        # negative be verb
        "isn't": "ISNT",
        "aren't": "ARENT",
        "wasn't": "WASNT",
        "weren't": "WERENT",
        # primitive verb
        "do": "DO",
        "does": "DOES",
        "did": "DID",
        "have": "HAVE",
        "has": "HAS",
        "had": "HAD",
        "like": "LIKE",
        "likes": "LIKES",
        "liked": "LIKED",
        "named": "NAMED",
        "call": "CALL",
        "called": "CALLED",
        # ordinary negation
        "not": "NOT",
        # representative adjactive
        "so": "SO",
        "very": "VERY",
        "good": "GOOD",
        "bad": "BAD",
        "nice": "NICE",
        "well": "WELL",
        "such": "SUCH",
        # connective junction
        "and": "AND",
        "or": "OR",
        # fundamental naun
        "name": "NAME",
        # preposition
        "for": "FOR",
        "from": "FROM",
        "to": "TO",
        "of": "OF",
        "in": "IN",
        "as": "AS",
        "at": "AT",
        "just": "JUST",
        "now": "NOW",
        "with": "WITH",
        "without": "WITHOUT",
        "toward": "TOWARD",
        "onto": "ONTO",
        "into": "INTO",
        "on": "ON",
        "upward": "UPWARD",
        "downward": "DOWNWARD"
    }
    tokens = [
            'PERIOD',
            'COMMA',
            'LPAR',
            'RPAR',
            'LITERAL',
            'OBJECT',
              ] + list(reserved.values())
    token_list = (
        # Reserved words
    )
    token = tokens

    t_ignore_COMMENT = r"/\*\[\s\S]*\*/|//.*"
    t_ignore = " \t"

    t_PERIOD = r"\s*\."
    t_COMMA = r"\s*,\s*"
    t_LPAR = r"\("
    t_RPAR = r"\)"

    t_LITERAL = r"\"(\"\"|[^\"])*\""

    def t_OBJECT(self, t):
        r"[a-zA-Z]+(\-[a-zA-Z0-9']+)*"
        # print("picked as object:", t)
        if t.value in self.reserved.keys():
            t.type = self.reserved[t.value]
            # print("replace type to '{}'".format(t.type))
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


class SentenceParser:

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
    tokens = SentenceSyntacticAnalyzer.tokens

    def p_interpretable(self, p):
        """
        interpretable : proper_statement  period
        """
        p[0] = ("proper-statement", p[1])

    def p_period(self, p):
        """
        period : PERIOD
        """
        p[0] = p[1]

    def p_proper_statement(self, p):
        """
        proper_statement : subject subjectless_statement
        """
        p[0] = (p[1], p[2])

    def p_subject(self, p):
        """
        subject : object
        subject : objects
        """
        p[0] = ("subject", p[1])

    def p_subjectless_statement(self, p):
        """
        subjectless_statement : be_statement
        subjectless_statement : act_statement
        """
        p[0] = p[1]

    def p_be_statement(self, p):
        """
        be_statement :                    be be_targets
        be_statement : auxiliary_verb     be be_targets
        be_statement : auxiliary_verb not be be_targets
        """
        be = self.concat_phrases("be", p[1:len(p)-1])
        be_targets = p[len(p)-1]
        p[0] = (be, be_targets)

    # def p_auxiliary_be_statement(self, p):
    #     """
    #     auxiliary_be_statement : auxiliary_verb     be be_targets
    #     auxiliary_be_statement : auxiliary_verb not be be_targets
    #     """
    #     be = self.concat_phrases("be", p[1:len(p)-1])
    #     be_targets = p[len(p)-1]
    #     p[0] = (be, be_targets)

    def p_be_targets(self, p):
        """
        be_targets : be_target
        be_targets : close_be_targets
        """
        p[0] = ("be-targets", p[1])

    def p_close_be_targets(self, p):
        """
        close_be_targets : open_be_targets and be_target
        close_be_targets : open_be_targets or  be_target
        """
        p[1].append(p[3])
        p[0] = tuple(p[1])

    def p_open_be_targets(self, p):
        """
        open_be_targets : be_target
        open_be_targets : open_be_targets comma be_target
        """
        if len(p) == 2:
            be_targets = [p[1]]
        else:
            p[1].append(p[3])
            be_targets = p[1]
        p[0] = be_targets

    def p_be_target(self, p):
        """
        be_target : object
        be_target : not object
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = (p[1], p[2])

    def p_act_targets(self, p):
        """
        act_targets : act_target
        act_targets : close_act_targets
        """
        p[0] = ("act-targets", p[1])

    def p_close_act_targets(self, p):
        """
        close_act_targets : open_act_targets and act_target
        close_act_targets : open_act_targets or  act_target
        """
        p[1].append(p[3])
        p[0] = p[1]

    def p_open_act_targets(self, p):
        """
        open_act_targets : act_target
        open_act_targets : open_act_targets comma act_target
        """
        if len(p) == 2:
            act_targets = [p[1]]
        else:
            p[1].append(p[3])
            act_targets = p[1]
        p[0] = act_targets

    def p_act_target(self, p):
        """
        act_target : object
        """
        p[0] = p[1]

    def p_act_statement(self, p):
        """
        act_statement : act act_predicates
        act_statement : act act_targets
        act_statement : act act_targets act_predicates
        """
        if len(p) == 3:
            if self.what_phase(p[2]) == "act-predicates":
                act_predicates = p[2]
                act_targets = ()
            else:
                act_predicates = ()
                act_targets = p[2]
        else:
            act_targets = p[2]
            act_predicates = p[3]
        act = ("act", p[1], act_predicates)
        p[0] = (act, act_targets)

    def p_act(self, p):
        """
        act : primitive_action
        act : does not  primitive_action
        act : doesnt    primitive_action
        act : do not    primitive_action
        act : dont      primitive_action
        act : did not   primitive_action
        act : didnt     primitive_action
        act : auxiliary_verb  primitive_action
        act : auxiliary_negative_verb primitive_action
        """
        v = self.concat_phrases(p[1:])
        p[0] = v

    def p_primitive_action(self, p):
        """
        primitive_action : object_symbol
        primitive_action : like
        primitive_action : likes
        primitive_action : liked
        primitive_action : call
        primitive_action : have
        primitive_action : has
        primitive_action : had
        primitive_action : do
        primitive_action : does
        primitive_action : did
        """
        p[0] = (p[1])

    def p_act_predicates(self, p):
        """
        act_predicates : act_predicate_list
        """
        p[0] = ("act-predicates", tuple(p[1]))

    def p_act_predicate_list(self, p):
        """
        act_predicate_list : act_predicate
        act_predicate_list : act_predicate_list act_predicate_list
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_act_predicate(self, p):
        """
        act_predicate : preposition act_resources
        """
        p[0] = (p[1], p[2])

    def p_act_resources(self, p):
        """
        act_resources : objects
        act_resources : act_resources and act_resources
        act_resources : act_resources or  act_resources
        """
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = (p[1], p[2])
        else:
            p[0] = (p[2], (p[1], p[3]))

    def p_identifier(self, p):
        """
        identifier : ambiguous_identifier
        identifier : concrete_identifier
        """
        p[0] = ("identifier", p[1])

    def p_ambiguous_identifier(self, p):
        """
        ambiguous_identifier : a
        """
        p[0] = p[1]

    def p_concrete_identifier(self, p):
        """
        concrete_identifier : the
        concrete_identifier : that
        concrete_identifier : this
        concrete_identifier : its
        concrete_identifier : his
        concrete_identifier : her
        concrete_identifier : their
        """
        p[0] = p[1]

    def p_auxiliary_verb(self, p):
        """
        auxiliary_verb : will
        auxiliary_verb : can
        auxiliary_verb : would
        auxiliary_verb : could
        auxiliary_verb : may
        auxiliary_verb : might
        auxiliary_verb : should
        auxiliary_verb : shall
        auxiliary_verb : have to
        auxiliary_verb : has to
        auxiliary_verb : would like to
        """
        p[0] = self.concat_phrases(p[1:])

    def p_auxiliary_negative_verb(self, p):
        """
        auxiliary_negative_verb : will not
        auxiliary_negative_verb : can not
        auxiliary_negative_verb : cant
        auxiliary_negative_verb : would not
        auxiliary_negative_verb : wouldnt
        auxiliary_negative_verb : could not
        auxiliary_negative_verb : couldnt
        auxiliary_negative_verb : may not
        auxiliary_negative_verb : might not
        auxiliary_negative_verb : should not
        auxiliary_negative_verb : shouldnt
        auxiliary_negative_verb : have not to
        auxiliary_negative_verb : havent   to
        auxiliary_negative_verb : hasnt    to
        auxiliary_negative_verb : have never
        auxiliary_negative_verb : has  never
        auxiliary_negative_verb : would not like to
        auxiliary_negative_verb : wouldnt   like to
        """
        p[0] = self.concat_phrases(p[1:])

    def p_will(self, p):
        """
        will : WILL
        """
        p[0] = (p[1])

    def p_can(self, p):
        """
        can : CAN
        """
        p[0] = (p[1])

    def p_could(self, p):
        """
        could : COULD
        """
        p[0] = (p[1])

    def p_may(self, p):
        """
        may : MAY
        """
        p[0] = (p[1])

    def p_might(self, p):
        """
        might : MIGHT
        """
        p[0] = (p[1])

    def p_should(self, p):
        """
        should : SHOULD
        """
        p[0] = (p[1])

    def p_shouldnt(self, p):
        """
        shouldnt : SHOULDNT
        """
        p[0] = (p[1])

    def p_shell(self, p):
        """
        shall : SHALL
        """
        p[0] = (p[1])

    def p_be(self, p):
        """
        be : BE
        be : IS
        be : ARE
        be : WAS
        be : WERE
        """
        p[0] = p[1]

    def p_a(self, p):
        """
        a : A
        """
        p[0] = p[1]

    def p_the(self, p):
        """
        the : THE
        """
        p[0] = p[1]

    def p_that(self, p):
        """
        that : THAT
        """
        p[0] = p[1]

    def p_such(self, p):
        """
        such : SUCH
        """
        p[0] = p[1]

    def p_its(self, p):
        """
        its : ITS
        """
        p[0] = p[1]

    def p_this(self, p):
        """
        this : THIS
        """
        p[0] = p[1]

    def p_his(self, p):
        """
        his : HIS
        """
        p[0] = p[1]

    def p_her(self, p):
        """
        her : HER
        """
        p[0] = p[1]

    def p_their(self, p):
        """
        their : THEIR
        """
        p[0] = p[1]

    def p_objects(self, p):
        """
        objects : close_object_list
        """
        p[0] = ("objects", p[1])

    def p_close_object_list(self, p):
        """
        close_object_list : open_object_list and object
        close_object_list : open_object_list or object
        """
        if len(p) == 2:
            p[0] = tuple(p[1])
        else:
            p[1].append(p[3])
            p[0] = (p[2], tuple(p[1]))

    def p_open_object_list(self, p):
        """
        open_object_list : object
        open_object_list : open_object_list comma object
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].extend(p[3])

    def p_object_symbol(self, p):
        """
        object_symbol : OBJECT
        """
        p[0] = p[1]

    def p_object(self, p):
        """
        object : object_symbol
        object : object_symbol postpositional_predicate_sequence
        object : identifier object_symbol
        object : identifier object_symbol postpositional_predicate_sequence
        """
        if len(p) == 2:
            p[0] = (p[1], ())
        elif len(p) == 3:
            if self.what_phase(p[1]) == "identifier":
                p[0] = (p[2], (), p[1])
            else:
                p[0] = (p[1], p[2])
        else:
            p[0] = (p[1], p[2])

    def p_postpositional_predicate(self, p):
        """
        postpositional_predicate : such that mentions
        postpositional_predicate : such as objects
        postpositional_predicate : such like object
        postpositional_predicate : named  literal
        postpositional_predicate : called literal
        postpositional_predicate : in which mentions
        postpositional_predicate : which subjectless_statement
        postpositional_predicate : that  subjectless_statement
        postpositional_predicate : who   subjectless_statement
        postpositional_predicate : where mentions
        postpositional_predicate : whose name subjectless_statement
        postpositional_predicate : whose object_symbol subjectless_statement
        postpositional_predicate : preposition objects
        """
        v = self.concat_phrases(p[1:])
        p[0] = ("post-predicate", tuple(v), p[len(p)-1])

    def p_postpositional_predicate_sequence(self, p):
        """
        postpositional_predicate_sequence : postpositional_predicate
        postpositional_predicate_sequence : postpositional_predicate_sequence and postpositional_predicate_sequence
        postpositional_predicate_sequence : postpositional_predicate_sequence or  postpositional_predicate_sequence
        """
        if len(p) == 2:
            p[0] = tuple(p[1])
        else:
            p[0] = (p[2], (p[1], p[3]))
        p[0] = (p[1])

    def p_predicates(self, p):
        """
        predicates : such that mentions
        predicates : such as objects
        """
        p[0] = ((p[1], p[2]), p[3])

    def p_mentions(self, p):
        """
        mentions : proper_statement
        mentions : mentions and mentions
        mentions : mentions or mentions
        mentions : not mentions
        mentions : lpar mentions rpar
        """
        if len(p) == 2:
            p[0] = (p[1])
        elif len(p) == 3:
            p[0] = (p[1], p[2])
        elif len(p) == 4:
            if p[1] == "(":
                p[0] = p[1]
            else:
                p[0] = (p[2], (p[1], p[3]))

    def p_lpar(self, p):
        """
        lpar : LPAR
        """
        p[0] = p[1]

    def p_rpar(self, p):
        """
        rpar : RPAR
        """
        p[0] = p[1]

    def p_and(self, p):
        """
        and : AND
        """
        p[0] = p[1]

    def p_or(self, p):
        """
        or : OR
        """
        p[0] = p[1]

    def p_not(self, p):
        """
        not : NOT
        """
        p[0] = p[1]

    def p_does(self, p):
        """
        does :  DOES
        """
        p[0] = p[1]

    def p_doesnt(self, p):
        """
        doesnt :  DOESNT
        """
        p[0] = p[1]

    def p_do(self, p):
        """
        do :  DO
        """
        p[0] = p[1]

    def p_dont(self, p):
        """
        dont :  DONT
        """
        p[0] = p[1]

    def p_would(self, p):
        """
        would :  WOULD
        """
        p[0] = p[1]

    def p_wouldnt(self, p):
        """
        wouldnt :  WOULDNT
        """
        p[0] = p[1]

    def p_cant(self, p):
        """
        cant :  CANT
        """
        p[0] = p[1]

    def p_couldnt(self, p):
        """
        couldnt :  COULDNT
        """
        p[0] = p[1]

    def p_never(self, p):
        """
        never :  NEVER
        """
        p[0] = p[1]

    def p_have(self, p):
        """
        have : HAVE
        """
        p[0] = p[1]

    def p_havent(self, p):
        """
        havent : HAVENT
        """
        p[0] = p[1]

    def p_has(self, p):
        """
        has : HAS
        """
        p[0] = p[1]

    def p_hasnt(self, p):
        """
        hasnt : HASNT
        """
        p[0] = p[1]

    def p_had(self, p):
        """
        had : HAD
        """
        p[0] = p[1]

    def p_hadnt(self, p):
        """
        hadnt : HADNT
        """
        p[0] = p[1]

    def p_did(self, p):
        """
        did : DID
        """
        p[0] = p[1]

    def p_didnt(self, p):
        """
        didnt : DIDNT
        """
        p[0] = p[1]

    def p_like(self, p):
        """
        like : LIKE
        """
        p[0] = p[1]

    def p_likes(self, p):
        """
        likes : LIKES
        """
        p[0] = p[1]

    def p_liked(self, p):
        """
        liked : LIKED
        """
        p[0] = p[1]

    def p_call(self, p):
        """
        call : CALL
        """
        p[0] = p[1]

    def p_called(self, p):
        """
        called : CALLED
        """
        p[0] = p[1]

    def p_name(self, p):
        """
        name : NAME
        """
        p[0] = p[1]

    def p_named(self, p):
        """
        named : NAMED
        """
        p[0] = p[1]

    def p_why(self, p):
        """
        why : WHY
        """
        p[0] = (p[1])

    def p_how(self, p):
        """
        how : HOW
        """
        p[0] = (p[1])

    def p_who(self, p):
        """
        who : WHO
        """
        p[0] = (p[1])

    def p_what(self, p):
        """
        what : WHAT
        """
        p[0] = (p[1])

    def p_which(self, p):
        """
        which : WHICH
        """
        p[0] = (p[1])

    def p_where(self, p):
        """
        where : WHERE
        """
        p[0] = (p[1])

    def p_whose(self, p):
        """
        whose : WHOSE
        """
        p[0] = (p[1])

    def p_comma(self, p):
        """
        comma : COMMA
        """
        p[0] = p[1]

    def p_preposition(self, p):
        """
        preposition : for
        preposition : from
        preposition : to
        preposition : of
        preposition : in
        preposition : as
        preposition : at
        preposition : toward
        preposition : onto
        preposition : into
        preposition : on
        preposition : with
        preposition : without
        preposition : upward
        preposition : downward
        """
        p[0] = p[1]

    def p_for(self, p):
        """
        for : FOR
        """
        p[0] = p[1]

    def p_from(self, p):
        """
        from : FROM
        """
        p[0] = p[1]

    def p_to(self, p):
        """
        to : TO
        """
        p[0] = p[1]

    def p_of(self, p):
        """
        of : OF
        """
        p[0] = p[1]

    def p_in(self, p):
        """
        in : IN
        """
        p[0] = p[1]

    def p_as(self, p):
        """
        as : AS
        """
        p[0] = p[1]

    def p_at(self, p):
        """
        at : AT
        """
        p[0] = p[1]

    def p_toward(self, p):
        """
        toward : TOWARD
        """
        p[0] = p[1]

    def p_onto(self, p):
        """
        onto : ONTO
        """
        p[0] = p[1]

    def p_into(self, p):
        """
        into : INTO
        """
        p[0] = p[1]

    def p_on(self, p):
        """
        on : ON
        """
        p[0] = p[1]

    def p_with(self, p):
        """
        with : WITH
        """
        p[0] = p[1]

    def p_without(self, p):
        """
        without : WITHOUT
        """
        p[0] = p[1]

    def p_upward(self, p):
        """
        upward : UPWARD
        """
        p[0] = p[1]

    def p_downward(self, p):
        """
        downward : DOWNWARD
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
        err = SentenceParserError(p)
        raise err

    def __init__(self, owner):
        self._owner = owner
        self._lexer = SentenceSyntacticAnalyzer()
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
        if isinstance(rtn, SentenceSyntacticError):
            print("stop type:{}, value:{}", rtn.type, rtn.value)
            break
        if isinstance(rtn, SentenceParserError):
            rtn.detail()
            print("interpretable:", rtn)
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
    l = SentenceSyntacticAnalyzer()
    l.build()
    p = SentenceParser(l)
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
