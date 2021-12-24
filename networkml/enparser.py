# -*- coding:utf-8 -*-

# For parser information, see below,
# benepar PyPI
# pypi.org › project › benepar

from networkml.generic import debug, is_debug_mode
import nltk
import benepar


_parser = None
_setup_done = False


def update():
    nltk.download('punkt')
    benepar.download('benepar_en2')


def setup():
    global _setup_done
    if not _setup_done:
        update()
        _setup_done = True


def parse(string):
    global _parser
    setup()
    if _parser is None:
        _parser = benepar.Parser("benepar_en2")
    tree = _parser.parse(string)
    return tree


def try_parse(string):
    try:
        tree = parse(string)
        return tree
    except Exception as ex:
        debug(ex)
        return None
