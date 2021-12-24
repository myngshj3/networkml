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


class Benepar:

    def __init__(self, config=None):
        self._parser = None
        self.setup()

    def setup(self):
        if self._parser is None:
            self._parser = benepar.Parser("benepar_en2")

    def __call__(self, *args, **kwargs):
        return self.parse(args[0])

    def parse(self, string):
        self.setup()
        tree = self._parser.parse(string)
        return tree

    def try_parse(self, string):
        try:
            tree = self._parser.parse(string)
            return tree
        except Exception as ex:
            debug(ex)
            return None
